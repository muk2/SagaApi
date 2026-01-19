# Task Template for Ralph Loop

<!--
This is a template for Ralph Loop autonomous development tasks.
Ralph will develop, commit, create PR, self-review, iterate, and finalize.
-->

## Task Objective
Add comprehensive test coverage for the authentication system

## Acceptance Criteria
- [ ] All auth endpoints have integration tests
- [ ] Test coverage is at least 80% for auth_service.py and auth_repository.py
- [ ] Tests pass with pytest
- [ ] Tests include edge cases (invalid tokens, expired sessions, etc.)
- [ ] Add pytest fixtures for common test data
- [ ] PR created and self-reviewed
- [ ] All review feedback addressed

## Constraints
- Do NOT modify the existing authentication logic in `src/services/auth_service.py`
- Do NOT change database schema
- Use pytest and pytest-asyncio for async tests
- Use httpx for FastAPI test client
- Follow existing project structure (put tests in `tests/` directory)

## Implementation Workflow

### Phase 1: Development
1. Create branch: `ralph/add-auth-test-coverage`
2. Explore existing auth code to understand implementation
3. Design test strategy covering all auth flows
4. Implement tests incrementally:
   - Run tests in container after each change: `docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest"`
   - Commit working increments: `[ralph] Add tests for X`
5. Ensure all quality checks pass:
   - All tests pass
   - No linting errors: `docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && ruff check src/"`
   - Coverage >= 80%: `docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest --cov=src/services/auth_service --cov=src/repositories/auth_repository"`

### Phase 2: PR Creation
1. Push branch: `git push -u origin ralph/add-auth-test-coverage`
2. Create draft PR: `gh pr create --base main --title "Add comprehensive auth test coverage" --body "<description>" --draft`

### Phase 3: Self-Review
1. Get PR diff: `gh pr diff <pr-number>`
2. Review critically and add comments: `gh pr review <pr-number> --comment --body "<feedback>"`
   - Check for missing edge cases
   - Verify error handling
   - Assess test coverage gaps
   - Identify code quality issues
   - Note any documentation needs

### Phase 4: Iteration
1. Address each review comment
2. Make improvements on the same branch
3. Commit fixes: `[ralph] Address review: <what you fixed>`
4. Push updates: `git push`
5. Re-review to verify fixes
6. Repeat until all feedback addressed

### Phase 5: Finalization
1. Verify all acceptance criteria met
2. Mark PR as ready: `gh pr ready <pr-number>`
3. Add final summary comment explaining what was done

## Quality Standards

Before marking PR as ready:
- [ ] All tests pass in container
- [ ] No linting errors
- [ ] Code coverage >= 80% for auth modules
- [ ] Edge cases handled (invalid tokens, expired sessions, etc.)
- [ ] Error messages are clear
- [ ] Follows existing code patterns
- [ ] Commits are atomic and well-described
- [ ] Self-review completed with critical feedback
- [ ] All review feedback addressed

## Success Metrics
1. `pytest` exits with code 0 (all tests pass)
2. Coverage report shows >= 80% for auth modules
3. No linting errors from `ruff check`
4. API still starts without errors
5. PR created, reviewed, and marked ready
6. Human can review and merge confidently

## Technical Context
- Database URL: `postgresql://sagaapi:sagaapi_dev@db:5432/sagaapi`
- Dev container: `sagaapi-devcontainer-app-1`
- Working directory in container: `/workspace`
- FastAPI test client: Use `TestClient` from `fastapi.testclient`

## Important Notes
- Run all Python/testing commands in the dev container using `docker exec`
- Run git/GitHub CLI commands on the host normally
- Make frequent, atomic commits as you work
- Be critical in your self-review - don't just approve your work
- Test everything thoroughly before marking PR ready
