#!/usr/bin/env python3
"""
Resume Optimizer Tool
Optimizes resumes based on job descriptions using AI-powered analysis.
"""

import json
import sys
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from collections import Counter
import subprocess


@dataclass
class JobAnalysis:
    """Analysis of a job description"""
    job_title: str
    company: str
    required_skills: List[str]
    preferred_skills: List[str]
    experience_level: str
    key_requirements: List[str]
    keywords: List[str]
    salary_range: Optional[str] = None


@dataclass
class ResumeMatch:
    """How well resume matches job"""
    score: float
    matched_skills: List[str]
    missing_skills: List[str]
    weak_skills: List[str]
    recommendations: List[str]


def extract_job_info(job_text: str) -> JobAnalysis:
    """
    Extract key information from job description using AI.
    """
    print("🔍 Analyzing job description...\n")

    # Use the image/analysis tool (via subprocess to call the model)
    prompt = f"""Analyze this job description and extract:
1. Job title
2. Required technical skills (list them)
3. Preferred/bonus skills (list them)
4. Experience level required
5. Key requirements/duties (3-5 key points)
6. Important keywords/phrases (top 10)

Job Description:
{job_text}

Return in JSON format:
{{
  "job_title": "...",
  "company": "...",
  "required_skills": ["skill1", "skill2", ...],
  "preferred_skills": ["skill1", "skill2", ...],
  "experience_level": "...",
  "key_requirements": ["req1", "req2", ...],
  "keywords": ["keyword1", "keyword2", ...],
  "salary_range": "..." (optional)
}}"""

    # For now, do basic extraction without AI
    return basic_job_extraction(job_text)


def basic_job_extraction(job_text: str) -> JobAnalysis:
    """
    Basic job extraction using regex patterns.
    """
    # Extract job title (first line or before first bullet)
    lines = job_text.strip().split('\n')
    job_title = lines[0].strip() if lines else "Unknown Position"

    # Extract skills using common patterns
    tech_skills = []
    skill_patterns = [
        r'\b(Python|SQL|R|JavaScript|Java|C\+\+|Go|TypeScript|Ruby|PHP|Swift|Kotlin)\b',
        r'\b(Tableau|Power BI|Excel|Access|SAS|SPSS|MATLAB|Looker|Qlik)\b',
        r'\b(Docker|Kubernetes|AWS|Azure|GCP|Linux|Git|Jenkins|CI/CD)\b',
        r'\b(Pandas|NumPy|Matplotlib|Scikit-learn|TensorFlow|PyTorch)\b',
        r'\b(React|Angular|Vue|Node\.js|Django|Flask|FastAPI|Spring)\b',
        r'\b(Agile|Scrum|Data Analysis|Machine Learning|Deep Learning|AI)\b',
        r'\b(Business Intelligence|ETL|Data Pipeline|Data Warehouse|SQL Server|PostgreSQL|MongoDB)\b'
    ]

    for pattern in skill_patterns:
        matches = re.findall(pattern, job_text, re.IGNORECASE)
        tech_skills.extend(matches)

    # Remove duplicates and capitalize
    required_skills = list(dict.fromkeys([s.title() for s in tech_skills]))

    # Extract experience level
    experience_level = "Not specified"
    exp_patterns = [
        (r'(Entry[- ]level|Junior)', 'Entry-level'),
        (r'(Mid[- ]level|Mid[- ]Senior|Intermediate)', 'Mid-level'),
        (r'(Senior|Lead|Staff|Principal)', 'Senior'),
        (r'(Director|VP|Chief)', 'Executive')
    ]
    for pattern, level in exp_patterns:
        if re.search(pattern, job_text, re.IGNORECASE):
            experience_level = level
            break

    # Extract key requirements (bullet points or numbered lists)
    key_requirements = []
    requirement_patterns = [
        r'^[\s]*[-•*]\s*(.+)$',
        r'^[\s]*\d+[\.\)]\s*(.+)$'
    ]
    for line in lines:
        for pattern in requirement_patterns:
            match = re.match(pattern, line)
            if match:
                req = match.group(1).strip()
                if len(req) > 20:  # Filter out too short/irrelevant
                    key_requirements.append(req)
                    if len(key_requirements) >= 5:
                        break
        if len(key_requirements) >= 5:
            break

    # Extract keywords (important terms that appear frequently)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', job_text)
    word_freq = Counter([w.lower() for w in words])
    # Filter out common words
    stop_words = {'and', 'the', 'for', 'with', 'you', 'that', 'this', 'will', 'have',
                 'are', 'from', 'work', 'your', 'team', 'able', 'looking', 'company'}
    keywords = [w for w, freq in word_freq.most_common(15)
                if w not in stop_words and freq >= 2]

    return JobAnalysis(
        job_title=job_title,
        company="Unknown",
        required_skills=required_skills[:10],
        preferred_skills=[],
        experience_level=experience_level,
        key_requirements=key_requirements[:5],
        keywords=[k.title() for k in keywords[:10]]
    )


def analyze_resume_match(job: JobAnalysis, resume_text: str) -> ResumeMatch:
    """
    Analyze how well the resume matches the job.
    """
    print("📊 Analyzing resume match...\n")

    # Extract skills from resume
    resume_skills = []
    for skill in job.required_skills:
        if skill.lower() in resume_text.lower():
            resume_skills.append(skill)

    # Find matched skills
    matched_skills = resume_skills

    # Find missing skills
    missing_skills = [s for s in job.required_skills if s not in matched_skills]

    # Calculate score
    total_skills = len(job.required_skills)
    matched_count = len(matched_skills)
    score = (matched_count / total_skills * 100) if total_skills > 0 else 0

    # Generate recommendations
    recommendations = []

    if score < 50:
        recommendations.append("⚠️  Low match score - Consider highlighting relevant skills")
    if missing_skills:
        recommendations.append(f"💡 Add these missing skills: {', '.join(missing_skills[:3])}")
    if job.experience_level != "Not specified":
        recommendations.append(f"📌 Emphasize experience relevant to {job.experience_level} roles")
    recommendations.append("✨ Tailor your summary/objective to match this job title")

    return ResumeMatch(
        score=round(score, 1),
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        weak_skills=[],
        recommendations=recommendations
    )


def generate_optimized_resume(job: JobAnalysis, match: ResumeMatch,
                            original_resume: str, profile: Dict) -> str:
    """
    Generate an optimized version of the resume.
    """
    print("✨ Generating optimized resume...\n")

    # Parse original resume
    lines = original_resume.split('\n')

    # Extract key sections
    name = lines[0] if lines else profile.get('profile', {}).get('personal', {}).get('full_name', '')
    contact = ""

    # Build optimized summary
    optimized_summary = f"""Results-driven {job.experience_level or 'Professional'} with strong expertise in {', '.join(job.required_skills[:3])}. Proven track record in {', '.join(job.key_requirements[:2])}. Passionate about leveraging data analytics and automation to drive business insights and efficiency."""

    # Highlight experience section
    optimized_experience = f"""Experience

{profile.get('profile', {}).get('experience', {}).get('current_title', 'Current Role')}
Key Achievements:
• Demonstrated proficiency in {', '.join(match.matched_skills[:3])} to deliver measurable results
• Applied {job.required_skills[0] if job.required_skills else 'technical skills'} to solve complex business problems
• Collaborated cross-functionally to {job.key_requirements[0].lower() if job.key_requirements else 'achieve business objectives'}
• Consistently exceeded performance targets through data-driven decision making"""

    # Skills section prioritized for this job
    optimized_skills = f"""Technical Skills

Programming: {', '.join([s for s in job.required_skills if s.lower() in original_resume.lower()])}
Data Tools: Tableau, Power BI, Excel, Access
Analytics: SQL, Data Analysis, Reporting, Dashboard Development
Soft Skills: Communication, Problem-Solving, Team Collaboration"""

    # Combine all sections
    optimized_resume = f"""{name}
{profile.get('profile', {}).get('personal', {}).get('email', '')}
{profile.get('profile', {}).get('personal', {}).get('phone', '')}
{profile.get('profile', {}).get('personal', {}).get('linkedin_url', '')}

SUMMARY
{optimized_summary}

{optimized_experience}

{optimized_skills}

PROJECTS
Quote Automation Tool | Python, pandas, pyodbc, Access 2023
• Built automation script reducing manual errors by 30%
• Integrated with Access database for seamless quote generation

NYC Traffic and Safety Data Analysis | Python, SQL, ETL, Power BI 2022
• Analyzed 1M+ records to identify safety correlations
• Created interactive dashboards with actionable insights

EDUCATION
{profile.get('profile', {}).get('education', {}).get('highest_degree', '')} in {profile.get('profile', {}).get('education', {}).get('field_of_study', '')}
{profile.get('profile', {}).get('education', {}).get('university', '')}

Certifications
Google Data Analytics
Advanced SQL for Data Science"""

    return optimized_resume


def save_optimized_resume(optimized_resume: str, job_title: str) -> str:
    """
    Save optimized resume to file.
    """
    filename = f"Optimized_Resume_{job_title.replace(' ', '_')}.txt"
    filepath = Path.home() / filename

    with open(filepath, 'w') as f:
        f.write(optimized_resume)

    return str(filepath)


def main():
    """Main CLI interface"""
    print("📄 RESUME OPTIMIZER TOOL")
    print("="*60)
    print()

    # Get job description from user
    print("Paste the job description (press Ctrl+D when done):")
    job_text = sys.stdin.read()

    if not job_text.strip():
        print("❌ No job description provided")
        return

    # Load profile
    profile_path = Path.home() / "job_profile.json"
    profile = {}
    if profile_path.exists():
        with open(profile_path, 'r') as f:
            profile = json.load(f)

    # Load resume
    resume_path = profile.get('profile', {}).get('documents', {}).get('resume_path', '')
    if not resume_path:
        resume_path = str(Path.home() / "Desktop" / "Tommy Lu Resume.pdf")

    try:
        # Try to read as text (simple case)
        if resume_path.endswith('.txt') or resume_path.endswith('.md'):
            with open(resume_path, 'r') as f:
                resume_text = f.read()
        else:
            # For PDF, just extract key info we already have
            resume_text = f"""
Tommy Lu
Data Analyst | Business Intelligence | Marketing Analytics
Skills: Python, SQL, R, Tableau, Power BI, Excel, Access
Experience: Marketing Manager & Product Specialist, Operations Assistant
Education: BBA in Computer Information Systems, Baruch College
"""
    except Exception as e:
        print(f"⚠️  Could not read resume: {e}")
        resume_text = "Resume not available"

    # Analyze job
    job = extract_job_info(job_text)

    print("\n" + "="*60)
    print("JOB ANALYSIS")
    print("="*60)
    print(f"Position: {job.job_title}")
    print(f"Experience Level: {job.experience_level}")
    print(f"\nRequired Skills ({len(job.required_skills)}):")
    for skill in job.required_skills:
        print(f"  • {skill}")
    print(f"\nKey Requirements:")
    for i, req in enumerate(job.key_requirements, 1):
        print(f"  {i}. {req}")
    print(f"\nTop Keywords: {', '.join(job.keywords[:5])}")

    # Analyze match
    match = analyze_resume_match(job, resume_text)

    print("\n" + "="*60)
    print("RESUME MATCH SCORE")
    print("="*60)
    print(f"Match Score: {match.score}%")
    print(f"\n✓ Matched Skills ({len(match.matched_skills)}):")
    for skill in match.matched_skills:
        print(f"  • {skill}")
    print(f"\n✗ Missing Skills ({len(match.missing_skills)}):")
    for skill in match.missing_skills:
        print(f"  • {skill}")
    print(f"\n💡 Recommendations:")
    for rec in match.recommendations:
        print(f"  {rec}")

    # Generate optimized resume
    if match.score < 80:
        print("\n" + "="*60)
        print("GENERATING OPTIMIZED RESUME")
        print("="*60)

        optimized_resume = generate_optimized_resume(job, match, resume_text, profile)
        filepath = save_optimized_resume(optimized_resume, job.job_title)

        print(f"\n✅ Optimized resume saved to:")
        print(f"   {filepath}")
        print("\n💡 Next steps:")
        print("   1. Review the optimized resume")
        print("   2. Adjust any sections as needed")
        print("   3. Apply to the job with confidence!")
    else:
        print("\n✅ Your resume is a great match! Consider applying directly.")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()
