#!/usr/bin/env python3
"""
Convert markdown resumes to styled PDFs using WeasyPrint
"""

import os
from pathlib import Path
import weasyprint

def markdown_to_simple_html(markdown_text, title):
    """Convert markdown to simple HTML for PDF generation"""
    lines = markdown_text.split('\n')
    html_lines = []
    html_lines.append(f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>')
    html_lines.append('<style>')
    html_lines.append('''
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            line-height: 1.4;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 40px;
        }
        h1 {
            font-size: 24px;
            margin-bottom: 5px;
            color: #000;
        }
        h2 {
            font-size: 14px;
            text-transform: uppercase;
            color: #666;
            border-bottom: 1px solid #ddd;
            margin-top: 20px;
            padding-bottom: 5px;
        }
        h3 {
            font-size: 14px;
            font-weight: 600;
            margin-top: 15px;
            margin-bottom: 5px;
            color: #000;
        }
        h4 {
            font-size: 12px;
            font-weight: 600;
            color: #555;
        }
        p {
            margin: 5px 0;
            font-size: 11px;
        }
        ul {
            margin: 5px 0 5px 20px;
            padding: 0;
        }
        li {
            font-size: 11px;
            margin: 3px 0;
        }
        strong {
            color: #000;
        }
        hr {
            border: none;
            border-top: 1px solid #ddd;
            margin: 15px 0;
        }
        .header-line {
            font-size: 11px;
            color: #555;
            margin-bottom: 20px;
        }
        .section {
            margin-bottom: 15px;
        }
    ''')
    html_lines.append('</style></head><body>')

    i = 0
    while i < len(lines):
        line = lines[i]

        # Headers
        if line.startswith('# '):
            text = line[2:].strip()
            html_lines.append(f'<h1>{text}</h1>')
        elif line.startswith('## '):
            text = line[2:].strip()
            html_lines.append(f'<h2>{text}</h2>')
        elif line.startswith('### '):
            text = line[4:].strip()
            html_lines.append(f'<h3>{text}</h3>')
        elif line.startswith('#### '):
            text = line[5:].strip()
            html_lines.append(f'<h4>{text}</h4>')

        # Header contact line
        elif '**' in line and '**' in line and '|' in line:
            # Replace markdown bold with HTML strong
            line = line.replace('**', '<strong>').replace('</strong>', '<strong>')
            # Split by | and format
            parts = line.split('|')
            parts = [p.strip().replace('<strong>', '').replace('</strong>', '') for p in parts]
            contact_parts = []
            for part in parts:
                if part:
                    if '@' in part or 'linkedin.com' in part or '917' in part:
                        contact_parts.append(part)
            if contact_parts:
                html_lines.append(f'<p class="header-line">{" | ".join(contact_parts)}</p>')

        # Horizontal rule
        elif line.strip() == '---':
            html_lines.append('<hr>')

        # Bullet points
        elif line.strip().startswith('- '):
            text = line[2:].replace('**', '<strong>').replace('**', '</strong>')
            html_lines.append(f'<li>{text}</li>')

        # Blank lines - skip
        elif not line.strip():
            pass

        # Regular text/paragraphs
        elif line.strip():
            text = line.replace('**', '<strong>').replace('**', '</strong>')
            html_lines.append(f'<p>{text}</p>')

        i += 1

    html_lines.append('</body></html>')
    return '\n'.join(html_lines)

def convert_resume(md_path, pdf_path):
    """Convert a single markdown resume to PDF"""
    print(f"Converting {md_path}...")

    with open(md_path, 'r') as f:
        markdown_content = f.read()

    title = md_path.stem.replace('_', ' ').replace('-', ' ')
    html_content = markdown_to_simple_html(markdown_content, title)

    # Convert to PDF
    weasyprint.HTML(string=html_content).write_pdf(pdf_path)
    print(f"✅ Saved to {pdf_path}")

def main():
    """Convert all resumes"""
    resume_dir = Path("/Users/tommylu/clawd/resumes")

    # Find markdown resumes
    md_files = list(resume_dir.glob("*.md"))

    if not md_files:
        print("No markdown resumes found")
        return

    print(f"Found {len(md_files)} resume(s) to convert\n")

    for md_file in md_files:
        if "FINAL" in md_file.name or "final" in md_file.name:
            pdf_file = md_file.with_suffix('.pdf')
            convert_resume(md_file, pdf_file)

    print(f"\n✅ Done! PDFs saved to {resume_dir}")

if __name__ == "__main__":
    main()
