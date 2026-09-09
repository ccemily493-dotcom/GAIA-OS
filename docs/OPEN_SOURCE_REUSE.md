# Open-Source Technology Reuse Analysis

This document evaluates candidate open-source frameworks and libraries identified in the GAIA OS product vision.

Per GAIA's core development philosophy:
> **"Reuse before rebuilding, but never integrate a dependency merely because it exists. Every dependency must solve a concrete GAIA requirement."**

---

## Evaluation Matrix Summary

| Project | Category | License | Maintenance Status | Recommendation | GAIA Target Milestone | Necessity |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Graphiti** | Temporal Knowledge Graph | Apache 2.0 | Active (Zep team) | **Study & Adapt** | v0.4 (Personal World Model) | Medium |
| **Letta** (MemGPT) | Stateful Memory / Context | Apache 2.0 | High activity | **Study** | v0.3 (Memory Subsystem) | Medium |
| **Microsoft Agent Framework** | Workflow / Multi-Agent | MIT / Apache 2.0 | Active | **Study (Do not adopt)** | v0.5 (Agent Bridge) | Low |
| **OpenHands** | Autonomous Software Dev | MIT | Very active | **Study & Connect via MCP** | v0.5 (Agent Bridge) | Medium |
| **BlockNote** | Rich Block-based Editor | MPL 2.0 | Active | **Integrate** | v0.6 (Gloomy UI) | High |
| **whisper.cpp** | Local Speech-to-Text | MIT | Highly active / mature | **Integrate** | v0.2 (Voice Ingress) | High |
| **Piper** | Local Fast Neural TTS | MIT | Active (rhasspy) | **Integrate** | v0.2 (Voice Egress) | High |

---

## Detailed Analyses

### 1. Graphiti (Zep)
- **Problem it could solve:** Dynamic relationship tracking, entity extraction, and temporal knowledge graphs. Unlike static vector stores, Graphiti creates edge-weighted entity graphs that evolve over time as new information arrives.
- **Recommendation:** **Study & Adapt concepts (Do not integrate directly in v0.1/v0.2)**.
- **License:** Apache 2.0.
- **Coupling Risk:** **High**. Graphiti introduces external graph database requirements (Neo4j / specialized stores) and its own LLM extraction pipeline. Embedding it directly into GAIA Core would make GAIA dependent on a heavyweight graph runtime.
- **Maintenance Status:** Actively maintained by the Zep AI team.
- **Is it actually necessary now?** No. GAIA v0.1 requires only relational entity linking in SQLite (`Project`, `Task`, `Note`, `Idea`). In v0.4, we will assess whether an adapted SQLite-based adjacency/graph model suffices before pulling in a full graph database.
- **Relevant Milestone:** **v0.4 (Personal World Model)**.

---

### 2. Letta (formerly MemGPT)
- **Problem it could solve:** Long-term hierarchical memory, memory paging (core memory vs. archival memory), and agent state persistence across conversation resets.
- **Recommendation:** **Study**.
- **License:** Apache 2.0.
- **Coupling Risk:** **High**. Letta is an opinionated, full-stack agent server platform with its own database schemas, REST APIs, and client runtimes. Wrapping GAIA around Letta would violate GAIA's independence and architectural autonomy.
- **Maintenance Status:** High community and venture-backed activity.
- **Is it actually necessary now?** No. GAIA's memory model is designed around explicit domain entities (`Note`, `Idea`, `Decision`) and append-only event streams. However, Letta's conceptual model of tiered memory (in-context working memory vs. persistent archival memory) provides valuable design patterns for GAIA's Context Fabric.
- **Relevant Milestone:** **v0.3 (Memory Subsystem)**.

---

### 3. Microsoft Agent Framework (Semantic Kernel / AutoGen / MAF)
- **Problem it could solve:** Multi-agent coordination, conversational loops, and task routing.
- **Recommendation:** **Study (Do not adopt as a dependency)**.
- **License:** MIT / Apache 2.0.
- **Coupling Risk:** **Critical**. Frameworks like AutoGen or Semantic Kernel impose heavy abstractions, complex callback patterns, and large dependency trees that obscure simple control flow and break testability.
- **Maintenance Status:** Active development by Microsoft.
- **Is it actually necessary now?** No. GAIA explicitly rejects giant autonomous agent loops in early milestones. Single-turn, deterministic intent interpretation via typed tools provides strict testability, auditability, and speed.
- **Relevant Milestone:** **v0.5 (Agent Bridge)**.

---

### 4. OpenHands (formerly OpenDevin)
- **Problem it could solve:** Coordinating complex software engineering tasks, sandboxed code execution, and autonomous repo modification.
- **Recommendation:** **Study & Connect via MCP / Agent Bridge**.
- **License:** MIT.
- **Coupling Risk:** **Moderate (if treated as an external service); Extreme (if integrated internally)**.
- **Maintenance Status:** Very high open-source momentum.
- **Is it actually necessary now?** No. In GAIA v0.1–v0.4, GAIA acts as the personal orchestrator, note-taker, and context provider. When GAIA interacts with coding agents (Codex, OpenHands, Antigravity) in Milestone v0.5, it should do so via external protocol boundaries (MCP or dedicated API bridges), keeping GAIA's core clean.
- **Relevant Milestone:** **v0.5 (Agent Bridge)**.

---

### 5. BlockNote
- **Problem it could solve:** Notion-style block-based rich text editor for GAIA's visual workspace (Gloomy).
- **Recommendation:** **Integrate directly into Gloomy frontend**.
- **License:** MPL 2.0 (Mozilla Public License 2.0 — compatible with proprietary or separate core runtimes as long as modifications to BlockNote source are disclosed).
- **Coupling Risk:** **Low**. BlockNote is a client-side TypeScript/React UI component built on Prosemirror. It lives entirely in the frontend presentation layer and never touches GAIA Core.
- **Maintenance Status:** Active, well-documented, widely adopted for modern block-editor interfaces.
- **Is it actually necessary now?** No. Gloomy UI is deferred to Milestone v0.6. When Gloomy is built, BlockNote is the leading candidate for markdown/block page editing.
- **Relevant Milestone:** **v0.6 (Gloomy Visual Workspace)**.

---

### 6. whisper.cpp (Georgi Gerganov)
- **Problem it could solve:** High-performance, low-latency, zero-cloud-dependency local Speech-to-Text (STT) inference on CPU and GPU.
- **Recommendation:** **Integrate as the default local STT engine**.
- **License:** MIT.
- **Coupling Risk:** **Low**. Can be invoked via lightweight C-bindings (`pywhispercpp` or `ctypes`) or as a local sidecar subprocess communicating over a stream/socket.
- **Maintenance Status:** Highly mature, optimized for Apple Silicon, AVX2, and CUDA.
- **Is it actually necessary now?** No in v0.1 (text-first vertical slice); **Essential for v0.2** (Voice milestone).
- **Relevant Milestone:** **v0.2 (Voice Ingress)**.

---

### 7. Piper (rhasspy)
- **Problem it could solve:** Fast, local, high-quality neural Text-to-Speech (TTS) optimized for Raspberry Pi and desktop hardware with zero cloud dependencies.
- **Recommendation:** **Integrate as the default local TTS engine**.
- **License:** MIT.
- **Coupling Risk:** **Low**. Provides a standalone binary and simple Python wrapper that converts text into raw audio streams with sub-100ms first-chunk latency.
- **Maintenance Status:** Active, widely used in local home automation and voice assistant ecosystems.
- **Is it actually necessary now?** No in v0.1; **Essential for v0.2** (Voice milestone).
- **Relevant Milestone:** **v0.2 (Voice Egress)**.
