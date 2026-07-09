# Branch protection checklist (GitHub)

`gh` CLI was not available during release automation. Apply these settings in
GitHub → Settings → Branches → Branch protection rules for `master` (or `main`):

1. Require a pull request before merging
2. Require status checks to pass: **Lint · Typecheck · Smoke · Build** (`CI — RTAS Web`)
3. Require branches to be up to date before merging
4. Do not allow force pushes
5. Do not allow deletions
6. Restrict who can push (maintainers only)

After installing GitHub CLI:

```bash
winget install --id GitHub.cli -e
gh auth login
gh api repos/rtasdmcompany-hub/RTAS-Studio-AI/branches/master/protection \
  --method PUT \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["Lint · Typecheck · Smoke · Build"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

Repository: https://github.com/rtasdmcompany-hub/RTAS-Studio-AI
