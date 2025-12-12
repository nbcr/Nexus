import re
from pathlib import Path

versions_dir = Path("alembic/versions")
migrations = sorted(
    [f for f in versions_dir.glob("*.py") if f.name.startswith(tuple("0123456789"))]
)

for mig in migrations:
    content = mig.read_text()
    rev_match = re.search(r"revision\s*=\s*['\"]([^'\"]+)['\"]", content)
    down_match = re.search(r"down_revision\s*=\s*['\"]?([^'\")\n]+)", content)

    rev = rev_match.group(1) if rev_match else "?"
    down = down_match.group(1) if down_match else "?"
    down = down.strip().strip("'\"")

    print(f"{mig.name:40} R:{rev:4} <- D:{down}")
