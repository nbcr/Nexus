import re

with open("PROJECT_CONTEXT.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for i, line in enumerate(lines):
    # Convert remaining h1 dates to h2 (fix h1 headings that weren't dates)
    if line.startswith("# 2025") and i > 0 and lines[i - 1].strip() != "":
        line = "## " + line[2:]

    # Remove trailing spaces
    line = line.rstrip() + "\n" if line.rstrip() else "\n"

    # Remove colons from ## subheadings (MD026)
    if line.startswith("## ") and line.rstrip().endswith(":"):
        line = line.rstrip()[:-1] + "\n"

    output.append(line)

with open("PROJECT_CONTEXT.md", "w", encoding="utf-8") as f:
    f.writelines(output)

print("✓ Fixed remaining h1 headings, colons, and trailing spaces")
