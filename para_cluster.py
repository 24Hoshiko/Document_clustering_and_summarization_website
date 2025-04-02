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
    
    # Remove isolated numbers (likely page numbers)
    text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
    
    # Remove empty lines or just special characters
    text = re.sub(r'^[()0-9\s\-.]+$', '', text, flags=re.MULTILINE)
    
    # Remove emails (common in research papers)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
    
    # Remove DOI references
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
            text += "\n\n".join([clean_text(b[4]) for b in blocks if b[4].strip()])  # Cleaned text
        except Exception as e:
            print(f"⚠️ Error extracting text from {pdf_path}: {e}")
    
    return text.strip()

# Load PDFs
folder_path = r"C:\Users\aditi\Downloads\Quantum AI"

if not os.path.exists(folder_path):
    print("❌ Folder path does not exist!")
    sys.exit()

pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
if not pdf_files:
    print("❌ No PDF files found!")
    sys.exit()

print(f"✅ Found {len(pdf_files)} PDFs:", pdf_files)

paragraphs = []
document_map = {}  # To track which paragraph belongs to which document

for filename in pdf_files:
    pdf_path = os.path.join(folder_path, filename)
    pdf_text = extract_text_from_pdf(pdf_path)

    if not pdf_text:
        print(f"⚠️ No text extracted from {filename}. It might be scanned.")
        continue

    extracted_paragraphs = [p for p in pdf_text.split("\n\n") if len(p) > 30]  # Ignore very short text
    
    if extracted_paragraphs:
        print(f"📄 Extracted {len(extracted_paragraphs)} paragraphs from {filename}")
    else:
        print(f"⚠️ No meaningful text found in {filename}")

    paragraphs.extend(extracted_paragraphs)

    # Store document mapping
    for p in extracted_paragraphs:
        document_map[p] = filename  # Each paragraph links to its document

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
# Compute pairwise cosine distance matrix
cosine_distance_matrix = squareform(pdist(embeddings, metric="cosine"))

# Run HDBSCAN using the precomputed distance matrix
clusterer = hdbscan.HDBSCAN(min_cluster_size=5, metric="precomputed")
clusters = clusterer.fit_predict(cosine_distance_matrix)

unique_clusters = set(clusters)
num_noise = sum(1 for c in clusters if c == -1)
print(f"✅ Clusters found: {unique_clusters}")
print(f"🔹 Noise points: {num_noise} ({(num_noise / len(clusters)) * 100:.2f}%)")
print(f"🔹 First 10 cluster labels: {clusters[:10]}")

# Store Clustered Paragraphs (including outliers)
clustered_paragraphs = {}
for i, cluster_id in enumerate(clusters):
    if cluster_id not in clustered_paragraphs:
        clustered_paragraphs[cluster_id] = []
    clustered_paragraphs[cluster_id].append((paragraphs[i], document_map[paragraphs[i]]))  # Keep track of source

if not clustered_paragraphs:
    print("❌ No clusters formed.")
    sys.exit()

# Print first 3 paragraphs per cluster (including outliers)
for cluster_id, para_list in clustered_paragraphs.items():
    if cluster_id == -1:
        print("\n🟠 Outlier Cluster (-1):")
    else:
        print(f"\n🟢 Cluster {cluster_id}:")
    
    for para, doc in para_list[:3]:  # Show first 3
        print(f" - [{doc}] {para[:200]}...")  # Print document name + paragraph

print("✅ Clustering complete!")
