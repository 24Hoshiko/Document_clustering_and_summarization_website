import os
import sys
import fitz  # PyMuPDF
import numpy as np
import re  # For text cleaning
from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
import hdbscan
from scipy.spatial.distance import pdist, squareform

# Load SBERT model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Function to clean extracted text
def clean_text(text):
    text = text.strip()
    text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[()0-9\s\-.]+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    text = re.sub(r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b', '', text, flags=re.IGNORECASE)
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

# Load PDFs
folder_path = r"D:\Document_clustering_and_summarization_website\clustered_docs\obstacle_crossref_pp_drone_cid"

if not os.path.exists(folder_path):
    print("❌ Folder path does not exist!")
    sys.exit()

pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
if not pdf_files:
    print("❌ No PDF files found!")
    sys.exit()

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
    sys.exit()

print(f"✅ Total paragraphs extracted: {len(paragraphs)}")
print(f"🔹 Sample paragraph:\n{paragraphs[0][:300]}")

# Convert paragraphs to embeddings
embeddings = model.encode(paragraphs)
if embeddings.shape[0] == 0:
    print("❌ No embeddings were generated!")
    sys.exit()

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
    clustered_paragraphs[cluster_id].append((paragraphs[i], document_map[paragraphs[i]]))

if not clustered_paragraphs:
    print("❌ No clusters formed.")
    sys.exit()

# Organize paragraphs by document for similarities and differences
# Organize paragraphs by document for similarities and differences
similarities_by_doc = {}
differences_by_doc = {}

for cluster_id, para_list in clustered_paragraphs.items():
    if cluster_id != -1:  # Exclude outliers
        for para, doc in para_list:
            if doc not in similarities_by_doc:
                similarities_by_doc[doc] = []
            similarities_by_doc[doc].append(para)  # Store paragraph without cluster ID
    else:  # Outliers go to differences
        for para, doc in para_list:
            if doc not in differences_by_doc:
                differences_by_doc[doc] = []
            differences_by_doc[doc].append(para)

# Write similarities to similarities.txt
with open("clustered_docs\obstacle_crossref_pp_drone_cid\similarities.txt", "w", encoding="utf-8") as sim_file:
    sim_file.write("Similarities Across Documents\n")
    sim_file.write("=" * 50 + "\n\n")
    
    for doc, para_list in similarities_by_doc.items():
        sim_file.write(f"Document: {doc}\n")
        sim_file.write("-" * 50 + "\n")
        sim_file.write("Similar Paragraphs:\n")
        for para in para_list:
            sim_file.write(f"{para}\n\n")
        sim_file.write("\n")

# Write differences to differences.txt
with open("clustered_docs\obstacle_crossref_pp_drone_cid\differences.txt", "w", encoding="utf-8") as diff_file:
    diff_file.write("Differences Across Documents\n")
    diff_file.write("=" * 50 + "\n\n")
    
    for doc, para_list in differences_by_doc.items():
        diff_file.write(f"Document: {doc}\n")
        diff_file.write("-" * 50 + "\n")
        diff_file.write("Outlier Paragraphs:\n")
        for para in para_list:
            diff_file.write(f"{para}\n\n")
        diff_file.write("\n")

print("✅ Results written to similarities.txt and differences.txt")
print("✅ Clustering complete!")