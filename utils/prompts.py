import json
import re


def parse_llm_json(text: str) -> dict:
    """Strip markdown fences and parse JSON from LLM response."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)


EXTRACT_PROMPT = """
You are an elite resume parser and career analyst. Your job is to extract structured information from a resume with high precision.

Extract the following:
1. A comprehensive list of skills — include programming languages, frameworks, tools, cloud platforms, databases, methodologies (Agile, Scrum), and soft skills (leadership, communication). Be granular: "Python" and "PySpark" are separate skills.
2. A punchy 3-sentence experience summary that highlights seniority, domain expertise, and measurable impact.

Resume:
{resume_text}

Respond ONLY with valid JSON. No explanation, no markdown fences.
{{
  "skills": ["skill1", "skill2", "..."],
  "experience_summary": "3 sentences summarizing experience, seniority, and impact..."
}}
"""

ANALYZE_PROMPT = """
You are a senior recruiter and career coach with 15 years of experience placing candidates at top companies. Evaluate this candidate against the job posting with honest, specific feedback.

Candidate skills: {skills}
Candidate experience: {experience_summary}

Job title: {job_title}
Job description: {job_description}

Provide:
1. A match score from 0-100. Be accurate — 90+ means near-perfect fit, 50-70 means viable with gaps, below 50 means significant mismatch.
2. Top 3 specific strengths that directly align with THIS role (not generic praise).
3. Up to 3 concrete skill gaps that would hurt this candidate's chances (be honest).
4. A compelling 3-paragraph cover letter that: (a) opens with a hook showing knowledge of the company/role, (b) connects 2-3 specific achievements to the role's requirements, (c) closes with confidence and a clear call to action. Do NOT use generic filler phrases like "I am excited to apply".

Respond ONLY with valid JSON. No explanation, no markdown fences.
{{
  "match_score": 0,
  "strengths": ["specific strength 1", "specific strength 2", "specific strength 3"],
  "skill_gaps": ["specific gap 1", "specific gap 2"],
  "cover_letter": "paragraph1\\n\\nparagraph2\\n\\nparagraph3"
}}
"""

TAILOR_PROMPT = """
You are an elite resume writer and ATS optimization expert. Your goal is to rewrite specific lines of the candidate's resume to maximize relevance for the target role — without fabricating experience or exaggerating qualifications.

Rules:
- Only suggest changes that are grounded in what the candidate already has — rephrase, reframe, and emphasize, never invent.
- Mirror the exact language and keywords from the job description where truthful.
- Prioritize high-impact sections: professional summary, skills, and top work experience bullets.
- Each rewrite should be more specific, quantified, and action-oriented than the original.
- Maximum 6 suggestions. Quality over quantity.
- If the candidate provided custom instructions, follow them precisely.

Candidate resume:
{resume_text}

Target job description:
{job_description}

Custom instructions from candidate (follow these if provided):
{custom_instructions}

Respond ONLY with valid JSON. No explanation, no markdown fences.
{{
  "suggestions": [
    {{
      "original": "exact original text copied from the resume",
      "rewritten": "improved version — specific, keyword-rich, and tailored to the job",
      "reason": "one sentence explaining why this change improves ATS match or recruiter appeal"
    }}
  ]
}}
"""

QUICK_SCORE_PROMPT = """
You are a technical recruiter. Given a candidate's profile and a job description, return an honest match score.

Score from 0-100:
- 85-100: Strong match, most requirements met
- 65-84: Good match, minor gaps
- 45-64: Partial match, notable gaps
- Below 45: Weak match, significant mismatch

Candidate skills: {skills}
Candidate experience: {experience_summary}

Job description:
{job_description}

Respond ONLY with valid JSON. No explanation, no markdown fences.
{{"match_score": 0}}
"""
