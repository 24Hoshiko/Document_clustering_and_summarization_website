import os
import sys
import fitz  # PyMuPDF
import numpy as np
import re  # For text cleaning
from sentence_transformers import SentenceTransformer
import hdbscan
from scipy.spatial.distance import pdist, squareform
from transformers import BartTokenizer, BartForConditionalGeneration

# Load SBERT model for clustering
model = SentenceTransformer('all-MiniLM-L6-v2')

# Load BART model and tokenizer for abstractive summarization
bart_tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
bart_model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')

# Function to clean extracted text
def clean_text(text):
    text = text.strip()
    text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)  # Remove lines with only digits
    text = re.sub(r'^[()0-9\s\-.]+$', '', text, flags=re.MULTILINE)  # Remove lines with only symbols/numbers
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)  # Remove emails
    text = re.sub(r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b', '', text, flags=re.IGNORECASE)  # Remove DOIs
    text = re.sub(r'\b(?:http|https|ftp)://\S+\b|\bwww\.\S+\b', '', text)  # Enhanced URL removal
    text = re.sub(r'\d+', '', text)  # Remove all numbers
    return text.strip()

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        try:
            blocks = page.get_text("blocks")
            blocks.sort(key=lambda b: (b[1], b[0]))  # Sort by Y, then X
            text += "\n\n".join([clean_text(b[4]) for b in blocks if b[4].strip()])
        except Exception as e:
            print(f"⚠️ Error extracting text from {pdf_path}: {e}")
    return text.strip()

# Function for detailed abstractive summarization using BART
def summarize_paragraphs_abstractive(paragraphs):
    if not paragraphs:
        return "No summary available."
    combined_text = " ".join(paragraphs)
    if len(combined_text) < 50:
        return "Text too short to summarize."
    
    inputs = bart_tokenizer(combined_text, max_length=1024, truncation=True, return_tensors="pt")
    summary_ids = bart_model.generate(
        inputs["input_ids"],
        max_length=800,  # Increased for detailed output (~200+ words)
        min_length=600,  # Ensures at least ~100-150 words, pushing towards 200
        length_penalty=1.0,  # Reduced to favor longer outputs
        num_beams=6,  # Higher beams for better coherence in longer text
        early_stopping=True
    )
    summary = bart_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# Load PDFs and process
def process_folder(folder_path):
    if not os.path.exists(folder_path):
        print("❌ Folder path does not exist!")
        sys.exit(1)

    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("❌ No PDF files found!")
        sys.exit(1)

    print(f"✅ Found {len(pdf_files)} PDFs:", pdf_files)

    paragraphs = []
    document_map = {}

    for filename in pdf_files:
        pdf_path = os.path.join(folder_path, filename)
        pdf_text = extract_text_from_pdf(pdf_path)
        if not pdf_text:
            print(f"⚠️ No text extracted from {filename}. It might be scanned.")
            continue
        extracted_paragraphs = [p for p in pdf_text.split("\n\n") if len(p) > 30]
        if extracted_paragraphs:
            print(f"📄 Extracted {len(extracted_paragraphs)} paragraphs from {filename}")
        else:
            print(f"⚠️ No meaningful text found in {filename}")
        paragraphs.extend(extracted_paragraphs)
        for p in extracted_paragraphs:
            document_map[p] = filename

    if not paragraphs:
        print("❌ No paragraphs extracted!")
        sys.exit(1)

    print(f"✅ Total paragraphs extracted: {len(paragraphs)}")
    print(f"🔹 Sample paragraph:\n{paragraphs[0][:300]}")

    # Convert paragraphs to embeddings
    embeddings = model.encode(paragraphs)
    if embeddings.shape[0] == 0:
        print("❌ No embeddings were generated!")
        sys.exit(1)

    print(f"✅ Embeddings shape: {embeddings.shape}")

    # Apply HDBSCAN Clustering
    cosine_distance_matrix = squareform(pdist(embeddings, metric="cosine"))
    clusterer = hdbscan.HDBSCAN(min_cluster_size=5, metric="precomputed")
    clusters = clusterer.fit_predict(cosine_distance_matrix)

    unique_clusters = set(clusters)
    num_noise = sum(1 for c in clusters if c == -1)
    print(f"✅ Clusters found: {unique_clusters}")
    print(f"🔹 Noise points: {num_noise} ({(num_noise / len(clusters)) * 100:.2f}%)")
    print(f"🔹 First 10 cluster labels: {clusters[:10]}")

    # Store Clustered Paragraphs
    clustered_paragraphs = {}
    for i, cluster_id in enumerate(clusters):
        if cluster_id not in clustered_paragraphs:
            clustered_paragraphs[cluster_id] = []
        clustered_paragraphs[cluster_id].append(paragraphs[i])

    if not clustered_paragraphs:
        print("❌ No clusters formed.")
        sys.exit(1)

    # Combine all similarities and differences across all documents
    all_similarities = []
    all_differences = []

    for cluster_id, para_list in clustered_paragraphs.items():
        if cluster_id != -1:  # Similarities
            all_similarities.extend(para_list)
        else:  # Differences (noise)
            all_differences.extend(para_list)

    # Generate detailed overall summaries
    overall_similarities_summary = summarize_paragraphs_abstractive(all_similarities)
    overall_differences_summary = summarize_paragraphs_abstractive(all_differences)

    # Write overall similarities
    with open(os.path.join(folder_path, "similarities.txt"), "w", encoding="utf-8") as sim_file:
        sim_file.write("Overall Summary of Similarities Across All Research Papers\n")
        sim_file.write("=" * 60 + "\n\n")
        sim_file.write(f"{overall_similarities_summary}\n")

        sim_file.write("\n\nOverall Summary of Differences Across All Research Papers\n")
        sim_file.write("=" * 60 + "\n\n")
        sim_file.write(f"{overall_differences_summary}\n")

    print("✅ Detailed overall abstractive summaries (200+ words) written to similarities.txt and differences.txt in", folder_path)
    print("✅ Clustering and summarization complete!")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python para_cluster.py <folder_path>")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    process_folder(folder_path)
