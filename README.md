# Multi-Agent Strategy Team (LangGraph + Ollama)

[Leia em Portugues (pt-BR)](README.pt-BR.md)

Python multi-agent system to support strategy, research, content planning, and critical review tasks.

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
```

## Notes

- The project was cleaned for generic/public use, with no hardcoded business context.
- To switch models, change `LLM_MODEL` in the main script.
- `vertice_estrategia.py` is kept as a compatibility entrypoint.
- On Python 3.14+, some LangChain ecosystem packages may emit warnings.
