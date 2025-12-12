import re

with open("PROJECT_CONTEXT.md", "r", encoding="utf-8") as f:
    content = f.read()

# Fix code blocks without language specification
# Find all ``` followed by newline, and add bash/powershell/etc based on context
lines = content.split("\n")
fixed_lines = []
i = 0

while i < len(lines):
    line = lines[i]

    # Check if this is a code block opening without language
    if line.strip().endswith("```") and not re.search(r"```\w+", line):
        # Check next few lines for context
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            # Determine language from content
            if (
                "bash" in next_line.lower()
                or "sh" in next_line.lower()
                or "ssh" in next_line.lower()
            ):
                line = line + "bash"
            elif "python" in next_line.lower() or "import" in next_line.lower():
                line = line + "python"
            elif any(x in next_line for x in ["powershell", "ps1", "Get-", "Set-"]):
                line = line + "powershell"
            elif any(x in next_line for x in ["json", "{"]):
                line = line + "json"
            elif any(x in next_line for x in [".py", ".sql"]):
                line = line + "python"

    fixed_lines.append(line)
    i += 1

with open("PROJECT_CONTEXT.md", "w", encoding="utf-8") as f:
    f.write("\n".join(fixed_lines))

print("✓ Fixed code block language specifications")
