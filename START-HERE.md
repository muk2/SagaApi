# 🚀 Start Here - Ralph Loop Setup

Complete autonomous development with Ralph Loop: Just run `claude` and use `/ralph-loop`.

## What You Get

```
You: claude
You: /ralph-loop <your task>

[Ralph works autonomously for 30-60+ mins]

Ralph: ✅ PR #42 created and ready for your review!
```

Ralph will:
- ✅ Work in your dev container
- ✅ Make code changes
- ✅ Run tests after each change
- ✅ Commit working increments
- ✅ Push branch
- ✅ Create PR
- ✅ **Review its own PR critically**
- ✅ **Make improvements based on review**
- ✅ **Iterate until ready**
- ✅ Mark PR ready for your final review

You just merge the final PR.

## Quick Setup (2 minutes)

### 1. Claude CLI Login (if not already logged in)
```bash
# Login to Claude.ai (uses your Pro/Max subscription)
claude login

# That's it - no API key needed!
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

## First Run

```bash
# 1. Start Claude
cd /Users/malchal/SagaApi
claude

# 2. Run Ralph Loop with task from file
/ralph-loop Follow the task at ralph-tasks/PROMPT.md
```

Or inline:

```
/ralph-loop Add comprehensive test coverage for authentication endpoints.
Create PR and self-review when done. Requirements:
- All auth endpoints have tests
- Coverage >= 80%
- Include edge cases
- All tests must pass
```

That's literally it. Go get coffee while Ralph works.

## What Happens Next

Ralph Loop will:

**Phase 1 - Development** (~10-20 mins)
- Reads existing code
- Creates branch `ralph/add-auth-tests`
- Implements tests incrementally
- Runs tests in container after each change
- Commits working code

**Phase 2 - PR Creation** (~1 min)
- Pushes branch
- Creates draft PR with description

**Phase 3 - Self-Review** (~5 mins)
- Gets PR diff
- Reviews code critically
- Adds review comments:
  - "Missing edge case for expired tokens"
  - "Need error handling for invalid input"
  - "Test coverage gap in logout endpoint"

**Phase 4 - Iteration** (~15-30 mins)
- Addresses each review comment
- Makes improvements
- Commits fixes
- Pushes updates
- Re-reviews

**Phase 5 - Finalization** (~1 min)
- Marks PR as ready
- Adds final summary
- Stops iterating

You review and merge PR #42. 🎉

## Monitoring Progress

While Ralph works:

```bash
# See Ralph's branch
git branch | grep ralph

# See commits Ralph made
git log --oneline ralph/<branch-name>

# Check PR status
gh pr list

# View container logs
docker logs sagaapi-devcontainer-app-1 --tail 50
```

## Reviewing Final PR

```bash
# View PR
gh pr view <number>

# See changes
gh pr diff <number>

# Test locally
gh pr checkout <number>
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest"

# Merge if good
gh pr merge <number> --squash
```

## Documentation

- **`ralph-tasks/SIMPLE-USAGE.md`** - Full usage guide
- **`.claude/RALPH-WORKFLOW.md`** - What Ralph does internally
- **`.claude/CONTEXT.md`** - Project context for Claude

## Example Task Templates

Create task files in `ralph-tasks/`:

**ralph-tasks/add-auth-tests.md:**
```markdown
# Add Authentication Test Coverage

## Objective
Complete test coverage for all authentication endpoints.

## Acceptance Criteria
- [ ] All auth endpoints have integration tests
- [ ] Coverage >= 80% for auth_service.py
- [ ] Tests include edge cases
- [ ] All tests pass
- [ ] PR created and self-reviewed

## Constraints
- Do NOT modify existing auth logic
- Use pytest and pytest-asyncio
- Follow existing test patterns

## Workflow
1. Create branch ralph/add-auth-tests
2. Implement tests incrementally
3. Commit after each working increment
4. Create PR and self-review
5. Iterate based on review
6. Mark ready when done
```

Then run:
```bash
claude
/ralph-loop Follow the task at ralph-tasks/add-auth-tests.md
```

## Tips for Best Results

✅ **Be specific** - Clear requirements = better results
✅ **Set acceptance criteria** - Ralph will follow them
✅ **Define constraints** - Tell Ralph what NOT to touch
✅ **Trust self-review** - Ralph will be critical of its own code
✅ **Review the final PR** - You're the ultimate quality gate

## Safety Features

- Ralph works on **separate branch** (never touches main)
- Creates **draft PRs** (you approve final merge)
- **Self-reviews critically** before marking ready
- Works in **isolated container**
- You **control merges** to main

## Troubleshooting

**Container not running:**
```bash
docker compose -f .devcontainer/docker-compose.yml up -d
```

**Can't push to GitHub:**
```bash
gh auth login
```

**Ralph seems stuck:**
Type `/cancel-ralph` in Claude session

**Not logged into Claude:**
```bash
claude login
```

## Next Steps

1. Complete the 2-minute setup above
2. Run your first Ralph Loop session
3. Watch the magic happen
4. Review and merge the PR

---

**Ready to go!**

```bash
claude
/ralph-loop Follow the task at ralph-tasks/PROMPT.md
```

☕️ Go relax while Ralph codes.
