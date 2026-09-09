# AGENTS.md — Contributor & Agent Guidelines for GAIA OS

Welcome to **GAIA OS** (General Autonomous Intelligent Assistant), a voice-first modular personal AI assistant runtime designed for testability, simplicity, and long-term agency.

---

## 1. Current Stable Milestone
- **Milestone:** `v0.1.0` — **Bootstrap Foundation**
- **Status:** **Frozen & Stable**.
- **Delivered Capabilities:**
  - Natural language vertical slice: `User Text → IntentInterpreter → ToolCall → Pydantic Validation → Typed Tool → SQLite Persistence → Append-Only Event Log → Response`.
  - 5 initial typed tools: `create_note`, `create_idea`, `create_task`, `list_projects`, `get_current_context`.
  - Deterministic administrative CLI (`gaia project create`, `gaia context set-project`).
  - Decoupled MCP tool adapter boundary (`gaia/mcp/adapter.py`).
  - Pluggable model providers (scripted `FakeModelProvider` for tests, `OpenAICompatibleProvider` for Ollama/vLLM/cloud, and `RuleBasedInterpreter` for offline runs).
  - Measurable intent evaluation baseline with 25 test cases (`evals/v001_intent_cases.json`).

---

## 2. Fundamental Architectural Boundaries
GAIA OS enforces a strict 6-layer separation of concerns. Do not mix these concepts:

1. **APPLICATION:** User-facing presentation (CLI REPL, single-shot invocations, administrative commands, future Gloomy desktop UI). Must contain zero business logic.
2. **HARNESS (Runtime):** Execution coordinator (`GaiaRuntime`). Manages request lifecycle, correlation IDs, execution timing, and structured logging.
3. **CONTEXT:** Situational awareness model (`ContextPacket`, `CurrentState`). Context flows proactively toward GAIA; the core does not poll or scrape.
4. **MODEL:** Statistical inference (`ModelProvider`). **The model only proposes actions via `ToolCall`**; it never constructs or persists domain entities directly.
5. **TOOLS:** Typed capabilities (`BaseTool`). Inputs are strictly validated via Pydantic schemas before domain execution.
6. **MEMORY:** Structured entities (`Project`, `Task`, `Idea`, `Note`, `Decision`) and an append-only event store with causality (`correlation_id`, `causation_id`, `actor`) in SQLite.

---

## 3. Rules Against Speculative Complexity
- **Simplicity first:** Never introduce a complex subsystem when a simpler implementation solves the requirement.
- **I/O Isolation:** Keep all I/O behind interfaces/protocols so unit tests run deterministically in-memory without external services or API keys.
- **Pure domain logic:** Separate calculation and validation from database and network operations.
- **Reuse before rebuilding:** Check existing open-source projects before building generic infrastructure, but do not add dependencies without a concrete use case.
- **No speculative abstractions:** Build only what is needed for the current milestone.

---

## 4. Quality Gates & Verification Commands
Before submitting or merging any changes, all agents must run and pass the complete verification suite:

```bash
# 1. Run unit and integration tests (must run offline and pass 100%)
pytest

# 2. Verify test coverage
pytest --cov=gaia --cov-report=term-missing

# 3. Static lint analysis (zero warnings allowed)
ruff check .

# 4. Code formatting check
ruff format --check .

# 5. Strict static type analysis
mypy gaia

# 6. Intent interpretation behavioral benchmark
python -m evals.run_evals
```

---

## 5. Branching & Contribution Policy
- **DO NOT commit directly to `main`:** The `main` branch is the canonical, production-ready, stable release branch.
- **Work on dedicated topic branches:** Every feature, bugfix, or milestone must be developed on an isolated branch and merged only after passing all quality gates.
- **Next Milestone Branch:** All upcoming voice work (Horizon 1 / v0.2) must occur on:
  ```bash
  git checkout antigravity/voice-v0.2
  ```

---

## 6. Key Documentation Links
- [README.md](README.md): Project overview, architecture summary, and quickstart guide.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): Detailed layer boundaries, data flow diagrams, and causality models.
- [docs/ROADMAP.md](docs/ROADMAP.md): Multi-horizon roadmap (v0.1 through v0.7+).
- [docs/DECISIONS.md](docs/DECISIONS.md): Architecture Decision Records (ADRs 001–007).
- [docs/OPEN_SOURCE_REUSE.md](docs/OPEN_SOURCE_REUSE.md): Analysis of Graphiti, Letta, whisper.cpp, Piper, OpenHands, BlockNote, and Microsoft Agent Framework.
