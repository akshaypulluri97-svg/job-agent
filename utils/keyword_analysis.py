"""Keyword frequency analysis — compare resume vs job description."""
import re
from collections import Counter

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "must", "can", "not",
    "no", "nor", "so", "yet", "both", "either", "neither", "than", "such",
    "that", "this", "these", "those", "it", "its", "we", "our", "you",
    "your", "he", "she", "they", "their", "i", "my", "me", "us", "what",
    "which", "who", "how", "when", "where", "why", "all", "each", "any",
    "some", "more", "most", "other", "into", "through", "about", "above",
    "after", "before", "between", "during", "including", "up", "out", "if",
    "then", "also", "just", "over", "under", "per", "within", "without",
    "however", "therefore", "thus", "while", "since", "although", "across",
    "ensure", "required", "experience", "skills", "role", "team", "work",
    "working", "years", "ability", "strong", "excellent", "good", "well",
    "key", "new", "will", "provide", "using", "including", "develop",
    "support", "responsible", "collaborate", "help", "join", "looking",
    "company", "position", "job", "opportunity", "candidate", "minimum",
    "preferred", "plus", "bonus", "etc", "eg", "ie", "via", "vs",
    "related", "relevant", "demonstrated", "proven", "knowledge",
    "understanding", "familiarity", "exposure", "background", "track",
    "record", "hands", "equivalent", "combination", "education", "degree",
    "bachelor", "master", "phd", "field", "discipline", "area", "range",
    "least", "must", "nice", "have", "highly", "desirable", "considered",
    "asset", "based", "focused", "driven", "oriented", "level",
    "senior", "junior", "mid", "lead", "staff", "principal", "associate",
    "full", "part", "time", "contract", "permanent", "temporary", "remote",
    "hybrid", "office", "location", "travel", "relocation", "visa",
    "business", "service", "services", "solution", "solutions", "product",
    "products", "client", "clients", "customer", "customers", "stakeholder",
    "stakeholders", "partner", "partners", "vendor", "vendors", "internal",
    "external", "global", "local", "national", "international", "enterprise",
    "organization", "member", "members", "cross", "functional",
    "environment", "fast", "paced", "dynamic", "innovative", "collaborative",
    "communication", "interpersonal", "written", "verbal", "presentation",
    "management", "manager", "director", "executive", "officer", "head",
    "report", "reporting", "meeting", "meetings", "daily", "weekly", "monthly",
    "inc", "ltd", "llc", "corp", "corporation", "group", "holdings",
    "canada", "usa", "united", "states", "north", "america", "ontario",
    "toronto", "vancouver", "montreal", "calgary", "ottawa",
    "broadband", "fibre", "rural", "living", "satellite", "wireless",
    "network", "networks", "connectivity", "internet", "speed",
}


def extract_keywords(text: str) -> Counter:
    """Extract meaningful keywords from text, filtering stop words."""
    words = re.findall(r"\b[a-z][a-z0-9+#\.\-]{1,}\b", text.lower())
    filtered = [
        w for w in words
        if w not in STOP_WORDS
        and len(w) > 2
        and not w.isdigit()
        and not re.match(r"^\d+[a-z]?$", w)
    ]
    return Counter(filtered)


def keyword_gap_analysis(resume_text: str, jd_text: str, top_n: int = 20) -> dict:
    jd_freq     = extract_keywords(jd_text)
    resume_freq = extract_keywords(resume_text)

    jd_top   = jd_freq.most_common(top_n)
    jd_words = [w for w, _ in jd_top]

    missing = [w for w in jd_words if resume_freq.get(w, 0) == 0]
    present = [w for w in jd_words if resume_freq.get(w, 0) > 0]

    coverage = round(len(present) / len(jd_words) * 100, 1) if jd_words else 0.0

    return {
        "jd_top":       jd_top,
        "resume_freq":  {w: resume_freq.get(w, 0) for w in jd_words},
        "missing":      missing,
        "present":      present,
        "coverage_pct": coverage,
    }