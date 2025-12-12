@echo off
REM Script to remove sensitive files from git history (Windows)

echo Removing sensitive files from git history...

REM Remove private key files
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch nginx/certs/privkey.pem" --prune-empty --tag-name-filter cat -- --all

REM Remove any other certificate files  
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch nginx/certs/*.pem nginx/certs/*.key nginx/certs/*.crt" --prune-empty --tag-name-filter cat -- --all

echo Cleaning up...
rmdir /s /q .git\refs\original\
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo Done! You should now force push to update the remote repository:
echo git push --force --all
echo git push --force --tags