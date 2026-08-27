from pydantic import BaseModel, Field


class CompanyBrief(BaseModel):
    company_name: str
    what_they_do: str
    industry: str
    employee_count: str = Field(description="approximate; 'N/A' if unknown")
    tech_stack: list[str]
    likely_skills: list[str] = Field(
        description="skills they'd want in a backend/data engineer"
    )
    questions_to_ask: list[str]
    sources: list[str] = Field(description="URLs the info came from")
    projects_to_focus: list[str] = Field(
        description="which of MY projects to highlight for this company, and why"
    )
    my_matching_skills: list[str] = Field(
        description="MY skills from the resume that match their needs"
    )
    skills_to_brush_up: list[str] = Field(
        description="gaps between their needs and my resume that I should revise"
    )
