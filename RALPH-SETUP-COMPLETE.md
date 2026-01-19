# ✅ Ralph Loop Setup Complete

Your autonomous development workflow is ready! No complex scripts needed - just run Claude CLI and use the Ralph Loop plugin.

## What's Been Built

A **simple, powerful workflow** where you:
1. Open Claude CLI
2. Run `/ralph-loop` with your task
3. Ralph autonomously develops, commits, creates PR, reviews it, iterates, and finalizes
4. You review and merge the final PR

**No tmux. No scripts. Just Ralph Loop doing everything.**

## Architecture

```
┌─────────────────────────────────────────────────┐
│ Your Mac (Host)                                 │
│                                                 │
│  You: claude (already logged in)               │
│       /ralph-loop <task>                        │
│                                                 │
│  Ralph Loop (autonomous):                      │
│  ├─ Works in dev container (docker exec)       │
│  ├─ Makes code changes                         │
│  ├─ Runs tests                                 │
│  ├─ Commits incrementally                      │
│  ├─ Creates PR                                 │
│  ├─ Reviews own PR                             │
│  ├─ Iterates on feedback                       │
│  └─ Marks PR ready                             │
│                                                 │
│  You: Review PR and merge                      │
└─────────────────────────────────────────────────┘
```

## Files Created

### Configuration
- **`.claude/settings.json`** - Ralph Loop plugin enabled
- **`.claude/RALPH-WORKFLOW.md`** - Workflow instructions for Ralph
- **`.claude/CONTEXT.md`** - Project context and command patterns

### Documentation
- **`START-HERE.md`** - Quick setup guide (start here!)
- **`ralph-tasks/README.md`** - Task directory overview
- **`ralph-tasks/SIMPLE-USAGE.md`** - Complete usage guide
- **`ralph-tasks/PROMPT.md`** - Example task template

### Project Files (Already Had)
- **`.devcontainer/`** - Dev container configuration
- **`ralph.toml`** - Ralph orchestrator config (alternative tool, not used)

## How It Works

### 1. You Start Ralph
```bash
cd /Users/malchal/SagaApi
claude
/ralph-loop Add comprehensive auth test coverage. Create PR and self-review.
```

### 2. Ralph Works Autonomously

**Development Phase:**
- Creates branch `ralph/add-auth-tests`
- Reads existing code
- Implements tests incrementally
- Runs tests in container: `docker exec ... pytest`
- Commits: `[ralph] Add login endpoint tests`
- Continues until implementation complete

**PR Creation Phase:**
- Pushes branch: `git push -u origin ralph/add-auth-tests`
- Creates draft PR: `gh pr create --draft`

**Self-Review Phase:**
- Gets PR diff: `gh pr diff 123`
- Reviews critically
- Adds comments: `gh pr review 123 --comment`
  - "Missing edge case for expired tokens"
  - "Need better error handling in logout"
  - "Test coverage gap in refresh endpoint"

**Iteration Phase:**
- Addresses each comment
- Makes improvements
- Commits: `[ralph] Address review: Add token expiration tests`
- Pushes: `git push`
- Re-reviews to verify fixes
- Repeats until satisfied

**Finalization Phase:**
- Marks PR ready: `gh pr ready 123`
- Adds final summary
- Stops iterating

### 3. You Review and Merge

```bash
gh pr view 123
gh pr diff 123
gh pr merge 123 --squash
```

## Setup Required (One-Time, 2 Minutes)

### 1. Claude CLI Login
```bash
# Login to Claude.ai (uses your Pro/Max subscription)
claude login

# No API key needed!
```

### 2. Git Config
```bash
git config --global user.email "you@example.com"
git config --global user.name "Your Name"
```

### 3. GitHub CLI
```bash
brew install gh
gh auth login
```

### 4. Start Dev Container
```bash
cd /Users/malchal/SagaApi
docker compose -f .devcontainer/docker-compose.yml up -d
```

Done! ✅

## Usage

### Simple Task
```bash
claude
/ralph-loop Add logging to all API endpoints. Create PR and self-review.
```

### Task from File
```bash
# Edit task file
vim ralph-tasks/PROMPT.md

# Run Ralph
claude
/ralph-loop Follow the task at ralph-tasks/PROMPT.md
```

### Complex Task with Details
```bash
claude
/ralph-loop Add comprehensive test coverage for authentication.

Requirements:
- All auth endpoints tested
- Coverage >= 80%
- Include edge cases (invalid tokens, expired sessions)
- Use pytest and pytest-asyncio

Constraints:
- Do NOT modify existing auth logic
- Follow existing test patterns

Workflow:
1. Create branch ralph/add-auth-tests
2. Implement tests incrementally
3. Create PR and self-review
4. Iterate until ready
```

## Key Features

### ✅ Fully Autonomous
- Ralph works without your intervention
- No prompts, no approvals (yolo mode)
- You just review final PR

### ✅ Self-Critical Review
- Ralph reviews its own code
- Identifies gaps and issues
- Iterates to fix them
- Only marks ready when truly complete

### ✅ Secure
- Uses Claude.ai login (no API keys to manage)
- Works on separate branch (never touches main)
- PR review gate (you control merges)

### ✅ Quality Focused
- Runs tests after every change
- Ensures linting passes
- Verifies coverage
- Makes atomic commits

## What Ralph Knows

Ralph has context from:
- **`.claude/RALPH-WORKFLOW.md`** - Full workflow instructions
- **`.claude/CONTEXT.md`** - Project structure, commands, conventions
- **`.claude/CLAUDE.md`** - Senior architect mindset
- **Your task description** - Specific requirements

Ralph understands:
- Run `pytest`, `ruff` in container via `docker exec`
- Run `git`, `gh` on host normally
- Create branch → develop → commit → PR → review → iterate → finalize
- Be critical in self-review
- Follow acceptance criteria strictly

## Monitoring Progress

While Ralph works (optional):

```bash
# See Ralph's branch
git branch | grep ralph

# See commits Ralph made
git log --oneline ralph/<branch-name>

# Check PR status
gh pr list

# View container activity
docker logs sagaapi-devcontainer-app-1 --tail 50
```

## Example Session

```
$ cd /Users/malchal/SagaApi
$ claude

Claude Code CLI v1.x.x

Claude: Hi! I'm Claude Code. How can I help?

You: /ralph-loop Add comprehensive test coverage for authentication endpoints.
     Requirements:
     - All auth endpoints have tests
     - Coverage >= 80%
     - Include edge cases
     - Create PR and self-review when done

Claude: I'll help you add comprehensive test coverage for authentication.
        Let me start by exploring the existing code...

[30-60 minutes later]

Claude: I've completed the implementation and created PR #42.

        Summary:
        - Created branch: ralph/add-auth-test-coverage
        - Added 18 tests covering all auth endpoints
        - Achieved 87% coverage for auth modules
        - Included edge cases for token expiration, invalid credentials, etc.
        - Self-reviewed and addressed all feedback:
          ✓ Added missing logout endpoint tests
          ✓ Improved error handling in token refresh tests
          ✓ Added fixtures for test data
        - All 156 tests passing
        - No linting errors
        - PR #42 marked as ready

        Ready for your review!

You: [Reviews PR, merges if satisfied]
```

## Task Template

See `ralph-tasks/PROMPT.md` for a complete template. Key sections:

```markdown
## Task Objective
Clear goal statement

## Acceptance Criteria
- [ ] Specific, measurable requirements
- [ ] PR created and self-reviewed

## Constraints
- What NOT to change

## Implementation Workflow
Phase-by-phase instructions for Ralph

## Quality Standards
What makes the PR ready

## Technical Context
Environment details, commands
```

## Safety & Control

✅ **Ralph works on separate branch** - Never touches `main`
✅ **Draft PR first** - Signals it's under development
✅ **Self-review required** - Ralph must critically review before finalizing
✅ **You approve merges** - Final quality gate
✅ **Container isolation** - Can't harm host system
✅ **No API keys to manage** - Uses your Claude.ai login
✅ **Git history** - Every change tracked, easy rollback

## Differences from Original Plan

| Original (Tmux-based) | New (Ralph Loop) |
|----------------------|------------------|
| Complex tmux orchestration | Simple: `claude` + `/ralph-loop` |
| Manual PR creation script | Ralph creates PR automatically |
| No self-review | Ralph reviews and iterates |
| Watch in tmux panes | Just check final PR |
| Multiple scripts | No scripts needed |

**Simpler and more powerful!**

## Next Steps

1. **Read**: `START-HERE.md` for quick setup
2. **Setup**: Complete the 5-minute setup above
3. **Edit**: `ralph-tasks/PROMPT.md` with your first task
4. **Run**: `claude` → `/ralph-loop Follow ralph-tasks/PROMPT.md`
5. **Wait**: Let Ralph work (30-60+ mins)
6. **Review**: Check PR and merge

## Documentation Index

| File | Purpose |
|------|---------|
| `START-HERE.md` | Quick setup and first run |
| `ralph-tasks/SIMPLE-USAGE.md` | Complete usage guide |
| `ralph-tasks/README.md` | Task directory overview |
| `ralph-tasks/PROMPT.md` | Example task template |
| `.claude/RALPH-WORKFLOW.md` | Ralph's internal workflow |
| `.claude/CONTEXT.md` | Project context |
| `RALPH-SETUP-COMPLETE.md` | This file |

## Troubleshooting

**Container not running:**
```bash
docker compose -f .devcontainer/docker-compose.yml up -d
```

**Ralph can't create PR:**
```bash
gh auth login
```

**Want to stop Ralph:**
```
/cancel-ralph
```

**Ralph seems stuck:**
- Check container logs: `docker logs sagaapi-devcontainer-app-1`
- Ralph Loop has iteration limits, it will stop gracefully

## Tips for Success

1. **Be specific** - Clear requirements = better results
2. **Set acceptance criteria** - Ralph will follow them strictly
3. **Define constraints** - Tell Ralph what NOT to touch
4. **Trust self-review** - Ralph will be critical
5. **Review final PR** - You're the ultimate quality gate
6. **Start small** - Test with simple tasks first
7. **Iterate** - Refine your task templates based on results

---

## 🎉 You're Ready!

Everything is configured. Just run:

```bash
cd /Users/malchal/SagaApi
claude
/ralph-loop <your task>
```

Then go eat, sleep, or relax while Ralph works. Come back to review PRs. ☕️

**See `START-HERE.md` to begin!**
