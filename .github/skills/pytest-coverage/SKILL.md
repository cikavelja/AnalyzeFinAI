---
name: pytest-coverage
description: "Run pytest tests with coverage, discover lines missing coverage, and increase coverage to 100%. Use when a module has low coverage, after adding new code, or when asked to 'improve test coverage', 'find untested lines', or 'get to 100% coverage'."
---

# Pytest Coverage

The goal is for all tests to cover every line of code.

## Step 1 — Generate a coverage report

```bash
pytest --cov --cov-report=annotate:cov_annotate
```

To check a specific module:
```bash
pytest --cov=app.financial.calculator --cov-report=annotate:cov_annotate
```

To run specific tests:
```bash
pytest tests/unit/test_calculator.py --cov=app.financial.calculator --cov-report=annotate:cov_annotate
```

## Step 2 — Identify uncovered lines

Open the `cov_annotate/` directory. There is one file per source file.

- If a file has **100% coverage**, skip it — no action needed.
- For files with **less than 100%**: find lines starting with `!` — these are uncovered.

## Step 3 — Add tests for uncovered lines

For each uncovered line:
1. Identify what scenario would exercise that line (error path, edge case, boundary value).
2. Add a test in the corresponding `tests/unit/test_<module>.py` file.
3. Follow the naming pattern: `test_<function>_<scenario>_<expected>`.
4. Mock all external dependencies (LLM, MCP, filesystem, HTTP).

## Step 4 — Iterate

Re-run coverage after each test addition:
```bash
pytest --cov --cov-report=annotate:cov_annotate
```

Continue until `!` lines are eliminated from all source files.

## AnalizerAI Coverage Priorities

Address these modules first — they are highest-risk:

| Priority | Module | Why |
|----------|--------|-----|
| 1 | `app/financial/calculator.py` | Deterministic — every formula must be tested |
| 2 | `app/ingestion/validator.py` | Security boundary — file validation |
| 3 | `app/routing/router.py` | Correctness — wrong routing = wrong analysis type |
| 4 | `app/conversion/local_converter.py` | Failure paths must be covered |
| 5 | `app/validation/validator.py` | Grounding checks must not be bypassed |

## Common Uncovered Patterns

- `except` clauses — add a test that mocks the dependency to raise the exception
- `if x is None` branches — call with `None` input
- Final `else` branches — ensure the default path is exercised
- Early `return` guards — call with invalid inputs that trigger the guard
