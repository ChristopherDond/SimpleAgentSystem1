# Time de Estrategia Multiagente (LangGraph + Ollama)

[Read this in English](README.md)

Sistema multiagente em Python para apoiar tarefas de estrategia, pesquisa, conteudo e revisao critica.

## Agentes

- Manager: roteia cada tarefa para o especialista mais adequado
- Roteirista: pitch, storytelling, roteiros e copy
- Pesquisador: dados de mercado, benchmark e contexto externo
- Estrategista: modelo de negocio, metas e plano de execucao
- Conteudista: calendario editorial, ideias de post e tom de voz
- Critico: revisao objetiva com melhorias concretas

## Requisitos

- Python 3.10 a 3.13 (recomendado)
- Ollama instalado e rodando localmente
- Modelo no Ollama disponivel (padrao no script: `llama3.1`)

## Instalacao

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

Modo interativo:

```bash
python agentes_estrategia.py
```

Modo tarefa unica:

```bash
python agentes_estrategia.py --task "escreva um pitch de 1 minuto"
```

## Observacoes

- O projeto foi limpo para uso generico/publico, sem contexto de negocio fixo.
- Para trocar modelo e comportamento de execucao, use variaveis de ambiente:
	- `LLM_MODEL` (padrao: `llama3.1`)
	- `LLM_TEMPERATURE` (padrao: `0.3`)
	- `LLM_TIMEOUT_SECONDS` (padrao: `90`)
	- `LLM_MAX_RETRIES` (padrao: `3`)
	- `MAX_TASK_LENGTH` (padrao: `5000`)
	- `LOG_LEVEL` (padrao: `INFO`)
- O app agora inclui retry com backoff exponencial e protecao de timeout nas chamadas ao LLM.
- A tarefa de entrada agora passa por validacao antes da execucao.
- `vertice_estrategia.py` foi mantido como entrypoint de compatibilidade.
- Em Python 3.14+, algumas bibliotecas do ecossistema LangChain podem emitir warnings.
