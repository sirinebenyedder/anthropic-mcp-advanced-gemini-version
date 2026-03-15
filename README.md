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

### 1.2 CLI Example: Document Summarization

#### 1. Input (`research.txt`)
```text
The condenser tower project began in January 2023 with an initial budget of $2.4 million.
    The engineering team, led by Angela Smith P.E., conducted a full structural assessment over 
    a period of 6 months. The assessment revealed significant corrosion on levels 3 through 7,
    particularly around the cooling fins and water distribution system. Temperature readings 
    showed inconsistencies of up to 15 degrees Celsius between the north and south faces.
    Water flow rates were measured at 340 liters per minute, below the required 400 liters per minute.
    The financial impact of delayed maintenance was estimated at $180,000 per month in lost efficiency.
    Recommended repairs include full replacement of cooling fins on levels 3-5, recalibration of 
    the water distribution valves, and installation of new temperature monitoring sensors on all 8 levels.
    Total repair cost is estimated at $890,000 with a projected completion date of March 2024.
    Upon completion, the tower is expected to return to 98% operational efficiency.
```
#### 2. Output

---

### 2. Log and Progress Notifications

> 🚧 Coming soon

---

### 3. Roots

> 🚧 Coming soon

---

### 4. Transports and Communication

> 🚧 Coming soon
