import re

with open("PROJECT_CONTEXT.md", "r", encoding="utf-8") as f:
    content = f.read()

# Remove colons from ### headings too
content = re.sub(r"(### [^\n:]+):\n", r"\1\n", content)

# Remove trailing colons from ### headings
content = re.sub(r"(###.*?):\s*$", r"\1", content, flags=re.MULTILINE)

with open("PROJECT_CONTEXT.md", "w", encoding="utf-8") as f:
    f.write(content)

print("✓ Removed colons from subheadings")
