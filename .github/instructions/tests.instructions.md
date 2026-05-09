---
description: "Use when writing or editing tests in tests/. Covers pytest-asyncio patterns, mocking rules, fixture conventions, naming standards, and what must never hit real APIs."
applyTo: "tests/**/*.py"
---
# Test Conventions

## Async Tests

All async tests must use `@pytest.mark.asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_converter_success_returns_markdown() -> None:
    ...
```

Configure once in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## Naming Pattern

`test_<function_or_class>_<scenario>_<expected_result>`

Examples:
- `test_detect_file_type_pdf_returns_pdf_mime`
- `test_router_financial_prompt_returns_financial_plan`
- `test_calculator_yoy_zero_prior_raises_calculation_error`

## Mocking Rules — What Must Always Be Mocked

| Dependency | Mock with |
|-----------|-----------|
| LLM provider (OpenAI, HuggingFace) | `pytest-mock` `mocker.AsyncMock` |
| MarkItDown MCP server | `pytest-mock` `mocker.patch` |
| Filesystem reads/writes | `tmp_path` fixture or `mocker.patch` |
| `httpx` / `requests` | `respx` for httpx, `responses` for requests |
| `datetime.now()` | `mocker.patch("module.datetime")` |

**Unit tests must never hit real APIs, real filesystems (outside `tmp_path`), or real network.**

## Fixture Patterns

Use `factory-boy` for Pydantic model factories:

```python
import factory
from app.models.document import DocumentMetadata

class DocumentMetadataFactory(factory.Factory):
    class Meta:
        model = DocumentMetadata
    file_name = factory.Sequence(lambda n: f"doc_{n}.pdf")
    file_size = 1024
    extension = ".pdf"
```

Sample documents for integration tests live in `tests/fixtures/sample_docs/`.

## Coverage Requirement

Every public function in `app/` must have at least:
- One success-path test
- One failure/error-path test
- Edge cases where inputs are empty, zero, or None
