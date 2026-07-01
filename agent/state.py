from typing import TypedDict, Optional


class AgentState(TypedDict):
    resume_text:            str
    skills:                 list[str]
    experience_summary:     str
    job_query:              str
    country_codes:          list[str]
    jobs:                   list[dict]
    analysis_results:       list[dict]
    tailoring_suggestions:  list[dict]
    accepted_rewrites:      list[dict]
    tailored_resume_text:   str
    target_jd:              Optional[str]
    custom_instructions:    Optional[str]
    error:                  Optional[str]
