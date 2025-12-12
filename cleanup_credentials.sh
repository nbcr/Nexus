#!/bin/bash
# Script to remove sensitive files from git history

echo "Removing sensitive files from git history..."

# Remove private key files
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch nginx/certs/privkey.pem' \
  --prune-empty --tag-name-filter cat -- --all

# Remove any other certificate files
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch nginx/certs/*.pem nginx/certs/*.key nginx/certs/*.crt' \
  --prune-empty --tag-name-filter cat -- --all

# Remove files that had hardcoded credentials
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch make_yot_admin.py' \
  --prune-empty --tag-name-filter cat -- --all

echo "Cleaning up..."
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "Done! You should now force push to update the remote repository:"
echo "git push --force --all"
echo "git push --force --tags"