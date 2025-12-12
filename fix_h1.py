with open("PROJECT_CONTEXT.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []
for line in lines:
    # Convert ALL h1 headings to h2 (except first main one)
    if line.startswith("# ") and not line.startswith("# Nexus Project Context"):
        line = "## " + line[2:]
    output.append(line)

with open("PROJECT_CONTEXT.md", "w", encoding="utf-8") as f:
    f.writelines(output)

print("✓ Converted all h1 headings to h2")
