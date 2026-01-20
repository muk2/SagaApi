# Ralph Loop - Autonomous Development

Run Ralph Loop to autonomously develop code, create PRs, review them, and iterate until complete.

## TL;DR

```bash
claude
/ralph-loop Follow the task at ralph-tasks/PROMPT.md
```

Ralph does everything. You just review and merge the final PR.

## One-Time Setup (2 minutes)

```bash
# 1. Login to Claude (if not already)
claude login

# 2. Configure git
git config --global user.email "you@example.com"
git config --global user.name "Your Name"

# 3. Login to GitHub
gh auth login

# 4. Start dev container
cd /Users/malchal/SagaApi
docker compose -f .devcontainer/docker-compose.yml up -d
```

Done! ✅

## Usage

### Option 1: Use Task File

```bash
# Edit task
vim ralph-tasks/PROMPT.md

# Run Ralph
claude
/ralph-loop Follow the task at ralph-tasks/PROMPT.md
```

### Option 2: Inline Task

```bash
claude
/ralph-loop Add comprehensive test coverage for auth endpoints.
Requirements:
- All endpoints tested
- Coverage >= 80%
- Include edge cases
Create PR and self-review when done.
```

## What Ralph Does

1. **Develops** - Creates branch, writes code, runs tests, commits
2. **Creates PR** - Pushes branch and creates draft PR
3. **Self-Reviews** - Reviews code, adds critical comments
4. **Iterates** - Fixes issues from review, commits, pushes
5. **Finalizes** - Marks PR ready when truly complete

You review the final PR and merge.

## Monitoring

```bash
# See Ralph's work
git branch | grep ralph
git log --oneline ralph/<branch-name>
gh pr list
```

## Review PR

```bash
gh pr view <number>
gh pr diff <number>
gh pr merge <number> --squash
```

## Files

- **`START-HERE.md`** - Full setup guide
- **`ralph-tasks/PROMPT.md`** - Example task template
- **`ralph-tasks/SIMPLE-USAGE.md`** - Complete usage guide
- **`.claude/RALPH-WORKFLOW.md`** - Ralph's internal workflow

## Key Points

✅ **No API keys needed** - Uses `claude login`
✅ **No scripts** - Just `/ralph-loop`
✅ **Self-reviewing** - Ralph critiques its own code
✅ **Fully autonomous** - Works while you sleep
✅ **Safe** - Separate branch, draft PR, you approve merge

---

**Start now:**

```bash
claude
/ralph-loop Follow the task at ralph-tasks/PROMPT.md
```
