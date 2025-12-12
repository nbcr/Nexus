import re

with open("PROJECT_CONTEXT.md", "r", encoding="utf-8") as f:
    content = f.read()

# Fix blank lines before and after headings
content = re.sub(r"([^\n])\n(## )", r"\1\n\n\2", content)
content = re.sub(r"(## [^\n]+)\n([^\n\-])", r"\1\n\n\2", content)

# Fix blank lines around lists
content = re.sub(r"([^\n])\n(- )", r"\1\n\n\2", content)
content = re.sub(r"(- [^\n]+)\n([^\-\n])", r"\1\n\n\2", content)

# Fix code blocks
content = re.sub(r"([^\n])\n(```)", r"\1\n\n\2", content)
content = re.sub(r"(```[^\n]*)\n([^`])", r"\1\n\n\2", content)

with open("PROJECT_CONTEXT.md", "w", encoding="utf-8") as f:
    f.write(content)

print("✓ Fixed markdown blank lines")
