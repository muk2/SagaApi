# Ralph Loop - Simple Usage Guide

Run Ralph Loop autonomously to develop, commit, create PR, review, and iterate until complete.

## TL;DR

```bash
# 1. Start Claude
claude

# 2. Run Ralph Loop with your task
/ralph-loop Complete the authentication test coverage task
```

That's it. Ralph will:
- ✅ Work in dev container
- ✅ Commit code as it works
- ✅ Create a PR when ready
- ✅ Review its own PR
- ✅ Iterate based on review
- ✅ Mark PR ready when done

You just review and merge the final PR.

## Setup (One-Time)

### 1. Claude CLI Login

```bash
# Login to Claude.ai (uses your Pro/Max subscription)
claude login

# No API key needed!
```

### 2. Git Configuration

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
# From project root
cd /Users/malchal/SagaApi
docker compose -f .devcontainer/docker-compose.yml up -d

# Verify it's running
docker ps | grep sagaapi
```

That's all the setup needed!

## Usage

### Define Your Task

Create or edit a task file (optional but recommended):

```bash
vim ralph-tasks/task-auth-tests.md
```

Example task:
```markdown
# Task: Add Comprehensive Auth Tests

## Objective
Add complete test coverage for authentication endpoints in the API.

## Acceptance Criteria
- [ ] All auth endpoints have integration tests
- [ ] Test coverage >= 80% for auth_service.py
- [ ] Tests include edge cases (invalid tokens, expired sessions)
- [ ] Tests use proper fixtures
- [ ] All tests pass

## Constraints
- Do NOT modify existing auth logic
- Use pytest and pytest-asyncio
- Follow existing test patterns in tests/ directory

## Workflow
1. Create branch: ralph/add-auth-tests
2. Implement tests incrementally
3. Run tests after each change
4. Commit working increments
5. When complete: push, create PR, self-review
6. Iterate based on review until ready
7. Mark PR as ready for human review
```

### Run Ralph Loop

```bash
# Start Claude
cd /Users/malchal/SagaApi
claude

# In Claude, run Ralph Loop with your task
/ralph-loop Add comprehensive authentication test coverage. Follow the task file at ralph-tasks/task-auth-tests.md. Create PR and self-review when done.
```

Or just paste the full task directly:

```
/ralph-loop Complete this task:

Task: Add auth test coverage
- Add tests for all auth endpoints
- Coverage >= 80%
- Include edge cases
- Create PR and self-review
- Iterate until ready
```

### Monitor Progress

Ralph Loop runs autonomously, but you can check:

```bash
# See branch Ralph created
git branch | grep ralph

# See commits Ralph made
git log --oneline ralph/<branch-name>

# See PR status
gh pr list --author @me

# Check dev container logs
docker logs sagaapi-devcontainer-app-1 --tail 50
```

### Review Final PR

When Ralph marks PR as ready:

```bash
# List PRs
gh pr list

# View the PR
gh pr view <number>

# See the diff
gh pr diff <number>

# Check out and test locally
gh pr checkout <number>
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest"

# Merge if satisfied
gh pr merge <number> --squash

# Or request changes
gh pr review <number> --request-changes --body "Please fix X"
```

## Ralph Loop Workflow Details

Ralph Loop will automatically:

### Phase 1: Development (Iterations 1-N)
- Read and understand codebase
- Create feature branch
- Implement code incrementally
- Run tests after each change in container
- Commit working increments
- Continue until implementation complete

### Phase 2: PR Creation (Iteration N+1)
- Push branch to remote
- Create draft PR with description
- Include summary of work done

### Phase 3: Self-Review (Iteration N+2)
- Get PR diff
- Critically review own code
- Add review comments identifying:
  - Missing edge cases
  - Error handling gaps
  - Test coverage gaps
  - Code quality issues
  - Documentation needs

### Phase 4: Iteration (Iterations N+3 onwards)
- Address review comments
- Make improvements
- Commit fixes
- Push updates
- Re-review changes
- Repeat until satisfied

### Phase 5: Finalization (Final iteration)
- Verify all acceptance criteria met
- Mark PR as ready (remove draft status)
- Add final summary comment
- Wait for human review

## Example Session

```
$ claude

Claude: Hi! I'm Claude Code.

You: /ralph-loop Add comprehensive test coverage for authentication endpoints.
     Requirements:
     - All auth endpoints tested
     - Coverage >= 80%
     - Edge cases included
     - Create PR and self-review when done

Claude: I'll help you add comprehensive test coverage. Let me start by...

[Ralph works autonomously for ~30-60 minutes]

Claude: I've completed the implementation and created PR #42. After self-review,
        I've addressed all feedback and marked it ready. The PR includes:
        - 15 new tests covering all auth endpoints
        - 87% coverage for auth_service.py
        - Edge cases for token expiration, invalid credentials, etc.
        - All tests passing

        Ready for your review!

You: [Later, review PR #42 and merge if satisfied]
```

## Stopping Ralph Early

If you need to stop Ralph before completion:

```
/cancel-ralph
```

Ralph will finish its current iteration gracefully and stop.

## Advanced: Multiple Tasks

Run multiple tasks in sequence:

```bash
# Task 1
claude
/ralph-loop <task 1>
# Wait for PR
/cancel-ralph

# Task 2
claude
/ralph-loop <task 2>
# Wait for PR
```

Or queue them in one session:

```
/ralph-loop Complete task 1: Add auth tests. When done, start task 2: Add logging.
```

## What Ralph Knows

Ralph has context from:
- `.claude/RALPH-WORKFLOW.md` - Workflow instructions
- `.claude/CLAUDE.md` - Project conventions
- Project files and structure
- Task description you provide

Ralph understands to:
- Run `pytest`, `ruff` etc. in the dev container
- Run `git`, `gh` on the host
- Make atomic commits
- Create and review PRs
- Iterate until quality standards met

## Troubleshooting

**Container not running:**
```bash
docker compose -f .devcontainer/docker-compose.yml up -d
```

**Ralph can't push to remote:**
```bash
# Check git credentials
git push origin main
# If fails, setup SSH or token auth
```

**Ralph creates commits but no PR:**
- Check GITHUB_TOKEN is set
- Or ensure `gh auth login` is done

**Want to see Ralph's thinking:**
Ralph Loop shows its thought process. Just read the conversation in Claude CLI.

## Tips

1. **Be specific** in your task description
2. **Set clear acceptance criteria** - Ralph will follow them
3. **Include constraints** - Tell Ralph what NOT to change
4. **Trust the process** - Ralph will self-review critically
5. **Review the final PR** - Ralph isn't perfect, you're the final gate

## Safety

✅ Ralph works on separate branch (never touches main)
✅ Creates draft PRs (you must approve final merge)
✅ Self-reviews critically before marking ready
✅ Runs in isolated container
✅ You control what gets merged to main

---

**You're ready!** Just run:

```bash
claude
/ralph-loop <your task>
```

And go get coffee. ☕️
