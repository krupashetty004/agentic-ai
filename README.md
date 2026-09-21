

## Overview

An AI chat system with multiple agents working together. A supervisor routes requests, search retrieves relevant documents, and summarization turns the results into a useful answer. Upload documents, ask questions, and work from one focused interface.

## Tech Stack

**Backend**
- FastAPI
- LangChain
- LangGraph workflow patterns
- Local MCP knowledge tools
- Redis
- Elasticsearch
- HuggingFace Models

**Frontend**
- Next.js 15
- TypeScript
- Tailwind CSS

## Getting Started

### Configure the backend

From the project root in PowerShell:

```powershell
Copy-Item backend\.env.example backend\.env
```

Set `HUGGINGFACE_API_KEY` and a strong local `AUTH_SECRET_KEY` in `backend\.env`.

### Optional infrastructure

Docker is optional. Use it when you need persistent Redis memory and Elasticsearch-backed indexing:

```powershell
docker compose -f podman-compose.yml up -d
```

Redis and Elasticsearch are optional. Without Docker, the app uses in-memory conversation storage and the bundled local knowledge catalog.

### Fast Docker-free start

From the project root, double-click `start-agentic-ai.bat`, or run:

```powershell
cd "D:\Documents\Agentic AI"
.\start-agentic-ai.bat
```

Do not run that command from the `frontend` directory unless you use the full path to the batch file.

### Start the backend

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000` and health status is at `http://localhost:8000/health`.

### Start the frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`, register a local account, ingest the sample catalog, and try a search or summary prompt.

### Start the MCP tools

In a third terminal:

```powershell
cd backend
python -m pip install -r requirements.txt
python mcp_server.py
```

The local MCP server exposes `list_knowledge_sources`, `search_knowledge`, and `get_source_record` for MCP-compatible clients.

## Assignment Demonstration

The system demonstrates authenticated user-agent interaction, Hugging Face model calls, custom document ingestion, MCP knowledge tools actively used by the search agent, Redis conversation memory, Elasticsearch retrieval, an explicit LangGraph `StateGraph` supervisor workflow, parallel agents, human review flags, and feedback metrics at `/api/v1/feedback/metrics`. Negative feedback changes the next routing decision to prefer grounded retrieval.

For a presentation, show this sequence: register, ingest sample data, ask a knowledge question, inspect the selected agents and retrieved source, approve or request review, then display the feedback metrics.

That's it.
