# GAIA OS — Multi-Horizon Roadmap

This document outlines the progressive evolution of GAIA OS from the v0.1 bootstrap foundation to a voice-first, learning-capable personal AI operating system.

---

## Horizon 0: Bootstrap Foundation (Milestone v0.1) — **COMPLETED**
**Goal:** Prove the foundational vertical slice with zero complexity bloat.
- [x] Python 3.13 + `pydantic` v2 + `uv` toolchain.
- [x] Core domain entities: `Project`, `Task`, `Idea`, `Note`, `Decision`.
- [x] Initial ContextPacket and CurrentState preparation schemas.
- [x] SQLite persistence via `aiosqlite` with transactional SQL migration runner.
- [x] Append-only event store with causality (`correlation_id`, `causation_id`, `actor`).
- [x] Typed tool interface (`BaseTool`) with 5 core tools (`create_note`, `create_idea`, `create_task`, `list_projects`, `get_current_context`).
- [x] Decoupled Model Context Protocol (MCP) tool adapter.
- [x] Pluggable ModelProvider abstraction (`FakeModelProvider`, `OpenAICompatibleProvider`, `RuleBasedInterpreter`).
- [x] Dual-mode CLI (Single-shot natural language query, rich REPL, non-AI admin commands).
- [x] Initial intent evaluation dataset (`evals/v001_intent_cases.json`) and benchmark runner.
- [x] Comprehensive architecture, open-source reuse, and ADR documentation.

---

## Horizon 1: Voice-First Layer (Milestone v0.2)
**Goal:** Enable low-latency, fully local voice interaction.
- [ ] **Speech-to-Text (STT):** Local integration of `whisper.cpp` (quantized models, streaming audio transcription, VAD/Voice Activity Detection).
- [ ] **Text-to-Speech (TTS):** Local integration of `Piper` (neural low-latency voice synthesis, streaming audio playback).
- [ ] **Voice Harness:** Push-to-talk CLI and audio session manager.
- [ ] **Voice Events:** `VOICE_RECORDING_STARTED`, `VOICE_TRANSCRIBED`, `AUDIO_PLAYBACK_COMPLETED`.

---

## Horizon 2: Context Fabric & Deep Memory (Milestone v0.3)
**Goal:** Enable proactive context streaming and long-term memory retrieval.
- [ ] **Context Producers:** Lightweight adapters for active shell, active git repository, and editor focus.
- [ ] **Context Ranking & Token Budgeting:** Dynamic context compiler assembling the highest-priority packets within prompt budget constraints.
- [ ] **Hybrid Search:** Embedding generation and FTS5 (full-text search) for Notes, Ideas, and Decisions.
- [ ] **Letta-Inspired Working Memory:** Paged working memory vs. archival memory distinction.

---

## Horizon 3: Personal World Model (Milestone v0.4)
**Goal:** Maintain an accurate real-time understanding of projects and user activity.
- [ ] **World Model State:** Automated desktop observation (active window title, active project detection).
- [ ] **Graphiti-Inspired Relationship Graph:** Temporal entity relationships (linking tasks to decisions, projects to notes).
- [ ] **Project State Tracking:** Automated progress indicators and activity recency.

---

## Horizon 4: Agent Bridge (Milestone v0.5)
**Goal:** Coordinate external coding agents and background specialists.
- [ ] **MCP Client & Server:** Two-way MCP communication allowing GAIA to drive external MCP servers and be driven by external agents.
- [ ] **Coding Agent Dispatcher:** Bridging tasks to Codex, Antigravity, and OpenHands.
- [ ] **Agent Event Stream:** `AGENT_TASK_SENT`, `AGENT_TASK_PROGRESS`, `AGENT_TASK_COMPLETED`.

---

## Horizon 5: Gloomy Visual Knowledge Workspace (Milestone v0.6)
**Goal:** Provide an intuitive, visual workspace for notes, pages, and projects.
- [ ] **BlockNote Integration:** Notion-style rich block editor for notes and project briefs.
- [ ] **Visual Knowledge Canvas:** Interactive relationship graph and board view of tasks/ideas.
- [ ] **Real-time Sync:** Local WebSocket/IPC synchronization between GAIA Core runtime and Gloomy desktop app.

---

## Horizon 6: Experience Engine & Continuous Learning (Milestone v0.7+)
**Goal:** Learn systematically from past successes, failures, and user corrections.
- [ ] **Experience Engine:** Recording tuples of `(State Before, Action, Predicted Outcome, Actual Outcome, Discrepancy, Lesson)`.
- [ ] **Teacher / Student Architecture:**
  - Teacher: Powerful offline model analyzes event logs and extracts synthetic training datasets.
  - Student: Lightweight local models fine-tuned via Hugging Face PEFT/TRL.
  - Evaluation Harness: Rigorous regression testing using `lm-evaluation-harness` before promoting candidate student adapters.
