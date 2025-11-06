# Development Guide

## Branch Strategy

- `main` - Production-ready code
- `development` - Active development branch
- `feature/*` - Feature branches
- `hotfix/*` - Emergency production fixes

## Workflow

1. **Start a new feature**:
   ```bash
   git checkout development
   git pull origin development
   git checkout -b feature/your-feature-name
Make changes and commit:

bash
git add .
git commit -m "feat: add your feature description"
Push and create PR:

bash
git push origin feature/your-feature-name
# Create Pull Request to development branch
After PR merge:

bash
git checkout development
git pull origin development
git branch -d feature/your-feature-name
Commit Message Convention
feat: - New feature

fix: - Bug fix

docs: - Documentation changes

style: - Code style changes (formatting, etc.)

refactor: - Code refactoring

test: - Adding tests

chore: - Maintenance tasks

Code Standards
Use Black for Python code formatting

Follow FastAPI best practices

Write docstrings for all functions

Include type hints

Test API endpoints
