import json
import re


def parse_llm_json(text: str) -> dict:
    """Strip markdown fences and parse JSON from LLM response."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)


EXTRACT_PROMPT = """
You are a resume parser. Extract from the resume below:
1. A list of technical and soft skills (be specific, include tools, languages, frameworks)
2. A 3-sentence experience summary

Resume:
{resume_text}

Respond ONLY with valid JSON. No explanation, no markdown fences.
{{
  "skills": ["skill1", "skill2", "..."],
  "experience_summary": "3 sentences summarizing experience..."
}}
"""

ANALYZE_PROMPT = """
You are a career coach. Given a candidate profile and a job posting, provide:
1. A match score from 0-100
2. Top 3 strengths that align with the role
3. Up to 3 skill gaps the candidate should address
4. A tailored 3-paragraph cover letter

Candidate skills: {skills}
Experience: {experience_summary}

Job title: {job_title}
Job description: {job_description}

Respond ONLY with valid JSON. No explanation, no markdown fences.
{{
  "match_score": 0,
  "strengths": ["strength1", "strength2", "strength3"],
  "skill_gaps": ["gap1", "gap2"],
  "cover_letter": "paragraph1\\n\\nparagraph2\\n\\nparagraph3"
}}
"""

TAILOR_PROMPT = """
You are an expert resume writer. Given a candidate's resume and a job description,
suggest specific rewrites to maximize ATS match and relevance.

For each suggestion:
- Quote the original line exactly as it appears in the resume
- Write an improved version tailored to the job
- Give a one-sentence reason why this change helps

Focus on: summary, skills section, and top 3 work experience bullets.
Maximum 6 suggestions total.

Resume:
{resume_text}

Job description:
{job_description}

Respond ONLY with valid JSON. No explanation, no markdown fences.
{{
  "suggestions": [
    {{
      "original": "exact original text from resume",
      "rewritten": "improved version tailored to job",
      "reason": "one sentence why this change helps"
    }}
  ]
}}
"""
