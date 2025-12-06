# utils.py

import os
import re
import string 
from pypdf import PdfReader
import docx2txt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# --- 1. File Extraction ---

def extract_text_from_file(file_path):
    """Extracts text from PDF, DOCX, or TXT files."""
    text = ""
    # Check if the path is a file or the raw JD text
    if not os.path.exists(file_path) or os.path.isdir(file_path):
         return file_path 
         
    ext = os.path.splitext(file_path)[1].lower()

    try:
        if ext == '.pdf':
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() or ''
        elif ext == '.docx':
            text = docx2txt.process(file_path)
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

        # Basic cleaning: lowercase and standardize whitespace
        text = ' '.join(text.split()).lower()
        return text
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return ""


# --- 2. Core Matching (TF-IDF & Cosine Similarity) ---

def calculate_similarity(job_description_text, resume_texts):
    """
    Calculates cosine similarity between the Job Description and multiple resumes.
    Returns: A list of similarity scores.
    """
    if not job_description_text or not resume_texts:
        return []

    # Combine JD and Resume texts. JD is always the first document.
    documents = [job_description_text] + resume_texts

    # Vectorization (TF-IDF)
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)

    # Similarity Calculation (Compare JD vector [0] against all others [1:])
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    
    # Extract the scores and convert them to a percentage
    scores = [round(score * 100, 2) for score in cosine_sim[0]]
    
    return scores

def get_top_matches(resume_files, scores, top_n=5):
    """Sorts resumes by score and returns the top N matches."""
    # Combine results and sort by score in descending order
    results = sorted(zip(resume_files, scores), key=lambda x: x[1], reverse=True)
    
    # Return top N results
    return results[:top_n]