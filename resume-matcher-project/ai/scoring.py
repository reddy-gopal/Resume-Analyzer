from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from .parser import extract_skills

def calculate_relevance(resume_text, jd_text, required_skills):
    """
    Calculates a weighted relevance score based on TF-IDF, keyword match, and skill coverage.
    """
    # 1. TF-IDF Cosine Similarity (Content Relevance)
    try:
        vectorizer = TfidfVectorizer().fit([jd_text, resume_text])
        vectors = vectorizer.transform([jd_text, resume_text])
        tfidf_score = cosine_similarity(vectors)[0, 1]
    except ValueError:
        tfidf_score = 0.0

    # 2. Fuzzy Keyword Match (Overall Similarity)
    keyword_score = fuzz.token_set_ratio(jd_text, resume_text) / 100.0

    # 3. Skill Coverage (Crucial Skills Match)
    resume_skills_found = extract_skills(resume_text, required_skills)
    missing_skills = list(set(required_skills) - set(resume_skills_found))
    
    if not required_skills:
        skill_score = 1.0  # No skills required, so perfect score
    else:
        skill_score = len(resume_skills_found) / len(required_skills)

    # Weighted final score (out of 100)
    # Weights can be tuned: e.g., 50% content, 20% keyword, 30% skills
    final_score = (0.5 * tfidf_score + 0.2 * keyword_score + 0.3 * skill_score) * 100

    # Determine Verdict
    if final_score >= 75:
        verdict = "High"
    elif final_score >= 50:
        verdict = "Medium"
    else:
        verdict = "Low"

    return {
        "score": round(final_score, 2),
        "verdict": verdict,
        "missing_skills": missing_skills,
        "found_skills": resume_skills_found
    }