---
description: "Generate comprehensive unit tests for an AnalizerAI module. Use when a module has no tests or tests need expanding to cover error paths and edge cases."
argument-hint: "Path to the module to test, e.g. 'app/financial/calculator.py'"
agent: agent
tools: [read, search, edit]
---

You are generating unit tests for the AnalizerAI project.

## Step 1 — Read the target module

Read **${input}** and identify:
- All public functions and methods (ignore `_private` ones)
- All parameters and return types
- All external dependencies that need to be mocked (LLM calls, filesystem, HTTP, MCP)

## Step 2 — Read existing tests

Search `tests/unit/` for any existing test file for this module. If found, read it
and only generate tests for uncovered scenarios.

## Step 3 — Determine the test file path

If the module is `app/foo/bar.py` → test file is `tests/unit/test_bar.py`.

## Step 4 — Generate tests

Follow [tests.instructions.md](../.github/instructions/tests.instructions.md) exactly.

For every public function generate:

### a) Success path
```python
@pytest.mark.asyncio
async def test_<function>_<happy_scenario>_<expected>() -> None:
    # Arrange: set up inputs and mocks
    # Act: call the function
    # Assert: verify return value and types
```

### b) Error/failure path
```python
@pytest.mark.asyncio
async def test_<function>_<error_scenario>_raises_or_returns_failure() -> None:
    # Arrange: mock the dependency to fail
    # Act + Assert: verify exception type or failure result
```

### c) Edge cases
- Empty list / empty string / zero / None inputs where applicable
- Boundary values (e.g. file at exactly MAX_FILE_SIZE_MB)

## Step 5 — Mocking rules

- LLM calls → `mocker.AsyncMock` returning a fixture string or Pydantic model
- Filesystem → use `tmp_path` pytest fixture
- HTTP/MCP → `respx` or `mocker.patch`
- `datetime.now()` → patch at the module level

## Step 6 — Write the test file

Create or update `tests/unit/test_<module>.py`.

## Step 7 — Confirm

State how many test functions were added and which scenarios are now covered.
