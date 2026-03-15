# MCP Chat — Advanced Topics

This project extends the [MCP Chat introduction project](https://github.com/sirinebenyedder/anthropic-mcp-gemini-version/tree/feat/mcp-integration) by applying the advanced concepts from Anthropic Academy's **Model Context Protocol: Advanced Topics** course directly into a working CLI application.

---

## Requirements

- Completion of the [MCP Chat intro project](https://github.com/sirinebenyedder/anthropic-mcp-gemini-version/tree/feat/mcp-integration)
- Python 3.9+
- Gemini API Key → [Get one here](https://aistudio.google.com/)

---

## Setup

1. Clone the repo and switch to the advanced branch:
```bash
git clone https://github.com/sirinebenyedder/anthropic-mcp-advanced-gemini-version
git checkout feat/advanced-mcp
```

2. Fill in your keys:
```bash
cp .env
```

3. Install dependencies and run:
```bash
uv venv
uv pip install -e .
uv run main.py
```

> See the [intro project README](https://github.com/sirinebenyedder/anthropic-mcp-gemini-version/tree/feat/mcp-integration) for full setup details.

---

## Course Plan

### 1. Sampling

#### 1.1 Definition

Sampling is an MCP feature that allows the **server to delegate LLM calls back to the client**. Instead of the server running its own AI model, the server sends a request to the client saying *"please process this text with your LLM"* — and the client responds using its own already-configured model.

```
Without Sampling:
Server tools → return raw data → client LLM processes it

With Sampling:
Server tools → ask client "summarize this for me"
             → client's Gemini processes it
             → result returned to server → back to user
```

#### 1.2 CLI Example

The `summarize_with_sampling` tool was added to `mcp_server.py`. 

---

### 2. Log and Progress Notifications

> 🚧 Coming soon

---

### 3. Roots

> 🚧 Coming soon

---

### 4. Transports and Communication

> 🚧 Coming soon
