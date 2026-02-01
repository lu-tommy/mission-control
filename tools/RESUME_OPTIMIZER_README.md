# Resume Optimizer Tool

Optimize your resume based on job descriptions to improve match scores and get more interviews.

## Features

- **Job Analysis**: Extracts key skills, requirements, and keywords from job descriptions
- **Match Scoring**: Calculates how well your resume matches the job (0-100%)
- **Missing Skills**: Identifies skills you should highlight or add
- **Optimized Resume**: Generates a tailored version of your resume for each job
- **Smart Recommendations**: Actionable tips to improve your chances

## Quick Start

### Option 1: Run directly
```bash
python3 /Users/tommylu/clawd/tools/resume-optimizer.py
```

### Option 2: Copy job description, then run
```bash
# Copy job description to clipboard, then:
pbpaste | python3 /Users/tommylu/clawd/tools/resume-optimizer.py
```

### Option 3: Interactive mode
```bash
python3 /Users/tommylu/clawd/tools/resume-optimizer.py
# Paste job description, press Ctrl+D
```

## How It Works

1. **Analyze Job**: Extracts:
   - Required technical skills (Python, SQL, Tableau, etc.)
   - Preferred/bonus skills
   - Experience level required
   - Key requirements and duties
   - Important keywords and phrases

2. **Match Analysis**: Compares your resume to job:
   - Calculates match score (0-100%)
   - Identifies matched skills
   - Finds missing skills to add
   - Generates recommendations

3. **Optimize Resume**: Creates tailored version:
   - Customizes summary for the specific role
   - Reorders skills based on job requirements
   - Highlights relevant experience
   - Emphasizes projects that match the job

## Example Usage

### Job Description Example
```
Data Analyst - Remote
Company: TechCorp Inc.

Requirements:
- Python and SQL experience required
- Experience with Tableau or Power BI
- Strong analytical and problem-solving skills
- 2+ years of data analysis experience
- Experience with ETL processes and data pipelines

Preferred:
- Knowledge of cloud platforms (AWS, Azure, GCP)
- Experience with machine learning or AI
- Excellent communication skills
```

### Output
```
📄 RESUME OPTIMIZER TOOL
============================================================

🔍 Analyzing job description...

============================================================
JOB ANALYSIS
============================================================
Position: Data Analyst - Remote
Experience Level: Mid-level

Required Skills (8):
  • Python
  • SQL
  • Tableau
  • Power Bi
  • Data Analysis
  • Etl
  • Data Pipeline

Key Requirements:
  1. Python and SQL experience required
  2. Experience with Tableau or Power BI
  3. Strong analytical and problem-solving skills
  4. 2+ years of data analysis experience
  5. Experience with ETL processes and data pipelines

Top Keywords: Data, Analyst, Experience, Required, Skills

📊 Analyzing resume match...

============================================================
RESUME MATCH SCORE
============================================================
Match Score: 72.7%

✓ Matched Skills (8):
  • Python
  • SQL
  • Tableau
  • Power Bi
  • Data Analysis
  • Etl
  • Data Pipeline

✗ Missing Skills (0):

💡 Recommendations:
  💡 Emphasize experience relevant to Mid-level roles
  ✨ Tailor your summary/objective to match this job title

============================================================
GENERATING OPTIMIZED RESUME
============================================================

✅ Optimized resume saved to:
   /Users/tommylu/Optimized_Resume_Data_Analyst_-_Remote.txt

💡 Next steps:
   1. Review optimized resume
   2. Adjust any sections as needed
   3. Apply to job with confidence!
```

## Tips for Best Results

1. **Be Specific**: Include the full job description for better analysis
2. **Check Keywords**: Look at the "Top Keywords" to understand what's important
3. **Highlight Projects**: Ensure your best projects match the job requirements
4. **Customize Summary**: The optimized summary is tailored - review and adjust
5. **Proofread**: Always review the optimized resume before applying

## Advanced Features

### Match Score Interpretation
- **80%+**: Great match - Apply directly
- **60-79%**: Good match - Consider highlighting missing skills
- **40-59%**: Fair match - Add missing skills to resume or reconsider
- **<40%**: Poor match - Job might not be a good fit

### Automatic Skill Extraction
The tool automatically recognizes:
- Programming languages (Python, SQL, R, JavaScript, etc.)
- Data tools (Tableau, Power BI, Excel, SAS, etc.)
- Cloud platforms (AWS, Azure, GCP, etc.)
- Frameworks (React, Django, Flask, etc.)
- Methodologies (Agile, Scrum, DevOps, etc.)

### Customization Options

Edit `~/job_profile.json` to customize:
- Personal information
- Work authorization
- Experience details
- Education
- Skills and certifications

## Integration with Job Search

Use this tool alongside job searching:

1. Find a job you're interested in
2. Copy the job description
3. Run: `pbpaste | python3 /Users/tommylu/clawd/tools/resume-optimizer.py`
4. Review the optimized resume
5. Apply with confidence!

## Troubleshooting

**"Could not read resume"**: 
- Make sure your resume path is set in `~/job_profile.json`
- Or provide a .txt version of your resume

**Low match score (<60%)**:
- Consider if this job is a good fit
- Look at "Missing Skills" section
- Update your resume with relevant skills

**Optimized resume doesn't look right**:
- The tool uses your profile data - update `~/job_profile.json`
- Manually edit the generated .txt file
- Consider using the suggestions as a guide for manual optimization

## Future Enhancements

- [ ] AI-powered keyword extraction
- [ ] Multiple resume versions
- [ ] Cover letter generation
- [ ] Integration with job search platforms
- [ ] Historical match tracking
