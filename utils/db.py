import os
import streamlit as st
from supabase import create_client

def get_supabase():
    """Get Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return create_client(url, key)

def _uid() -> str:
    """Get current user ID from session."""
    return st.session_state["user"].id

# ── Resume profile ──────────────────────────────────────────────

def get_profile() -> dict:
    """Get saved resume profile for current user."""
    try:
        supabase = get_supabase()
        res = supabase.table("resume_profiles").select("*").eq("user_id", _uid()).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def save_profile(resume_text: str, skills: list, experience_summary: str):
    """Save or update resume profile for current user."""
    try:
        supabase = get_supabase()
        supabase.table("resume_profiles").upsert({
            "user_id":            _uid(),
            "resume_text":        resume_text,
            "skills":             skills,
            "experience_summary": experience_summary,
        }, on_conflict="user_id").execute()
    except Exception as e:
        st.error(f"Could not save profile: {e}")

# ── Applications ────────────────────────────────────────────────

def get_applications() -> list:
    """Get all applications for current user."""
    try:
        supabase = get_supabase()
        res = (supabase.table("applications")
               .select("*")
               .eq("user_id", _uid())
               .order("created_at", desc=True)
               .execute())
        return res.data
    except Exception:
        return []

def save_application(job: dict):
    """Save a job application for current user."""
    try:
        supabase = get_supabase()
        supabase.table("applications").insert({
            "user_id":       _uid(),
            "job_title":     job.get("title", ""),
            "company":       job.get("company", ""),
            "location":      job.get("location", ""),
            "job_url":       job.get("url", ""),
            "adzuna_job_id": job.get("adzuna_job_id", ""),
            "match_score":   job.get("match_score", 0),
            "strengths":     job.get("strengths", []),
            "skill_gaps":    job.get("skill_gaps", []),
            "cover_letter":  job.get("cover_letter", ""),
            "source":        job.get("source", "adzuna"),
        }).execute()
    except Exception as e:
        st.error(f"Could not save application: {e}")

def update_application(app_id: str, status: str, notes: str):
    """Update status and notes for an application."""
    try:
        supabase = get_supabase()
        supabase.table("applications").update({
            "status": status,
            "notes":  notes,
        }).eq("id", app_id).eq("user_id", _uid()).execute()
    except Exception as e:
        st.error(f"Could not update application: {e}")

# ── Jobs seen (dedup) ───────────────────────────────────────────

def get_seen_job_ids() -> set:
    """Get all Adzuna job IDs already seen by current user."""
    try:
        supabase = get_supabase()
        res = (supabase.table("jobs_seen")
               .select("adzuna_job_id")
               .eq("user_id", _uid())
               .execute())
        return {row["adzuna_job_id"] for row in res.data}
    except Exception:
        return set()

def mark_jobs_seen(job_ids: list):
    """Mark a list of job IDs as seen for current user."""
    if not job_ids:
        return
    try:
        supabase = get_supabase()
        rows = [{"user_id": _uid(), "adzuna_job_id": jid} for jid in job_ids]
        supabase.table("jobs_seen").upsert(
            rows, on_conflict="user_id,adzuna_job_id"
        ).execute()
    except Exception:
        pass

# ── Tailored resumes ────────────────────────────────────────────

def save_tailored_resume(application_id: str, job_title: str, company: str,
                          original_text: str, tailored_text: str, suggestions: list):
    """Save a tailored resume for current user."""
    try:
        supabase = get_supabase()
        supabase.table("tailored_resumes").insert({
            "user_id":        _uid(),
            "application_id": application_id,
            "job_title":      job_title,
            "company":        company,
            "original_text":  original_text,
            "tailored_text":  tailored_text,
            "suggestions":    suggestions,
        }).execute()
    except Exception as e:
        st.error(f"Could not save tailored resume: {e}")
