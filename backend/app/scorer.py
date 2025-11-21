import pdfplumber
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def extract_text_from_pdf(file_bytes):
    """
    Opens a PDF file from memory and extracts text.
    """
    try:
        # pdfplumber requires a file-like object, so we might need io.BytesIO in main.py
        # For simplicity here, we assume valid text extraction logic
        with pdfplumber.open(file_bytes) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() or ""
        return full_text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def calculate_match_score(resume_text, job_description):
    """
    Compares resume vs job description using TF-IDF and Cosine Similarity.
    Returns a score between 0 and 100.
    """
    if not resume_text or not job_description:
        return 0
    
    # Clean text (basic)
    documents = [resume_text, job_description]
    
    # 1. Create the Vectorizer
    # stop_words='english' removes words like "the", "and", "is"
    tfidf = TfidfVectorizer(stop_words='english')
    
    try:
        # 2. Convert text to matrix of numbers
        tfidf_matrix = tfidf.fit_transform(documents)
        
        # Convert the sparse matrix to a standard dense array to satisfy the type checker
        dense_matrix = tfidf_matrix.toarray() # type: ignore
        
        # Calculate Cosine Similarity between Row 0 (Resume) and Row 1 (Job)
        # We pass slices [0:1] and [1:2] to keep them 2D, which cosine_similarity prefers
        similarity_matrix = cosine_similarity(dense_matrix[0:1], dense_matrix[1:2])
        
        # The result is a [[0.45]] matrix, so we grab [0][0]
        similarity_val = similarity_matrix[0][0]
        
        # 4. Convert to percentage (0-100)
        score = int(similarity_val * 100)
        return score
    except ValueError:
        # Happens if documents are empty or only contain stop words
        return 0