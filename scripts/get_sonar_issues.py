#!/usr/bin/env python3
"""
SonarQube Cloud Issues Fetcher
Retrieves code quality issues from SonarQube Cloud
"""

import requests
import json
import sys
from urllib.parse import quote

# SonarQube Cloud configuration
SONAR_TOKEN = "7446306b783cc3bde3f82cd32a87cd5899bf14d0"
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
    except:
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

def generate_markdown_report(project_key, all_issues, js_issues, feedrenderer_issues):
    """Generate markdown report of issues"""
    md_content = f"# SonarQube Issues Report\n\n"
    md_content += f"**Project:** {project_key}\n\n"
    md_content += f"**Total Issues:** {len(all_issues)}\n\n"
    md_content += f"**JavaScript Issues:** {len(js_issues)}\n\n"
    
    if feedrenderer_issues:
        md_content += f"## FeedRenderer.js Issues ({len(feedrenderer_issues)})\n\n"
        for issue in feedrenderer_issues:
            formatted = format_issue(issue)
            md_content += f"### Line {formatted['line']}: {formatted['severity']}\n\n"
            md_content += f"**Message:** {formatted['message']}\n\n"
            md_content += f"**Rule:** `{formatted['rule']}`\n\n"
            md_content += f"**Type:** {formatted['type']}\n\n"
            md_content += "---\n\n"
    
    if js_issues:
        md_content += f"## All JavaScript Issues ({len(js_issues)})\n\n"
        
        # Group by file
        files = {}
        for issue in js_issues:
            formatted = format_issue(issue)
            file_path = formatted['file']
            if file_path not in files:
                files[file_path] = []
            files[file_path].append(formatted)
        
        for file_path, file_issues in files.items():
            md_content += f"### {file_path} ({len(file_issues)} issues)\n\n"
            for issue in file_issues:
                md_content += f"- **Line {issue['line']}:** [{issue['severity']}] {issue['message']} (`{issue['rule']}`)\n"
            md_content += "\n"
    
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