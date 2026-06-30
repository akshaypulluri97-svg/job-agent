import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from datetime import date
from utils.auth import require_auth
from utils.db import (
    get_profile, save_profile,
    get_applications, save_application, update_application,
    get_seen_job_ids, mark_jobs_seen,
    save_tailored_resume
)
from tools.resume_parser import extract_text_from_pdf
from agent.graph import build_graph
from tools.job_search import COUNTRIES, JOB_TYPES, FRESHNESS, browse_jobs_adzuna

st.set_page_config(page_title="Job Applications Agent", page_icon="💼", layout="wide")

# ── Auth gate ────────────────────────────────────────────────────
user = require_auth()

# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.write(f"👤 **{user.email}**")
    if st.button("Sign out"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    st.header("Search settings")
    COUNTRIES = {
        "Canada":    "ca",
        "USA":       "us",
        "India":     "in",
        "UK":        "gb",
        "Australia": "au",
        "Germany":   "de",
        "Singapore": "sg",
    }
    selected = st.multiselect(
        "Job locations",
        options=list(COUNTRIES.keys()),
        default=["Canada", "USA"],
    )
    country_codes = [COUNTRIES[c] for c in selected]

# ── Tabs ─────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Analyze resume",
    "My applications",
    "Daily new jobs",
    "Tailor resume",
    "Browse jobs",
])

# ════════════════════════════════════════════════════════════════
# TAB 1 — Analyze resume
# ════════════════════════════════════════════════════════════════
with tab1:
    st.header("Analyze your resume")
    profile  = get_profile()
    pdf_file = st.file_uploader("Upload resume PDF", type=["pdf"])
    target_jd = st.text_area("Paste a specific job description (optional)", height=150)

    if profile and not pdf_file:
        st.info(f"Using saved profile — {len(profile['skills'])} skills on record. Upload a new PDF to update it.")

    if st.button("Run analysis", type="primary"):
        if not pdf_file and not profile:
            st.error("Please upload your resume PDF first.")
        else:
            with st.spinner("Analyzing your resume and searching for jobs…"):
                if pdf_file:
                    resume_text = extract_text_from_pdf(pdf_file)
                else:
                    resume_text = profile["resume_text"]

                initial_skills = profile["skills"] if (profile and not pdf_file) else []
                initial_summary = profile["experience_summary"] if (profile and not pdf_file) else ""

                graph = build_graph()
                result = graph.invoke({
                    "resume_text":           resume_text,
                    "skills":                initial_skills,
                    "experience_summary":    initial_summary,
                    "job_query":             "",
                    "country_codes":         country_codes,
                    "jobs":                  [],
                    "analysis_results":      [],
                    "tailoring_suggestions": [],
                    "accepted_rewrites":     [],
                    "tailored_resume_text":  "",
                    "target_jd":             target_jd or None,
                    "error":                 None,
                })

                if pdf_file and result.get("skills"):
                    save_profile(resume_text, result["skills"], result["experience_summary"])

            if result.get("error"):
                st.error(f"Error: {result['error']}")
            else:
                st.subheader("Your profile")
                st.write("**Skills:**", ", ".join(result.get("skills", [])))
                st.write("**Summary:**", result.get("experience_summary", ""))
                st.divider()

                results = result.get("analysis_results", [])
                if not results:
                    st.info("No new jobs found. Try different locations or a broader skill set.")
                else:
                    st.subheader(f"Found {len(results)} job matches")
                    for job in results:
                        score = job.get("match_score", 0)
                        color = "green" if score >= 70 else "orange" if score >= 50 else "red"
                        label = f":{color}[{score}%] {job.get('title','Role')} — {job.get('company','')}"
                        if job.get("country"):
                            label += f" · {job['country']}"

                        with st.expander(label, expanded=score >= 70):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write("**✅ Strengths**")
                                for s in job.get("strengths", []):
                                    st.write(f"- {s}")
                            with col2:
                                st.write("**⚠️ Skill gaps**")
                                for g in job.get("skill_gaps", []):
                                    st.write(f"- {g}")

                            st.write("**📝 Cover letter**")
                            st.write(job.get("cover_letter", ""))

                            col_a, col_b = st.columns([1, 3])
                            with col_a:
                                if st.button("Save application", key=f"save_{job.get('adzuna_job_id', job.get('title',''))}"):
                                    save_application(job)
                                    st.success("Saved to tracker!")
                            with col_b:
                                if job.get("url"):
                                    st.link_button("View posting →", job["url"])

# ════════════════════════════════════════════════════════════════
# TAB 2 — My applications
# ════════════════════════════════════════════════════════════════
with tab2:
    st.header("My applications")
    apps = get_applications()

    if not apps:
        st.info("No applications saved yet. Run an analysis and click 'Save application'.")
    else:
        STATUS_OPTIONS = ["applied", "interview", "offer", "rejected", "ghosted"]
        st.write(f"**{len(apps)} applications tracked**")

        for app in apps:
            applied = app.get("applied_date", str(date.today()))
            try:
                days = (date.today() - date.fromisoformat(applied)).days
            except Exception:
                days = 0

            score = app.get("match_score", 0)
            color = "green" if score >= 70 else "orange" if score >= 50 else "red"
            label = f":{color}[{score}%] {app['job_title']} — {app.get('company','')} · {days}d ago"

            with st.expander(label):
                col1, col2 = st.columns(2)
                with col1:
                    current_status = app.get("status", "applied")
                    if current_status not in STATUS_OPTIONS:
                        current_status = "applied"
                    new_status = st.selectbox(
                        "Status",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(current_status),
                        key=f"status_{app['id']}",
                    )
                with col2:
                    if days >= 7 and app.get("status") == "applied":
                        st.warning(f"⏰ No response in {days} days — consider following up!")

                new_notes = st.text_area(
                    "Notes",
                    value=app.get("notes") or "",
                    key=f"notes_{app['id']}",
                )

                if st.button("Update", key=f"update_{app['id']}"):
                    update_application(app["id"], new_status, new_notes)
                    st.success("Updated!")

                if app.get("cover_letter"):
                    with st.expander("Cover letter"):
                        st.write(app["cover_letter"])

                if app.get("job_url"):
                    st.link_button("View posting →", app["job_url"])

# ════════════════════════════════════════════════════════════════
# TAB 3 — Daily new jobs
# ════════════════════════════════════════════════════════════════
with tab3:
    st.header("New jobs since your last visit")
    profile = get_profile()

    if not profile:
        st.warning("Save your resume first in the Analyze tab.")
    else:
        st.write(f"Searching with your saved skills across: **{', '.join(selected) or 'no countries selected'}**")

        if st.button("Check for new jobs", type="primary"):
            with st.spinner("Searching for jobs you haven't seen yet…"):
                graph = build_graph()
                result = graph.invoke({
                    "resume_text":           profile["resume_text"],
                    "skills":                profile["skills"],
                    "experience_summary":    profile["experience_summary"],
                    "job_query":             "",
                    "country_codes":         country_codes,
                    "jobs":                  [],
                    "analysis_results":      [],
                    "tailoring_suggestions": [],
                    "accepted_rewrites":     [],
                    "tailored_resume_text":  "",
                    "target_jd":             None,
                    "error":                 None,
                })

            results = result.get("analysis_results", [])
            if not results:
                st.success("✅ You're all caught up — no new matching jobs since last time!")
            else:
                st.write(f"Found **{len(results)} new jobs:**")
                for job in results:
                    score = job.get("match_score", 0)
                    color = "green" if score >= 70 else "orange" if score >= 50 else "red"
                    with st.expander(f":{color}[{score}%] {job.get('title','')} — {job.get('company','')} · {job.get('country','')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**✅ Strengths**")
                            for s in job.get("strengths", []):
                                st.write(f"- {s}")
                        with col2:
                            st.write("**⚠️ Skill gaps**")
                            for g in job.get("skill_gaps", []):
                                st.write(f"- {g}")
                        st.write(job.get("cover_letter", ""))
                        col_a, col_b = st.columns([1, 3])
                        with col_a:
                            if st.button("Save", key=f"daily_{job.get('adzuna_job_id','')}"):
                                save_application(job)
                                st.success("Saved!")
                        with col_b:
                            if job.get("url"):
                                st.link_button("View posting →", job["url"])

# ════════════════════════════════════════════════════════════════
# TAB 4 — Tailor resume
# ════════════════════════════════════════════════════════════════
with tab4:
    st.header("Tailor your resume to a job")
    profile = get_profile()

    if not profile:
        st.warning("Save your resume first in the Analyze tab.")
    else:
        apps = get_applications()
        job_options = {f"{a['job_title']} — {a.get('company','')}": a for a in apps}

        col1, col2 = st.columns(2)
        with col1:
            selected_job = st.selectbox(
                "Pick a saved application",
                ["— paste a JD instead —"] + list(job_options.keys()),
            )
        with col2:
            custom_jd = st.text_area("Or paste a job description", height=150)

        if selected_job != "— paste a JD instead —":
            target_jd = job_options[selected_job].get("cover_letter", custom_jd)
        else:
            target_jd = custom_jd

        if st.button("Generate suggestions", type="primary"):
            if not target_jd:
                st.error("Please select a job or paste a job description.")
            else:
                with st.spinner("Analyzing your resume against the job description…"):
                    graph = build_graph()
                    result = graph.invoke({
                        "resume_text":           profile["resume_text"],
                        "skills":                profile["skills"],
                        "experience_summary":    profile["experience_summary"],
                        "job_query":             "",
                        "country_codes":         [],
                        "jobs":                  [],
                        "analysis_results":      [],
                        "tailoring_suggestions": [],
                        "accepted_rewrites":     [],
                        "tailored_resume_text":  "",
                        "target_jd":             target_jd,
                        "error":                 None,
                    })
                st.session_state["suggestions"] = result.get("tailoring_suggestions", [])
                st.session_state["accepted"]    = [False] * len(st.session_state["suggestions"])

        if st.session_state.get("suggestions"):
            st.subheader("Suggested rewrites")
            st.caption("Accept the changes you want, then build your tailored resume.")

            for i, s in enumerate(st.session_state["suggestions"]):
                with st.expander(f"Suggestion {i+1} — {s.get('reason','')}", expanded=True):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write("**Original**")
                        st.info(s.get("original", ""))
                    with col_b:
                        st.write("**Suggested rewrite**")
                        st.success(s.get("rewritten", ""))
                    st.session_state["accepted"][i] = st.checkbox(
                        "Accept this change",
                        value=st.session_state["accepted"][i],
                        key=f"accept_{i}",
                    )

            if st.button("Build tailored resume", type="primary"):
                tailored = profile["resume_text"]
                for i, s in enumerate(st.session_state["suggestions"]):
                    if st.session_state["accepted"][i]:
                        tailored = tailored.replace(s.get("original",""), s.get("rewritten",""))

                app_id = None
                company = ""
                title = selected_job if selected_job != "— paste a JD instead —" else "Custom JD"
                if selected_job in job_options:
                    app_id  = job_options[selected_job].get("id")
                    company = job_options[selected_job].get("company", "")

                save_tailored_resume(
                    application_id=app_id,
                    job_title=title,
                    company=company,
                    original_text=profile["resume_text"],
                    tailored_text=tailored,
                    suggestions=st.session_state["suggestions"],
                )

                st.download_button(
                    label="⬇️ Download tailored resume (.txt)",
                    data=tailored,
                    file_name="tailored_resume.txt",
                    mime="text/plain",
                )
                st.success("Tailored resume saved to your profile!")

# ════════════════════════════════════════════════════════════════
# TAB 5 — Browse jobs
# ════════════════════════════════════════════════════════════════
with tab5:
    st.header("Browse job postings")
    st.caption("Search real-time jobs powered by Adzuna across 7 countries.")

    # ── Filters ─────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        browse_keyword = st.text_input("Keyword", placeholder="e.g. Data Analyst")
    with col2:
        browse_country = st.selectbox("Country", options=list(COUNTRIES.keys()))
    with col3:
        browse_job_type = st.selectbox("Job type", options=list(JOB_TYPES.keys()))
    with col4:
        browse_freshness = st.selectbox("Posted within", options=list(FRESHNESS.keys()))

    if "browse_page" not in st.session_state:
        st.session_state["browse_page"] = 1

    search_clicked = st.button("Search jobs", type="primary")
    if search_clicked:
        st.session_state["browse_page"] = 1

    # ── Fetch jobs ───────────────────────────────────────────────
    country_code = COUNTRIES[browse_country]
    days_old     = FRESHNESS[browse_freshness]

    result = browse_jobs_adzuna(
            keyword=browse_keyword or "data analyst",
            country_code=country_code,
            job_type=browse_job_type,
            days_old=days_old,
            page=st.session_state["browse_page"],
            results=10,
        )

    # ── Results ──────────────────────────────────────────────────
    if result["error"]:
        st.error(f"Search error: {result['error']}")
    else:
        jobs  = result["jobs"]
        total = result["total"]
        st.caption(f"Found **{total:,}** jobs · page {st.session_state['browse_page']}")

        if not jobs:
            st.info("No jobs found. Try a different keyword, country, or time range.")
        else:
            for job in jobs:
                with st.container():
                    col_a, col_b = st.columns([5, 1])
                    with col_a:
                        st.markdown(f"### {job['title']}")
                        st.markdown(
                            f"🏢 **{job.get('company','N/A')}** &nbsp;|&nbsp; "
                            f"📍 {job.get('location','N/A')} &nbsp;|&nbsp; "
                            f"💰 {job.get('salary','Not specified')} &nbsp;|&nbsp; "
                            f"📅 {job.get('created','N/A')}"
                        )
                        if job.get("category"):
                            st.caption(f"Type: {job['category']}")
                        with st.expander("View description"):
                            st.write(job.get("description","No description available."))
                    with col_b:
                        st.write("")
                        st.write("")
                        if job.get("url"):
                            st.link_button("Apply →", job["url"])
                        if st.button("💾 Save", key=f"browse_save_{job.get('adzuna_job_id', job.get('title',''))}"):
                            save_application(job)
                            st.success("Saved!")
                    st.divider()

        # ── Pagination ───────────────────────────────────────────
        col_prev, _, col_next = st.columns([1, 3, 1])
        with col_prev:
            if st.session_state["browse_page"] > 1:
                if st.button("← Previous"):
                    st.session_state["browse_page"] -= 1
                    st.rerun()
        with col_next:
            if len(jobs) >= 10:
                if st.button("Next →"):
                    st.session_state["browse_page"] += 1
                    st.rerun()
