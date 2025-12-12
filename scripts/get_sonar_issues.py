#!/usr/bin/env python3
"""
SonarQube Cloud Issues Fetcher
Retrieves code quality issues from SonarQube Cloud
"""

import requests
import json
import sys
import os
from urllib.parse import quote

# SonarQube Cloud configuration
SONAR_TOKEN = os.getenv("SONAR_TOKEN", "<sonar_token>")
SONAR_URL = "https://sonarcloud.io"

def get_project_key():
    """Return the known project key"""
    return "nbcr_Nexus"

def check_project_exists(project_key):
    """Check if project exists in SonarQube"""
    try:
        url = f"{SONAR_URL}/api/projects/search"
        response = requests.get(url, auth=(SONAR_TOKEN, ""), params={"q": project_key})
        if response.status_code == 200:
            data = response.json()
            return any(p["key"] == project_key for p in data.get("components", []))
    except requests.exceptions.RequestException as e:
        pass
    return False

def fetch_issues(project_key, component_filter=None):
    """Fetch issues from SonarQube Cloud"""
    url = f"{SONAR_URL}/api/issues/search"
    
    params = {
        "componentKeys": project_key,
        "resolved": "false",
        "ps": 500,  # page size
        "facets": "severities,types"
    }
    
    if component_filter:
        params["components"] = f"{project_key}:{component_filter}"
    
    try:
        response = requests.get(url, auth=(SONAR_TOKEN, ""), params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching issues: {e}")
        return None

def filter_js_issues(issues_data, file_path=None):
    """Filter issues for JavaScript files, optionally for specific file"""
    if not issues_data or "issues" not in issues_data:
        return []
    
    filtered_issues = []
    for issue in issues_data["issues"]:
        component = issue.get("component", "")
        
        # Filter for JS files
        if not component.endswith(('.js', '.jsx', '.ts', '.tsx')):
            continue
            
        # Filter for specific file if provided
        if file_path and file_path not in component:
            continue
            
        filtered_issues.append(issue)
    
    return sorted(filtered_issues, key=lambda x: (x.get('component', ''), x.get('line', 0)))

def format_issue(issue):
    """Format issue for display"""
    component = issue.get("component", "").split(":")[-1]  # Get file path
    line = issue.get("line", "N/A")
    severity = issue.get("severity", "UNKNOWN")
    type_name = issue.get("type", "UNKNOWN")
    rule = issue.get("rule", "")
    message = issue.get("message", "")
    
    return {
        "file": component,
        "line": line,
        "severity": severity,
        "type": type_name,
        "rule": rule,
        "message": message
    }

def group_issues_by_severity(all_issues):
    """Group issues by severity level"""
    severity_groups = {"CRITICAL": [], "BLOCKER": [], "MAJOR": [], "MINOR": [], "INFO": []}
    for issue in all_issues:
        formatted = format_issue(issue)
        severity = formatted['severity']
        if severity in severity_groups:
            severity_groups[severity].append(formatted)
    return severity_groups

def generate_severity_section(severity, issues, severity_icons):
    """Generate markdown for a single severity section"""
    if not issues:
        return ""
    
    icon = severity_icons[severity]
    content = f"### {icon} {severity} Issues ({len(issues)})\n\n"
    
    # Group by file within severity
    files = {}
    for issue in issues:
        file_path = issue['file']
        if file_path not in files:
            files[file_path] = []
        files[file_path].append(issue)
    
    for file_path, file_issues in sorted(files.items()):
        content += f"#### {file_path}\n"
        for issue in file_issues:
            content += f"- **Line {issue['line']}:** {issue['message']} (`{issue['rule']}`)\n"
        content += "\n"
    
    content += "---\n\n"
    return content

def generate_summary_section(severity_groups):
    """Generate summary section"""
    content = "## Summary by Priority\n\n"
    severity_icons = {"CRITICAL": "🔴", "BLOCKER": "🟠", "MAJOR": "🟡", "MINOR": "🔵", "INFO": "⚪"}
    priority_text = {
        "CRITICAL": "Address immediately: Complex functions need refactoring",
        "BLOCKER": "Fix next: Missing variable declarations", 
        "MAJOR": "Schedule soon: Code quality improvements",
        "MINOR": "Address gradually: Style and best practice improvements",
        "INFO": "Optional: Informational suggestions"
    }
    
    for severity in ["CRITICAL", "BLOCKER", "MAJOR", "MINOR", "INFO"]:
        count = len(severity_groups[severity])
        if count > 0:
            icon = severity_icons[severity]
            content += f"**{icon} {severity} ({count} issues)** - {priority_text[severity]}\n"
    
    return content

def generate_markdown_report(project_key, all_issues, js_issues, feedrenderer_issues):
    """Generate markdown report of all issues organized by severity"""
    md_content = f"# SonarQube Issues Report\n\n"
    md_content += f"**Project:** {project_key}\n\n"
    md_content += f"**Total Issues:** {len(all_issues)}\n\n"
    md_content += f"**JavaScript Issues:** {len(js_issues)}\n\n"
    
    if not all_issues:
        return md_content
    
    severity_groups = group_issues_by_severity(all_issues)
    severity_icons = {"CRITICAL": "🔴", "BLOCKER": "🟠", "MAJOR": "🟡", "MINOR": "🔵", "INFO": "⚪"}
    
    md_content += "## Issues by Severity\n\n"
    
    for severity in ["CRITICAL", "BLOCKER", "MAJOR", "MINOR", "INFO"]:
        md_content += generate_severity_section(severity, severity_groups[severity], severity_icons)
    
    md_content += generate_summary_section(severity_groups)
    md_content += f"\n## All Issues ({len(all_issues)})\n\n"
    
    if js_issues:
        md_content += f"### JavaScript Issues ({len(js_issues)})\n\n"
    
    return md_content

def main():
    print("SonarQube Cloud Issues Fetcher")
    print("=" * 40)
    
    # Get project key
    project_key = get_project_key()
    if not project_key:
        print("No project key provided. Exiting.")
        sys.exit(1)
    
    print(f"Fetching issues for project: {project_key}")
    
    # Fetch all issues
    issues_data = fetch_issues(project_key)
    if not issues_data:
        print("Failed to fetch issues.")
        sys.exit(1)
    
    all_issues = issues_data.get('issues', [])
    feedrenderer_issues = filter_js_issues(issues_data, "FeedRenderer.js")
    all_js_issues = filter_js_issues(issues_data)
    
    print(f"\nTotal issues found: {len(all_issues)}")
    print(f"JavaScript issues: {len(all_js_issues)}")
    print(f"FeedRenderer.js issues: {len(feedrenderer_issues)}")
    
    # Generate and save markdown report
    markdown_content = generate_markdown_report(project_key, all_issues, all_js_issues, feedrenderer_issues)
    with open("issues.md", 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    # Save JSON data
    with open("sonar_issues.json", 'w') as f:
        json.dump({
            "project_key": project_key,
            "total_issues": len(all_issues),
            "js_issues": [format_issue(issue) for issue in all_js_issues],
            "feedrenderer_issues": [format_issue(issue) for issue in feedrenderer_issues],
            "raw_data": issues_data
        }, f, indent=2)
    
    print(f"\nMarkdown report saved to: issues.md")
    print(f"JSON data saved to: sonar_issues.json")

if __name__ == "__main__":
    main()