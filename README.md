# GAIA OS — Personal AI Assistant Runtime

> **GAIA (General Autonomous Intelligent Assistant)** is a voice-first personal AI assistant runtime designed for modularity, testability, and long-term personal agency. Inspired conceptually by JARVIS, but grounded in realistic, testability-first engineering.

---

## 1. What GAIA Is
- **A local-first, modular assistant runtime:** Built with strict boundaries between domain logic, persistence, inference models, and presentation.
- **An append-only experiential system:** Every interaction, tool invocation, and state modification is recorded with causality (`correlation_id`, `causation_id`, `actor`) for auditing and future machine learning.
- **A tool-driven orchestrator:** The LLM proposes typed tool calls; deterministic software validates inputs and performs operations.
- **An extensible foundation:** Engineered so that model providers (Ollama, OpenAI), persistence engines, speech systems, and agent bridges can be replaced without rewriting GAIA Core.

---

## 2. What GAIA Is NOT (Non-Goals for v0.1)
- **Not a giant autonomous loop:** GAIA does not run uncontrolled autonomous agent loops that burn tokens or perform uncontrolled operations.
- **Not a full desktop UI yet:** The visual workspace (Gloomy) is planned for Horizon 5.
- **Not a cloud-dependent SaaS:** GAIA is designed to run locally on your own machine.
- **Not a continuous microphone wiretap:** Continuous hotword listening and audio streaming are scheduled for Horizon 1 (v0.2).

---

## 3. Current Capabilities (Milestone v0.1)
- **Natural Language Vertical Slice:**
  `USER TEXT → IntentInterpreter → ModelProvider → ToolCall → Pydantic Validation → Tool Execution → SQLite Persistence → Append-Only Event Log → Formatted Response`
- **Initial Typed Tools:**
  1. `create_note`: Save persistent notes, documentation, and tags.
  2. `create_idea`: Record unrefined concepts and thoughts.
  3. `create_task`: Create actionable tasks with priority and status.
  4. `list_projects`: Inspect existing projects and filter by status.
  5. `get_current_context`: Retrieve active project, active task, and recent context packets.
- **Deterministic Administrative CLI:**
  - Create and list projects outside of the LLM pipeline.
  - Manually configure active project and task in `CurrentState`.
- **Model Context Protocol (MCP) Adapter Boundary:**
  - Standard MCP tool schema generation and execution adapter.
- **Measurable Intent Baseline:**
  - 25-case evaluation dataset in `evals/v001_intent_cases.json` with an automated benchmark runner (`python -m evals.run_evals`).

---

## 4. Project Status
- **Current Milestone:** **v0.1 — Bootstrap Foundation (Complete)**
- **Next Milestone:** **v0.2 — Voice-First Layer (`whisper.cpp` + `Piper`)**
- See [docs/ROADMAP.md](docs/ROADMAP.md) for the complete multi-horizon roadmap.
- See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for architectural layers and data flows.
- See [docs/DECISIONS.md](docs/DECISIONS.md) for Architecture Decision Records (ADRs).
- See [docs/OPEN_SOURCE_REUSE.md](docs/OPEN_SOURCE_REUSE.md) for open-source evaluation of Graphiti, Letta, whisper.cpp, Piper, etc.

---

## 5. Quick Start & How to Run

### Prerequisites
- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (recommended) or `pip`

### Installation
```bash
# Clone the repository and enter directory
cd GAIA-OS

# Create virtual environment and install dependencies
uv venv
.venv\Scripts\activate   # Windows (.venv/bin/activate on Linux/macOS)
uv pip install -e ".[dev]"
```

### Interactive REPL Shell
Launch the interactive GAIA shell:
```bash
python -m gaia.cli
# or
gaia
```

Inside the REPL:
```text
gaia (None)> create note Architecture with content I/O isolation is non-negotiable
✓ [create_note] Note 'Architecture' created successfully.

gaia (None)> create task Build whisper.cpp integration [high]
✓ [create_task] Task 'Build whisper.cpp integration' created successfully.

gaia (None)> get current context
✓ [get_current_context] Current context retrieved successfully.

gaia (None)> exit
```

### Single-Shot Commands
Run single-shot natural language commands directly from your terminal:
```bash
python -m gaia.cli "create idea Neural voice synthesis with Piper"
python -m gaia.cli "list projects"
```

### Administrative Commands (Deterministic, Non-AI)
Create projects and set working state directly:
```bash
# Create project
python -m gaia.cli project create "Gloomy UI" --description "Visual block canvas"

# List projects
python -m gaia.cli project list

# Set active working project
python -m gaia.cli context set-project <project-id>

# Inspect current context
python -m gaia.cli context show
```

### Running Tests
Execute the full test suite with fast, deterministic in-memory fixtures:
```bash
pytest
```

Run test coverage:
```bash
pytest --cov=gaia --cov-report=term-missing
```

### Running Intent Evaluation Baseline
Evaluate intent interpretation accuracy against the 25-case baseline:
```bash
python -m evals.run_evals
```

---

## 6. License
MIT License.
