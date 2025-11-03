## 🧩 Project Setup Guide

This repository contains both the **frontend** and **backend** of the Tadabbur project.

## Backend:

```bash
cd backend
uv sync
```
## Frontend:

```bash
cd frontend
npm install
```


# 🚀 Collaboration & Branching Guide

This repository uses **branch protection rules** to keep the `main` branch stable and production-ready.  
No one can **push directly to `main`** — all changes must go through Pull Requests (PRs).

---

## 🔒 Branch Protection Rules

The following rules are applied to the `main` branch:

- ✅ **Require Pull Request before merging**  
- ✅ **Require at least 1 approval** before merging  
- ✅ **Dismiss stale approvals when new commits are pushed**  
- ✅ **Require approval of the most recent reviewable push**  
- ✅ **Require all conversations to be resolved before merging**  
- ✅ **Require linear history (no merge commits)**  
- ✅ **No bypassing rules — applies to admins as well**  
- ❌ **No force pushes**  
- ❌ **No direct commits or deletions**  

---

## 🌿 Standard Git Workflow

Follow this process to safely contribute:

### 1. Pull the latest changes
```bash
git checkout main
git pull origin main
```
2. Create a new branch
Always create a new branch for your work (use descriptive names):

```bash
git checkout -b feature/add-login-form
```
or
```bash
git checkout -b fix/typo-in-readme
```
3. Make and commit your changes
```bash
git add .
git commit -m "Add login form functionality"
```
4. Push your branch to GitHub
```bash
git push origin feature/add-login-form
```
5. Open a Pull Request (PR)
Go to your repository on GitHub.

You’ll see a prompt to “Compare & pull request.”

Click it, describe your changes, and submit the PR to main.

6. Request Review
Tag another collaborator for review.

Wait for approval and address any comments.

7. Merge via Pull Request
Once approved and all conversations are resolved:

Use the “Squash and Merge” or “Rebase and Merge” option (to maintain a linear history).

The PR will then merge into main.

💡 Best Practices
Pull latest changes from main before creating a new branch.

Keep branch names short and clear (e.g., voice-feature/, fix/, tafseer-agent/).

Commit frequently with meaningful messages.

Never push directly to main.

Resolve all comments before merging.

👥 Approvals
Each PR requires 1 approval before it can be merged.
If new commits are pushed after approval, the previous approval will be dismissed and needs to be re-reviewed.

🧹 Clean-Up
After your PR is merged:

```bash
git checkout main
git pull origin main
git branch -d feature/add-login-form
```
Keeps your local repo tidy.











