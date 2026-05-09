# AnalyzeFinAI — Bug & Fix Tracker

> Auto-generated from full codebase audit. Work through sections top-to-bottom.  
> Each item is self-contained: file, problem, and concrete fix are all described.

---

## 🔴 CRITICAL — Fix Before Any Merge

---

### CRIT-1 · Real API Key in `.env` ✅ DONE
**File:** `.env` line 7  
**Problem:** A live `sk-proj-…` OpenAI key is stored in `.env`. Even though `.gitignore` excludes it, the file exists on disk and any accidental `git add -f` or IDE mistake permanently exposes it.  
**Fix:**
1. Rotate the key immediately at [platform.openai.com](https://platform.openai.com).
2. Replace the value with `sk-replace-me` placeholder.
3. Add `detect-secrets` or `git-secrets` pre-commit hook to prevent future leaks.

---

### CRIT-2 · File Read into Memory Before Size Validation ✅ DONE
**File:** `app/api/routes/documents.py` line 35  
**Problem:** `content = await file.read()` loads the **entire** upload into RAM before the 100 MB limit is checked. A multi-GB payload causes OOM before any guard fires.  
**Fix:** Check size before reading:
```python
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
if file.size and file.size > MAX_UPLOAD_BYTES:
    raise HTTPException(status_code=413, detail="File too large")
content = await file.read()
```
Or use streaming chunked ingestion.

---


### CRIT-4 · `LOCAL_ONLY_MODE` Not Enforced for MAF Agent LLM Calls ✅ DONE
**Files:** `app/agents/analyst_agent.py`, `app/agents/orchestrator_agent.py`, `app/agents/reviewer_agent.py` (lines 20–25 each)  
**Problem:** The `local_only_mode` guard lives only inside `OpenAIProvider.complete()` and `MCPConverter.convert()`. Agents construct `OpenAIChatClient` directly via `agent_framework` and bypass this guard entirely. With `LOCAL_ONLY_MODE=true`, agents still make real LLM calls.  
**Fix:** Add at the top of each `_build_*_agent()` function:
```python
if settings.local_only_mode:
    raise AnalysisError("LOCAL_ONLY_MODE is enabled — agent LLM calls are blocked.")
```

---

### CRIT-5 · ZIP Files: Zip Bomb Risk + LocalConverter Produces Garbage ✅ DONE
**Files:** `app/ingestion/detector.py` line 18, `app/conversion/local_converter.py`, `app/conversion/markitdown_converter.py`  
**Analysis:**  
- `MarkitdownConverter` already works correctly for ZIPs — markitdown has a built-in `ZipConverter` that reads each entry into `BytesIO` in memory (no disk extraction → **no path-traversal risk**).  
- `LocalConverter` decodes ZIP bytes as raw UTF-8 → produces garbage output silently.  
- **The only remaining risk is zip bombs**: markitdown calls `zipObj.read(name)` with no uncompressed-size limit — a crafted 42 KB ZIP inflating to 4 GB causes OOM.

**Fix:**  
1. In `MarkitdownConverter.convert()`, add a pre-flight zip-bomb check before delegating:
```python
import zipfile
MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024  # 500 MB

if path.suffix.lower() == ".zip":
    with zipfile.ZipFile(path, "r") as zf:
        total_uncompressed = sum(e.file_size for e in zf.infolist())
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise ConversionError(
                f"ZIP uncompressed size {total_uncompressed} bytes exceeds the 500 MB limit."
            )
# then proceed with self._md.convert(str(path)) as normal
```
2. In `LocalConverter.convert()`, reject `.zip` explicitly:
```python
if ext == ".zip":
    raise ConversionError(
        "ZIP files are not supported in local conversion mode. "
        "Set CONVERSION_MODE=markitdown to enable ZIP support."
    )
```

---

## 🟠 HIGH — Fix Before Release

---

### HIGH-1 · Blocking Sync I/O Inside Async Converter ✅ DONE
**File:** `app/conversion/mcp_converter.py` line 41  
**Problem:** `with open(file_path, "rb") as fh:` is synchronous and blocks the asyncio event loop for all concurrent requests.  
**Fix:**
```python
content = await asyncio.to_thread(Path(file_path).read_bytes)
```

---

### HIGH-2 · Deprecated `asyncio.get_event_loop()` in Audit Logger ✅ DONE
**File:** `app/audit/logger.py` line 47  
**Problem:** `asyncio.get_event_loop()` is deprecated since Python 3.10 and raises `RuntimeError` in some 3.12+ contexts.  
**Fix:**
```python
loop = asyncio.get_running_loop()
await loop.run_in_executor(None, self._append_sync, line)
```

---

### HIGH-3 · Infinite Loop When `overlap >= chunk_size` in Chunker ✅ DONE
**File:** `app/chunking/chunker.py` line 75  
**Problem:** `start = end - overlap`. If `overlap >= chunk_size`, then `end - overlap <= start` → infinite loop. No input validation exists.  
**Fix:** Guard at function entry:
```python
if overlap >= chunk_size:
    raise ValueError(f"overlap ({overlap}) must be less than chunk_size ({chunk_size})")
```

---

### HIGH-4 · CAGR Formula Not Wrapped in Try/Except ✅ DONE
**File:** `app/financial/calculator.py` line 126  
**Problem:** `(end_val / start_val) ** (1 / n_years) - 1` can raise `ValueError` or produce complex numbers for edge-case negative inputs that slip past the `> 0` guard. The call site is outside the try/except block.  
**Fix:** Wrap the computation:
```python
try:
    metrics.cagr = (end_val / start_val) ** (1 / n_years) - 1
except (ValueError, ZeroDivisionError):
    metrics.cagr = None
```

---

### HIGH-5 · Double `path.stat()` Call Creates Race Condition ✅ DONE
**File:** `app/ingestion/loader.py` lines 48 and 58  
**Problem:** `path.stat().st_size` is called twice. Between calls the file size could change. Audit log also lacks `request_id`.  
**Fix:**
```python
stat = path.stat()
# use stat.st_size in both DocumentMetadata and audit detail
```
Add `request_id: UUID | None = None` param to `load_document()` and thread it into `AuditEvent`.

---

### HIGH-6 · Converter Selection Logic Duplicated ✅ DONE
**Files:** `app/ingestion/document_loader.py` lines 22–30 and `app/workflows/analysis_workflow.py` lines 62–67  
**Problem:** Converter factory is copy-pasted in two places. Adding a new converter requires updating both; divergence produces different behavior on the API path vs. the workflow path.  
**Fix:** Create a single factory in `app/conversion/__init__.py`:
```python
def get_converter() -> AbstractConverter:
    if settings.conversion_mode == "mcp":
        return MCPConverter()
    if settings.conversion_mode == "markitdown":
        return MarkitdownConverter()
    return LocalConverter()
```
Import and use everywhere.

---

### HIGH-7 · Raw Exception Messages Leaked to API Clients ✅ DONE
**Files:** `app/api/routes/analysis.py` line 68, `app/api/routes/documents.py` line 64  
**Problem:** `raise HTTPException(status_code=500, detail=str(exc))` sends Python stack details and internal paths to the client (OWASP A05 violation).  
**Fix:**
```python
logger.error("api_error", error=str(exc), exc_info=True)
raise HTTPException(status_code=500, detail="Internal server error") from exc
```

---

### HIGH-8 · MCP Server Endpoint Hardcoded — Not Configurable ✅ DONE
**File:** `app/conversion/mcp_converter.py` line 19  
**Problem:** `_MCP_ENDPOINT = "http://localhost:3001/convert"` is hardcoded. With `CONVERSION_MODE=mcp`, the address cannot be changed without editing source.  
**Fix:** Add to `app/config.py`:
```python
mcp_endpoint: str = Field(default="http://localhost:3001/convert", alias="MCP_ENDPOINT")
```
Use `settings.mcp_endpoint` in `MCPConverter`.

---

### HIGH-9 · `data/uploads/` Not in `.gitignore` ✅ DONE
**File:** `.gitignore`  
**Problem:** User-uploaded (potentially confidential) financial documents in `data/uploads/` are not gitignored. A `git add .` would stage them.  
**Fix:** Add to `.gitignore`:
```
data/uploads/
data/converted/
```

---

### HIGH-10 · Workflow Ingestion Step Is a No-Op Stub ✅ DONE
**File:** `app/workflows/analysis_workflow.py` lines 32–46  
**Problem:** `ingest_step` only records a timestamp and document count. It never calls `load_document()`, creates no `DocumentMetadata`, and emits no audit events. The step is functionally empty.  
**Fix:** Call `await load_document(file_path)` for each document, resolving paths from `data/uploads/`.

---

### HIGH-11 · `load_chunks` Called Twice for Same Document ✅ DONE
**File:** `app/agents/analyst_agent.py` lines 58 and 103  
**Problem:** When `AnalysisType.FINANCIAL` is processed, `load_chunks([UUID(document_id)])` runs inside both `analyze_document()` and `run_financial_calculation()`. If the orchestrator invokes both tools, the file is converted twice.  
**Fix:** Cache chunks by `document_id` within a request context, or pass chunks as a parameter between tool calls rather than re-loading.

---

## 🟡 MEDIUM — Should Fix

---

### MED-1 · Workflow Steps Emit No Audit Events ✅ DONE
**File:** `app/workflows/analysis_workflow.py` (all step functions)  
**Problem:** The audit-first rule requires every pipeline step to emit `AuditEvent` start + end. Workflow steps only write structlog messages.  
**Fix:** Add `await audit_logger.emit(AuditEvent(event_type="workflow_step", status="started", ...))` at the top and bottom of each `@executor` decorated function.

---

### MED-2 · Converters Emit No Audit Events ✅ DONE
**Files:** `app/conversion/local_converter.py`, `app/conversion/markitdown_converter.py`, `app/conversion/mcp_converter.py`  
**Problem:** No converter emits `AuditEvent` start/end, violating the audit-first architecture requirement.  
**Fix:** Add `await audit_logger.emit(...)` at the start and end of each `convert()` method.

---

### MED-3 · Router and Chunker Emit No Audit Events ✅ DONE
**Files:** `app/routing/router.py`, `app/chunking/chunker.py`  
**Problem:** Same as MED-2. Pipeline steps with no audit trail.  
**Fix:** Emit `AuditEvent` at start and end of `route()` and `chunk_text()`.

---

### MED-4 · `FilesystemStorage` Implemented But Never Used ✅ DONE
**File:** `app/storage/filesystem.py`  
**Problem:** Converted markdown is not persisted. Every `analyze` request re-reads and re-converts the original file. If `data/uploads/` is cleaned, the document is lost permanently.  
**Fix:** Integrate `FilesystemStorage` into `document_loader.py`: save converted markdown after first conversion, load from cache on repeat requests.

---

### MED-5 · `AnalysisType.CUSTOM` Is Unreachable via Router ✅ DONE
**File:** `app/routing/router.py` lines 25–66  
**Problem:** `_ROUTING_TABLE` has no entry for `CUSTOM`. No keyword set maps to it. It can only be set if the client sends `analysis_type: "custom"` directly, but `AnalyzeRequest` only accepts a `prompt` field — making `CUSTOM` permanently unreachable through the intended API flow.  
**Fix:** Either add a `CUSTOM` keyword set, or expose `analysis_type` as an override field in `AnalyzeRequest`.

---

### MED-6 · DataFrame Column Recomputed Three Times ✅ DONE
**File:** `app/financial/calculator.py` lines 106, 119, 132  
**Problem:** `pd.to_numeric(df["revenue"], errors="coerce").dropna()` is computed separately for YoY growth, CAGR, and trend slope. Redundant processing.  
**Fix:**
```python
if "revenue" in df.columns:
    rev_series = pd.to_numeric(df["revenue"], errors="coerce").dropna()
    # use rev_series for all three metrics
```

---

### MED-7 · `_make_client()` Copy-Pasted Across Three Agent Files ✅ DONE
**Files:** `app/agents/analyst_agent.py` line 20, `app/agents/orchestrator_agent.py` line 21, `app/agents/reviewer_agent.py` line 19  
**Problem:** Identical 4-line function is triplicated. Changes must be applied in three places.  
**Fix:** Create `app/agents/_client.py`:
```python
def make_agent_client() -> OpenAIChatClient:
    kwargs: dict = {"model": settings.openai_model}
    if settings.openai_api_key:
        kwargs["api_key"] = settings.openai_api_key
    return OpenAIChatClient(**kwargs)
```

---

### MED-8 · `import json` Inside Hot Async Loop ✅ DONE
**File:** `app/llm/provider.py` line 123  
**Problem:** `import json` is inside the `async for` loop inside the `stream()` generator — executed once per SSE chunk.  
**Fix:** Move `import json` to the module top-level.

---

### MED-9 · Audit Events Missing `request_id` in Ingestion Loader ✅ DONE
**File:** `app/ingestion/loader.py` lines 35–61  
**Problem:** Both `AuditEvent` records in `load_document()` have `request_id=None`, making it impossible to correlate ingestion events with a specific analysis request.  
**Fix:** Add `request_id: UUID | None = None` to `load_document()` signature and pass it into every `AuditEvent(request_id=request_id, ...)` call.

---

### MED-10 · `docker-compose.yml` Uses Deprecated `version:` Key ✅ DONE
**File:** `docker/docker-compose.yml` line 1  
**Problem:** `version: "3.9"` is ignored and produces a deprecation warning in Docker Compose v2+.  
**Fix:** Remove the `version:` line entirely.

---

### MED-11 · Analysis Results Not Persisted ✅ DONE
**Files:** `app/api/routes/analysis.py`, `app/workflows/analysis_workflow.py`  
**Problem:** `AnalysisResult` objects are computed and returned but never written to storage. A lost HTTP response (timeout, network error) means the analysis is gone and must be re-run. No GET endpoint exists to retrieve past results.  
**Fix:** Persist `AnalysisResult` via `FilesystemStorage` after completion. Add `GET /api/v1/results/{request_id}` endpoint.

---

### MED-12 · CORS Overly Permissive ✅ DONE
**File:** `app/api/main.py` lines 40–47  
**Problem:** `allow_methods=["*"]` + `allow_headers=["*"]` combined with `allow_credentials=True` bypasses browser CORS protections (OWASP).  
**Fix:**
```python
allow_methods=["GET", "POST", "OPTIONS"],
allow_headers=["Content-Type", "Authorization"],
```

---

### MED-13 · No Authentication on Any API Route ⏳ DEFERRED
**Files:** `app/api/routes/analysis.py`, `app/api/routes/documents.py`  
**Problem:** All routes are publicly accessible. Anyone who can reach the server can trigger paid LLM calls.  
**Fix:** Add an API key check via FastAPI dependency injection, or document that the service must be deployed behind an authenticating reverse proxy.

---

### MED-14 · `validate_result` Has Unreachable `None` Check ✅ DONE
**File:** `app/validation/validator.py` lines 32–33  
**Problem:** `if result is None: raise ValidationError(...)` is unreachable because `result: AnalysisResult` is typed as non-optional. The `ValidationError` here also conflicts with Pydantic's `ValidationError`.  
**Fix:** Remove the `None` check (trust the type system), or use `assert result is not None` with a comment explaining why.

---

### MED-15 · `AnalysisForm` File Removal Doesn't Delete Server-Side File ✅ DONE
**File:** `ui/src/components/AnalysisForm.tsx` lines 16–32  
**Problem:** Files are uploaded immediately on selection. Clicking "Remove" deletes the file from the UI list but does not call a delete endpoint — server disk usage grows unboundedly.  
**Fix:** Add `DELETE /api/v1/documents/{document_id}` endpoint and call it in `handleRemove`.

---

## 🟢 LOW — Nice to Fix

---

### LOW-1 · Redundant `@pytest.mark.asyncio` with `asyncio_mode = "auto"` ✅ DONE
**Files:** `tests/unit/test_markitdown_converter.py` and other test files  
**Problem:** `asyncio_mode = "auto"` in `pyproject.toml` makes the decorator redundant and may produce warnings in newer pytest-asyncio.  
**Fix:** Remove all `@pytest.mark.asyncio` decorators from test functions (auto mode handles them), OR switch to `asyncio_mode = "strict"` and keep the decorators.

---

### LOW-2 · Dockerfile Doesn't Create `data/uploads/` as Non-Root User ✅ DONE
**File:** `docker/Dockerfile` line 33  
**Problem:** `RUN mkdir -p data/converted` exists but not `data/uploads`. At runtime the `analizer` user may lack permission to create it.  
**Fix:**
```dockerfile
RUN mkdir -p data/uploads data/converted && chown -R analizer:analizer data/
```
(before the `USER analizer` line)

---

### LOW-3 · `write_markdown_report` Calls `.upper()` on `StrEnum` ✅ DONE
**File:** `app/reporting/writer.py` line 32  
**Problem:** `result.analysis_type.upper()` returns a plain `str` from a `StrEnum` — works but is semantically inconsistent.  
**Fix:** Use `str(result.analysis_type).upper()`.

---

### LOW-4 · `routing/prompts.py` Is Dead Code ✅ DONE
**File:** `app/routing/prompts.py`  
**Problem:** `ROUTER_SYSTEM_PROMPT` and `ROUTER_USER_TEMPLATE` are defined but never imported or used anywhere.  
**Fix:** Either implement the LLM-assisted router and use these constants, or delete the file and track the feature in an issue.

---

### LOW-5 · `FinancialMetrics.anomalies` Needs a Typed Model ✅ DONE
**File:** `app/models/financial.py` line 40  
**Problem:** `anomalies: list[dict[str, float | str]]` is loosely typed. Dict keys `"period"` (str) and `"value"` (float) should be a typed model.  
**Fix:**
```python
class AnomalyRecord(BaseModel):
    period: str
    value: float

class FinancialMetrics(BaseModel):
    anomalies: list[AnomalyRecord] = []
```

---

### LOW-6 · Inconsistent LLM Failure Fallback Strings ✅ DONE
**Files:** `app/analyzers/universal.py` line 71, `app/analyzers/financial.py` line 63  
**Problem:** `UniversalAnalyzer` sets `summary = "Analysis unavailable due to LLM error."` while `FinancialAnalyzer` sets `narrative = "Financial narrative unavailable."` — inconsistent fallback messaging.  
**Fix:** Define shared fallback constants in `app/analyzers/base.py` and use them in both analyzers.

---

### LOW-7 · `token_count` Field Is Actually Word Count ✅ DONE
**File:** `app/chunking/chunker.py` line 68  
**Problem:** `token_count=len(chunk_text_slice.split())` computes whitespace-split word count, not actual LLM tokens. The field name is misleading.  
**Fix:** Rename to `word_count`, or implement real tokenization via `tiktoken` (already noted as a TODO in the chunker docstring).

---

### LOW-8 · Health Check Always Returns OK ✅ DONE
**File:** `app/api/routes/health.py`  
**Problem:** `GET /healthz` always returns `{"status": "ok"}` regardless of whether storage is writable or the LLM provider is reachable.  
**Fix:** Keep current endpoint as a liveness probe. Add `GET /readyz` as a readiness probe that checks: writable uploads dir, writable audit log dir, and (optionally) LLM provider ping.

---

## 🧪 Test Coverage Gaps

The following modules have **zero unit tests**. Each should have at minimum: happy path, error path, edge case.

| Module | Missing Test Scenarios |
|---|---|
| `app/audit/logger.py` | `emit()` success, `_append_sync()` I/O error |
| `app/analyzers/financial.py` | LLM error path, no-chunks path, metrics path |
| `app/analyzers/universal.py` | All `AnalysisType` variants, LLM error path |
| `app/llm/provider.py` | `complete()`, `stream()`, `local_only_mode` enforcement |
| `app/llm/prompt_templates.py` | `get_system_prompt()` and `get_user_prompt()` for each type |
| `app/ingestion/loader.py` | Success, file not found, unsupported type |
| `app/ingestion/document_loader.py` | `load_chunks()`, `load_chunks_from_path()`, converter selection |
| `app/conversion/local_converter.py` | Text file, binary file, missing file |
| `app/conversion/mcp_converter.py` | Server error, `local_only_mode=true`, success |
| `app/reporting/writer.py` | `write_markdown_report()`, `write_json_report()` |
| `app/storage/filesystem.py` | `save()`, `load()`, `exists()` |
| `app/validation/validator.py` | Empty summary, missing `request_id`, valid result |
| `app/routing/router.py` | All `AnalysisType` variants; verify `CUSTOM` is unreachable |
| `app/workflows/analysis_workflow.py` | All 5 step executors; full workflow chain |
| `app/agents/analyst_agent.py` | `run_financial_calculation()`, `analyze_document()` branches |
| `app/agents/orchestrator_agent.py` | `run_analysis_workflow()`, routing functions |
| `app/agents/reviewer_agent.py` | Invalid JSON, missing fields, valid result |
| `app/api/routes/analysis.py` | POST success, LLM error, routing error |
| `app/api/routes/documents.py` | Upload success, file too large, invalid extension |
| `app/api/routes/health.py` | GET liveness |

**Specific edge-case tests also needed:**
- `LOCAL_ONLY_MODE=true` blocks agent LLM calls (CRIT-4)
- `LOCAL_ONLY_MODE=true` blocks MCP conversion
- Chunker with `overlap >= chunk_size` raises `ValueError` (HIGH-3)
- Upload route rejects files over 100 MB before reading (CRIT-2)
- CAGR with negative `start_val` is handled gracefully (HIGH-4)
- Anomaly detection with fewer than 3 data points

---

## Priority Order for Implementation

```
CRIT-1  → rotate API key + add pre-commit hook
CRIT-2  → stream-check file size before read
HIGH-9  → add data/uploads/ to .gitignore
HIGH-7  → stop leaking exception details to clients
MED-12  → tighten CORS
CRIT-4  → enforce LOCAL_ONLY_MODE in agents
CRIT-5  → remove or safe-guard ZIP support
HIGH-1  → fix blocking I/O in mcp_converter
HIGH-2  → fix deprecated get_event_loop()
HIGH-3  → guard chunker against overlap >= chunk_size
HIGH-8  → make MCP endpoint configurable
HIGH-6  → consolidate converter factory
HIGH-10 → implement ingest_step properly
HIGH-5  → single stat() call + thread request_id
HIGH-4  → wrap CAGR in try/except
HIGH-11 → avoid double load_chunks
MED-1..3 → add audit events to workflow/converters/router/chunker
MED-4   → use FilesystemStorage for converted docs
MED-11  → persist AnalysisResult + add GET endpoint
MED-5   → make CUSTOM reachable
MED-7   → deduplicate _make_client()
MED-6   → compute rev_series once
MED-13  → add API key auth (or document proxy requirement)
MED-15  → DELETE endpoint + call on file remove
LOW-*   → address in any order
Test gaps → one module at a time, highest-risk first
```
