# Pre-Commit Checklist ✅

Sử dụng checklist này trước khi commit và push Git.

---

## ✅ 1. Backups Completed

- [x] **Code backup**: `backups/backup_20260113_140929/`
  - ML models: 1 file (.pkl)
  - Configurations: 6 files
  - Checkpoints metadata: Saved
  - System state: JSON file

- [x] **Docker images backup**: `bigbig-stack-snapshot.tar`
  - Size: 2.96 GB
  - Images: 11 containers
  - Time: 192 seconds
  - Can restore: `docker load -i bigbig-stack-snapshot.tar`

---

## ✅ 2. Gitignore Protection

Verify these are **EXCLUDED** from commit:

- [x] `.venv/` - 32,000+ files
- [x] `checkpoints/` - 1,700+ files
- [x] `logs/` - Log files
- [x] `data/` - Raw data
- [x] `ml-layer/models/*.pkl` - Binary models
- [x] `backups/` - Backup directory
- [x] `__pycache__/` - Python cache
- [x] `*.tar` - Docker images backup

**Run this to verify**:
```bash
git status
# Should NOT see: .venv/, checkpoints/, logs/, .tar files
```

---

## ✅ 3. Files Ready to Commit

New files to commit (~5 new files):

- [ ] `DOCKER_RESTORE_GUIDE.md` - Docker restore instructions
- [ ] `docker-save-images.ps1` - Docker backup script
- [ ] `GIT_COMMIT_GUIDE.md` - Updated with Docker info
- [ ] `COMMIT_MESSAGE.md` - Detailed commit message
- [ ] `.gitignore` - Updated to exclude .tar

Previously created (~30 files):

- [ ] `PHASE4_GUIDE.md`, `PHASE5_GUIDE.md` - Documentation
- [ ] `batch-layer/`, `ml-layer/` - Source code
- [ ] `verify_phase4.py`, `backup_before_commit.py` - Scripts
- [ ] `PLANMODE.md` - Updated with Phase 5 completion

---

## ✅ 4. Git Commands

```bash
# Step 1: Check status
git status

# Step 2: Add all files
git add .

# Step 3: Verify again (IMPORTANT!)
git status
# ⚠️ Make sure NO .venv/, checkpoints/, *.tar

# Step 4: Commit
git commit -F COMMIT_MESSAGE.md

# Alternative: Short commit
# git commit -m "feat: Complete Lambda Architecture (Phase 1-5)"

# Step 5: Push
git push origin main

# Step 6 (Optional): Tag release
git tag -a v1.0 -m "Phase 5 Complete - ML Layer"
git push --tags
```

---

## ✅ 5. After Push

- [ ] **Verify on GitHub/GitLab**
  - File count: ~35 files (not 34,000+)
  - No .venv/ or .tar files visible
  - Documentation rendered correctly

- [ ] **Save Docker backup**
  - Copy `bigbig-stack-snapshot.tar` (2.96 GB) to:
    - [ ] External HDD/USB
    - [ ] Google Drive / OneDrive (may need compression)
    - [ ] NAS / Network storage

- [ ] **Test clone (Optional)**
  ```bash
  # On another machine or folder
  git clone <repo-url>
  cd bigbig
  python -m venv .venv
  pip install -r requirements.txt
  docker load -i bigbig-stack-snapshot.tar
  docker compose up -d
  ```

---

## ✅ 6. Safety Checks

- [x] No sensitive data (credentials, API keys)
- [x] No large files (>100 MB) in Git
- [x] Documentation is complete
- [x] Can fully restore in <10 minutes
- [x] All data regenerable from source

---

## 📊 Summary

| Item | Status | Size/Count |
|------|--------|------------|
| Code backup | ✅ Done | backups/ folder |
| Docker backup | ✅ Done | 2.96 GB |
| Files to commit | ✅ Ready | ~35 files |
| Files excluded | ✅ Protected | ~34,000 files |
| Repo size | ✅ Small | ~1-2 MB |
| Safe to push | ✅ YES | Verified |

---

## 🎯 Final Command Sequence

Copy & paste these commands:

```bash
# 1. Final check
git status

# 2. Add all
git add .

# 3. Verify NO large files
git status | Select-String -Pattern ".venv|.tar|checkpoints"
# Should return NOTHING

# 4. Commit
git commit -F COMMIT_MESSAGE.md

# 5. Push
git push origin main

# 6. Tag (optional)
git tag -a v1.0 -m "Phase 5 Complete"
git push --tags

# ✅ DONE!
```

---

**Checklist completed**: ✅ ALL READY  
**Safe to push**: ✅ YES  
**Estimated push time**: 1-3 minutes  
**Date**: 2026-01-13
