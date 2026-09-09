# Architecture Decision Records (ADRs)

## ADR-001: Technology Stack & Language Selection (Python 3.13 + Pydantic v2 + uv)
- **Context:** GAIA OS is a long-term personal AI assistant project. Its roadmap involves local machine learning inference (whisper.cpp, Piper), potential future fine-tuning (PEFT, TRL, lm-evaluation-harness), knowledge graph experiments (Graphiti), and fast iteration.
- **Decision:** Use Python 3.13+ with Pydantic v2 for data modeling and `uv` (PEP 621 `pyproject.toml`) for high-performance dependency management.
- **Consequences:**
  - *Positive:* Native alignment with Python's AI/ML ecosystem, fast dependency resolution via `uv`, robust type contracts via Pydantic v2.
  - *Negative:* Frontend presentation (Gloomy) will require a separate TypeScript/React application later.

---

## ADR-002: Persistence Engine & Explicit SQL Migrations (aiosqlite)
- **Context:** GAIA requires zero-infrastructure, local-first persistence for projects, tasks, notes, ideas, decisions, and events in v0.1.
- **Decision:** Use SQLite via `aiosqlite` with explicit, version-tracked SQL migrations (`001_initial.sql`), avoiding heavy ORMs like SQLAlchemy or SQLModel in v0.1.
- **Consequences:**
  - *Positive:* Zero server setup, lightning-fast test suites (in-memory `:memory:` databases in <0.2s), inspectable `.sql` files, foreign-key safety.
  - *Negative:* SQL queries and row mappings are maintained manually in `SqliteRepository`.

---

## ADR-003: Direct Append-Only Event Recording Over Speculative EventBus
- **Context:** In v0.1, the only consumer of events is the SQLite event log. Introducing an asynchronous pub/sub event bus would be speculative overhead without current justification.
- **Decision:** Use a direct `EventRecorder.record()` call writing to `EventRepository.append_event()`. The API signature is designed with causality metadata (`correlation_id`, `causation_id`, `actor`) so an EventBus can be introduced seamlessly when multiple consumers (Gloomy, Experience Engine, Teacher) emerge.
- **Consequences:**
  - *Positive:* Simple, deterministic execution; zero asynchronous event loss or concurrency bugs in v0.1.
  - *Negative:* All subscribers must be explicitly wired when multiple consumers are added in future milestones.

---

## ADR-004: Decoupling ModelProvider from IntentInterpreter
- **Context:** LLM providers frequently change (Ollama, local vLLM, OpenAI, Groq, Anthropic), and future GAIA versions may use fine-tuned student models or deterministic routing without changing low-level network client logic.
- **Decision:** Separate `ModelProvider` (handles network requests, headers, token completions) from `IntentInterpreter` (receives user text and tool schemas, interacts with `ModelProvider`, returns `ToolCall` or `ConversationalResponse`).
- **Consequences:**
  - *Positive:* Zero coupling between prompt formatting, intent decisions, and network transport.
  - *Negative:* Requires an extra translation step between raw completions and domain tool calls.

---

## ADR-005: Model Context Protocol (MCP) as an External Adapter Boundary
- **Context:** MCP is a valuable open protocol for exposing tools and resources to external agents. However, coupling GAIA Core's internal tool architecture directly to third-party MCP SDKs would create a vendor/framework lock-in.
- **Decision:** Define GAIA tools using native typed Pydantic contracts (`BaseTool`). Provide `McpToolAdapter` at the boundary to translate GAIA tools to/from MCP tool schemas and call formats.
- **Consequences:**
  - *Positive:* GAIA Core remains 100% self-contained and testable without MCP dependencies. MCP clients can consume GAIA tools without friction.
  - *Negative:* Translation logic must be maintained in `gaia/mcp/adapter.py`.

---

## ADR-006: Dual-Mode CLI with Deterministic Administrative Operations
- **Context:** Users interact with GAIA both in quick shell commands and interactive sessions. Furthermore, initial setup (e.g. creating projects, setting active state) should not depend on LLM interpretation.
- **Decision:** Implement dual-mode CLI with Click and Rich. Natural language queries can be executed in single-shot mode (`python -m gaia.cli "<query>"`) or in an interactive REPL (`python -m gaia.cli`). Deterministic administrative operations (`gaia project create`, `gaia context set-project`) bypass the LLM and call `GaiaAdminService` directly.
- **Consequences:**
  - *Positive:* Guaranteed reliability for administrative tasks; flexible developer workflow.
  - *Negative:* CLI router must distinguish administrative subcommands from natural language queries (implemented via `NaturalLanguageGroup`).

---

## ADR-007: Scripted Fake Model Provider for Deterministic Unit Testing
- **Context:** Automated tests must be fast, offline, and deterministic. Testing should never depend on random LLM outputs, API keys, or fuzzy keyword matching.
- **Decision:** Implement `FakeModelProvider` with scripted response queues (`responses=[ToolCall(...)]`). All unit and integration tests use `FakeModelProvider` or the offline `RuleBasedInterpreter`.
- **Consequences:**
  - *Positive:* 100% deterministic, reproducible tests running in hundreds of milliseconds without API keys.
  - *Negative:* Tests must explicitly specify expected model tool proposals.
