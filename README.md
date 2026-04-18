# Multi-Agent Strategy Team (LangGraph + Ollama)

[Leia em Portugues (pt-BR)](README.pt-BR.md)

Python multi-agent system to support strategy, research, content planning, and critical review tasks.

## Entry points

- `agentes_estrategia.py`: primary CLI entrypoint
- `vertice_estrategia.py`: legacy compatibility wrapper

## Agents

- Manager: routes each request to the best specialist
- Scriptwriter: pitch, storytelling, scripts, and copy
- Researcher: market data, benchmark, and external context
- Strategist: business model, goals, and execution plan
- Content Strategist: editorial calendar, post ideas, brand voice
- Critic: objective review with concrete improvement points

## Requirements

- Python 3.10 to 3.13 (recommended)
- Ollama installed and running locally
- Ollama model available (default in script: `llama3.1`)

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Interactive mode:

```bash
python agentes_estrategia.py
```

Single task mode:

```bash
python agentes_estrategia.py --task "write a 1-minute pitch"
# or
python agentes_estrategia.py -t "write a 1-minute pitch"
```

## Configuration

The app reads the following environment variables:

- `LLM_MODEL` (default: `llama3.1`)
- `LLM_TEMPERATURE` (default: `0.3`)
- `MAX_TASK_LENGTH` (default: `5000`)
- `LLM_TIMEOUT_SECONDS` (default: `90`)
- `LLM_MAX_RETRIES` (default: `3`)
- `LOG_LEVEL` (default: `INFO`)

## Notes

- The project was cleaned for generic/public use, with no hardcoded business context.
- The app now includes retry with exponential backoff and timeout protection for LLM calls.
- Task input is validated before execution.
- The app now runs complementary support agents in parallel and synthesizes a final answer.
- `vertice_estrategia.py` is kept as a compatibility entrypoint.
- On Python 3.14/3.12+, some LangChain ecosystem packages may emit warnings.

## Testing

Run the local test suite with:

```bash
python -m pytest tests -q
```
