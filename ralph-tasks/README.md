# Ralph Loop Tasks

This directory contains task definitions for Ralph Loop autonomous development.

## Quick Start

```bash
# 1. Start Claude CLI
claude

# 2. Run Ralph Loop with a task
/ralph-loop Follow the task defined in ralph-tasks/PROMPT.md. Create PR and self-review when complete.
```

Ralph will autonomously:
- Develop the code in dev container
- Run tests and commit changes
- Create a pull request
- Review its own PR critically
- Iterate based on review feedback
- Mark PR ready for your final review

## Files

- **`PROMPT.md`** - Example task template (edit this for your tasks)
- **`SIMPLE-USAGE.md`** - Complete usage documentation
- **`README.md`** - This file

## Task Template Structure

Each task should include:

1. **Task Objective** - Clear goal
2. **Acceptance Criteria** - Checklist of requirements
3. **Constraints** - What NOT to change
4. **Implementation Workflow** - Phase-by-phase instructions
5. **Quality Standards** - What makes the PR ready
6. **Technical Context** - Environment details

See `PROMPT.md` for a complete example.

## Creating New Tasks

```bash
# Copy the template
cp ralph-tasks/PROMPT.md ralph-tasks/my-new-task.md

# Edit for your needs
vim ralph-tasks/my-new-task.md

# Run Ralph Loop
claude
/ralph-loop Follow ralph-tasks/my-new-task.md
```

## Example Tasks

**Add Test Coverage:**
```markdown
## Task Objective
Add comprehensive test coverage for authentication endpoints

## Acceptance Criteria
- [ ] All endpoints tested
- [ ] Coverage >= 80%
- [ ] Edge cases included
- [ ] PR created and self-reviewed
```

**Add Logging:**
```markdown
## Task Objective
Add structured logging to all API endpoints

## Acceptance Criteria
- [ ] All endpoints log requests/responses
- [ ] Use structured JSON logging
- [ ] Include request IDs
- [ ] PR created and self-reviewed
```

**Refactor Module:**
```markdown
## Task Objective
Refactor authentication service for better testability

## Acceptance Criteria
- [ ] Extract dependencies to constructor
- [ ] Add interfaces for external services
- [ ] Tests still pass
- [ ] PR created and self-reviewed
```

## Ralph Loop Workflow

Ralph automatically follows this workflow:

### 1. Development Phase
- Creates feature branch
- Implements code incrementally
- Runs tests after each change
- Commits working increments

### 2. PR Creation Phase
- Pushes branch to remote
- Creates draft PR

### 3. Self-Review Phase
- Gets PR diff
- Reviews code critically
- Adds review comments identifying issues

### 4. Iteration Phase
- Addresses review feedback
- Makes improvements
- Commits and pushes
- Re-reviews changes

### 5. Finalization Phase
- Marks PR as ready
- Adds final summary
- Waits for human review

## Dev Container Commands

Ralph knows to run these in the container:

```bash
# Tests
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest"

# Linting
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && ruff check src/"

# Coverage
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest --cov=src"
```

## Git/GitHub Commands

Ralph runs these on the host:

```bash
git checkout -b ralph/<branch-name>
git add .
git commit -m "[ralph] Description"
git push -u origin ralph/<branch-name>
gh pr create --draft
gh pr review <number> --comment
gh pr ready <number>
```

## Monitoring Progress

While Ralph works:

```bash
# See Ralph's branch
git branch | grep ralph

# See commits
git log --oneline ralph/<branch-name>

# Check PRs
gh pr list

# View container activity
docker logs sagaapi-devcontainer-app-1 --tail 50
```

## Reviewing Final PR

When Ralph finishes:

```bash
# View PR
gh pr view <number>

# See changes
gh pr diff <number>

# Checkout and test
gh pr checkout <number>
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest"

# Merge if satisfied
gh pr merge <number> --squash
```

## Tips

✅ **Be specific** - Clear acceptance criteria help Ralph focus
✅ **Set constraints** - Tell Ralph what NOT to change
✅ **Trust self-review** - Ralph will be critical of its own work
✅ **Define quality standards** - Ralph will follow them
✅ **Review final PR** - You're the ultimate quality gate

## Documentation

- **Project Setup**: See `/START-HERE.md` in project root
- **Full Usage Guide**: `ralph-tasks/SIMPLE-USAGE.md`
- **Ralph Workflow**: `.claude/RALPH-WORKFLOW.md`
- **Project Context**: `.claude/CONTEXT.md`

## Troubleshooting

**Container not running:**
```bash
docker compose -f .devcontainer/docker-compose.yml up -d
```

**Ralph can't create PR:**
```bash
gh auth login
```

**Stop Ralph early:**
```
/cancel-ralph
```

---

**Ready to start?**

Edit `PROMPT.md` and run:
```bash
claude
/ralph-loop Follow ralph-tasks/PROMPT.md
```
