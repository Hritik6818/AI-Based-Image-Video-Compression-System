# GitHub: first repo + init

Local git init is done by `scripts/init_repo.ps1`. I cannot create github.com repos without your login — do:

```powershell
.\scripts\init_repo.ps1
# create empty repo on github.com/new (no README), then:
git remote add origin https://github.com/<you>/ai-compression.git
git branch -M main
git push -u origin main
```
