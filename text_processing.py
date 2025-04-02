import os
import shutil
import docx
import pdfplumber
import string
import numpy as np
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import logging

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

# Suppress pdfplumber CropBox warnings at the start
logging.getLogger("pdfplumber").setLevel(logging.CRITICAL)

# Ensure NLTK dependencies are downloaded
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)

# Input and output directories
INPUT_FOLDER = "uploaded_docs"
CLUSTERED_FOLDER = "clustered_docs"

os.makedirs(CLUSTERED_FOLDER, exist_ok=True)  # Ensure output folder exists

# -------------------- FILE EXTRACTION FUNCTIONS --------------------

def read_docx(file_path):
    """Extract text from a .docx file."""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def read_pdf(file_path):
    """Extract text from a PDF file."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def read_txt(file_path):
    """Extract text from a .txt file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read().strip()

def extract_text(file_path):
    """Determine file type and extract text accordingly."""
    if file_path.endswith(".docx"):
        return read_docx(file_path)
    elif file_path.endswith(".pdf"):
        return read_pdf(file_path)
    elif file_path.endswith(".txt"):
        return read_txt(file_path)
    else:
        return None  # Unsupported file format

# -------------------- TEXT PREPROCESSING FUNCTIONS --------------------

def tokenize_text(text):
    """Convert text to lowercase and tokenize into words."""
    return word_tokenize(text.lower())

def remove_stopwords(tokens):
    """Remove common stopwords."""
    stop_words = set(stopwords.words("english"))
    return [word for word in tokens if word not in stop_words]

def remove_punctuation(tokens):
    """Remove punctuation from tokenized text."""
    return [word for word in tokens if word not in string.punctuation]

def lemmatize_tokens(tokens):
    """Convert words to their base form."""
    lemmatizer = WordNetLemmatizer()
    return [lemmatizer.lemmatize(word) for word in tokens]

def preprocess_text(text):
    """Full text preprocessing pipeline."""
    tokens = tokenize_text(text)
    tokens = remove_stopwords(tokens)
    tokens = remove_punctuation(tokens)
    tokens = lemmatize_tokens(tokens)
    return " ".join(tokens)  # Convert back to a string

# -------------------- DOCUMENT LOADING --------------------

def load_documents(folder_path):
    """Load and preprocess all documents in a folder."""
    documents, filenames = [], []

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            text = extract_text(file_path)
            if text:
                preprocessed_text = preprocess_text(text)
                documents.append(preprocessed_text)
                filenames.append(filename)

    return documents, filenames

# -------------------- CLUSTERING AND FILE ORGANIZATION --------------------

def cluster_documents(documents, filenames, num_clusters=2):
    """Cluster documents using K-Means and organize them into folders."""
    if not documents:
        print("No valid documents found for clustering.")
        return

    # Convert documents into TF-IDF features
    vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
    X = vectorizer.fit_transform(documents)

    # Apply K-Means clustering
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    kmeans.fit(X)
    clusters = kmeans.labels_

    # Organize files into clusters
    cluster_names = {}
    for i, filename in enumerate(filenames):
        cluster_id = clusters[i]
        
        # Assign meaningful names based on top keywords
        if cluster_id not in cluster_names:
            top_keywords = np.argsort(kmeans.cluster_centers_[cluster_id])[-5:]
            cluster_name = "_".join([vectorizer.get_feature_names_out()[i] for i in top_keywords])
            cluster_names[cluster_id] = cluster_name

        cluster_folder = os.path.join(CLUSTERED_FOLDER, cluster_names[cluster_id])
        os.makedirs(cluster_folder, exist_ok=True)

        # Copy the file to the appropriate cluster folder (instead of moving)
        shutil.copy(os.path.join(INPUT_FOLDER, filename), os.path.join(cluster_folder, filename))

    print(f"Documents clustered into {len(cluster_names)} categories successfully!")

# -------------------- PROGRAM EXECUTION --------------------

if __name__ == "__main__":
    print("Loading and processing documents...")
    documents, filenames = load_documents(INPUT_FOLDER)
    print(f"Found {len(documents)} documents: {filenames}")
    if not documents:
        print("No documents to cluster. Exiting.")
    else:
        print(f"Clustering {len(documents)} documents...")
        cluster_documents(documents, filenames, num_clusters=2)
        print("Clustering completed. Check clustered_docs folder.")