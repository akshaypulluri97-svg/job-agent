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

ATS_EXTRACT_PROMPT = """
You are an enterprise ATS (Applicant Tracking System) engine used by Fortune 500 companies to rank candidates.

Your job is to parse this job description and extract ONLY the keywords and phrases that an ATS would use to rank candidates. Be precise — these keywords will be matched against a candidate's resume.

Rules:
- Use exact phrases as they appear in the JD (e.g. "Apache Spark" not just "spark")
- Separate must-have from preferred requirements
- Include tools, platforms, languages, frameworks, methodologies, certifications
- Include key job functions (what the person will actually do day-to-day)
- EXCLUDE: company name, location, salary, benefits, generic phrases like "team player"
- EXCLUDE: French or non-English words if the JD is bilingual — English terms only
- Maximum 8 items per category

Job description:
{job_description}

Respond ONLY with valid JSON. No explanation, no markdown fences.
{{
  "must_have": ["exact phrase 1", "exact phrase 2"],
  "preferred": ["exact phrase 1", "exact phrase 2"],
  "tools_platforms": ["tool 1", "tool 2"],
  "certifications": ["cert 1"],
  "job_functions": ["function 1", "function 2"]
}}
"""

ATS_GAP_PROMPT = """
You are a senior ATS analyst. Compare this candidate's resume against the extracted ATS keywords and score the match.

For each keyword, determine if it is:
- PRESENT: clearly mentioned or strongly implied in the resume
- MISSING: not mentioned at all
- PARTIAL: mentioned but not emphasized enough

Candidate resume:
{resume_text}

ATS keywords extracted from job description:
Must-have: {must_have}
Preferred: {preferred}
Tools/Platforms: {tools_platforms}
Job functions: {job_functions}

Respond ONLY with valid JSON. No explanation, no markdown fences.
{{
  "matched": ["keyword1", "keyword2"],
  "missing_critical": ["keyword1", "keyword2"],
  "missing_preferred": ["keyword1", "keyword2"],
  "partial": ["keyword1", "keyword2"],
  "ats_score": 0,
  "summary": "one sentence honest assessment of the match"
}}
"""

TAILOR_PROMPT = """
You are a world-class resume writer and ATS optimization expert who has helped thousands of candidates land roles at Google, Amazon, Goldman Sachs, and top banks.

Your goal: Transform this resume to maximize both ATS ranking AND senior HR appeal for the target role — without fabricating experience or exaggerating qualifications.

CONTEXT:
- Candidate resume: {resume_text}
- Target job description: {job_description}
- ATS keywords missing from resume: {missing_keywords}
- Custom instructions from candidate: {custom_instructions}

YOUR TASK — suggest exactly 6 high-impact rewrites following these priorities:
1. SUMMARY REWRITE (mandatory) — rewrite the professional summary to mirror the job title, 
   incorporate top ATS keywords naturally, and open with a powerful value proposition
2. SKILLS SECTION (mandatory) — restructure or expand skills to include missing ATS keywords 
   that the candidate genuinely has
3. TOP 3 EXPERIENCE BULLETS — rewrite the most relevant bullets to:
   - Start with powerful action verbs (Architected, Engineered, Delivered, Spearheaded)
   - Include missing ATS keywords naturally where truthful
   - Quantify impact (add metrics, percentages, scale if inferable from context)
   - Match the seniority and language of the target role
4. Apply custom instructions precisely if provided

RULES:
- Only reframe what exists — never invent tools, companies, or achievements
- Use exact keyword phrases from the JD (e.g. "data pipeline orchestration" not just "pipelines")
- Each rewrite must be noticeably better than the original — not just a word swap
- Senior HR test: would a Director of Engineering or VP of Data be impressed by this bullet?

Respond ONLY with valid JSON. No explanation, no markdown fences.
{{
  "suggestions": [
    {{
      "section": "Summary | Skills | Experience",
      "original": "exact original text copied from the resume",
      "rewritten": "powerful rewrite — ATS-optimized, quantified, senior HR ready",
      "reason": "one sentence on why this change improves ATS rank and HR appeal",
      "keywords_added": ["keyword1", "keyword2"]
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