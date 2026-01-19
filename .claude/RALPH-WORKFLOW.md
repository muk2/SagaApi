# Ralph Loop Autonomous Development Workflow

You are running in Ralph Loop mode, which means you will work autonomously to complete a task, create a PR, review it, and iterate until completion.

## Your Environment

**Dev Container:**
- Name: `sagaapi-devcontainer-app-1`
- Working directory: `/workspace`
- Database: PostgreSQL at `db:5432`

**Command Execution:**
- Python/tests/linting: Run in container via `docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && <command>"`
- Git operations: Run on host normally
- File operations: Work normally (shared mount)

## Ralph Loop Workflow

### Phase 1: Development
1. **Understand the task** - Read existing code and requirements
2. **Create a branch** - `git checkout -b ralph/<descriptive-name>`
3. **Implement incrementally**:
   - Make small, atomic changes
   - Run tests after each change: `docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest"`
   - Commit after each working increment: `git commit -m "[ralph] <description>"`
4. **Ensure quality**:
   - All tests pass
   - No linting errors: `docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && ruff check src/"`
   - Code follows project patterns

### Phase 2: PR Creation
Once implementation is complete:
1. **Push branch**: `git push -u origin <branch-name>`
2. **Create PR**: `gh pr create --base main --title "<title>" --body "<body>" --draft`
3. **Mark as draft initially** - This signals it's ready for self-review

### Phase 3: Self-Review (Critical!)
You MUST review your own PR critically:

1. **Request PR diff**: `gh pr diff <pr-number>`
2. **Analyze thoroughly**:
   - Edge cases not covered?
   - Error handling sufficient?
   - Tests comprehensive?
   - Code quality issues?
   - Documentation needed?
3. **Make review comments**: `gh pr review <pr-number> --comment --body "<feedback>"`
4. **Identify improvements needed**

### Phase 4: Iteration
Based on your review comments:

1. **Make improvements** on the same branch
2. **Commit changes**: `git commit -m "[ralph] Address review: <what you fixed>"`
3. **Push updates**: `git push`
4. **Re-review**: `gh pr diff <pr-number>` and verify fixes
5. **Add review comments** if more work needed
6. **Repeat** until satisfied

### Phase 5: Finalization
When the PR is truly ready:

1. **Mark as ready**: `gh pr ready <pr-number>` (removes draft status)
2. **Final summary comment**: Explain what was implemented, tested, and reviewed
3. **Stop iterating** - Your work is done, human will merge

## Quality Standards

Before marking PR as ready, ensure:
- [ ] All tests pass in container
- [ ] No linting errors
- [ ] Code coverage maintained or improved
- [ ] Edge cases handled
- [ ] Error messages are clear
- [ ] Documentation updated if needed
- [ ] No security vulnerabilities introduced
- [ ] Follows existing code patterns
- [ ] Commits are atomic and well-described

## Command Templates

**Run tests in container:**
```bash
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest tests/"
```

**Run linting in container:**
```bash
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && ruff check src/"
```

**Check coverage in container:**
```bash
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest --cov=src tests/"
```

**Create PR:**
```bash
gh pr create --base main --head <branch> --title "feat: <description>" --body "<detailed description>" --draft
```

**Review own PR:**
```bash
gh pr diff <pr-number>
gh pr review <pr-number> --comment --body "Review feedback here"
```

**Mark PR ready:**
```bash
gh pr ready <pr-number>
```

## Iteration Strategy

Ralph Loop will iterate automatically. For each iteration:

1. **Check current state**: What's been done? What's left?
2. **Make progress**: Implement next piece or fix identified issues
3. **Validate**: Run tests, check quality
4. **Commit**: Make atomic commit
5. **Assess**: Are we done? If not, continue

**Stop conditions:**
- PR is marked ready and passes all checks
- Max iterations reached (Ralph Loop handles this)
- Blocker encountered that requires human intervention

## Example Flow

```bash
# Iteration 1: Initial implementation
git checkout -b ralph/add-auth-tests
# ... write code ...
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest"
git commit -m "[ralph] Add basic auth endpoint tests"

# Iteration 2: More coverage
# ... add more tests ...
git commit -m "[ralph] Add edge case tests for auth"

# Iteration 3: Create PR
git push -u origin ralph/add-auth-tests
gh pr create --base main --title "Add comprehensive auth tests" --body "..." --draft

# Iteration 4: Self-review
gh pr diff 123
gh pr review 123 --comment --body "Missing tests for token expiration"

# Iteration 5: Address review
# ... add token expiration tests ...
git commit -m "[ralph] Address review: Add token expiration tests"
git push

# Iteration 6: Verify and finalize
gh pr diff 123
gh pr ready 123
# Done!
```

## Important Notes

- **Always start dev container if not running**: Check with `docker ps`
- **Make frequent commits**: Easier to track progress and rollback if needed
- **Be critical in self-review**: Don't just rubber-stamp your work
- **Test everything**: Run tests before every commit
- **Document decisions**: Use commit messages and PR comments
- **Follow project conventions**: Match existing code style and patterns

## Failure Handling

If you encounter issues:

1. **Container not running**: `docker compose -f .devcontainer/docker-compose.yml up -d`
2. **Tests failing**: Fix them before proceeding
3. **Linting errors**: Fix them before committing
4. **Git conflicts**: Rebase on main if needed
5. **Unknown blocker**: Document in PR comment and stop gracefully

Your goal: Deliver a high-quality, well-tested PR ready for human review and merge.
