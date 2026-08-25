# GitHub Terminal Commands

Run these commands only from the actual project folder.

```bash
cd ~/Downloads
unzip -o UrbanShadePlanningOptimizer_Local_GitHub_Complete.zip
cd ~/Downloads/UrbanShadePlanningOptimizer_Local_GitHub

pwd
test -f app.py || { echo "❌ app.py not found"; exit 1; }

rm -rf .git
git init
git branch -M main
git add -A

echo "=== FILES TO COMMIT ==="
git diff --cached --name-only

git commit -m "feat: add ShadePlan Local urban shade planning optimizer"

git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/shaunakmirajgaonkar/urban-shade-planning-optimizer.git

git remote -v
git push -u origin main
```

Do not run `git init` from `~` or directly from `~/Downloads`; initialize Git inside the project folder so unrelated Mac files are never staged.
