"""
╔══════════════════════════════════════════════════════════════════╗
║     TIME DE ESTRATÉGIA MULTIAGENTE (LangGraph + Ollama)         ║
╠══════════════════════════════════════════════════════════════════╣
║  AGENTES:                                                        ║
║  🧭 Manager      → lê a tarefa e decide quem responde           ║
║  🎤 Roteirista   → pitch, roteiro, narrativa, slogan            ║
║  🔍 Pesquisador  → dados de mercado, benchmark, tendências       ║
║  📊 Estrategista → modelo de negócio, plano, metas              ║
║  📱 Conteudista  → redes sociais, calendário, tom de voz         ║
║  📋 Crítico      → revisão objetiva e pontos de melhoria         ║
╚══════════════════════════════════════════════════════════════════╝

Requisitos:
    pip install langgraph langchain-community langchain-core ollama

Uso:
    python vertice_estrategia.py
    python vertice_estrategia.py --task "escreva um pitch de 1 minuto"
"""

import argparse
import logging
import operator
import os
import re
import time
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Annotated, TypedDict

from langchain_ollama import OllamaLLM
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph

# Configuracao
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("agentes_estrategia")

@dataclass(frozen=True)
class AppConfig:
    model: str
    temperature: float
    max_task_length: int
    timeout_seconds: int
    max_retries: int


def load_config() -> AppConfig:
    return AppConfig(
        model=os.getenv("LLM_MODEL", "llama3.1"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
        max_task_length=int(os.getenv("MAX_TASK_LENGTH", "5000")),
        timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "90")),
        max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
    )


CONFIG = load_config()
LLM_MODEL = CONFIG.model
TEMPERATURE = CONFIG.temperature
MAX_TASK_LENGTH = CONFIG.max_task_length
LLM_TIMEOUT_SECONDS = CONFIG.timeout_seconds
LLM_MAX_RETRIES = CONFIG.max_retries

llm = OllamaLLM(model=CONFIG.model, temperature=CONFIG.temperature)

ROUTES = ("roteirista", "pesquisador", "estrategista", "conteudista", "critico")
DEFAULT_ROUTE = "estrategista"

# Contexto base generico, injetado em todos os agentes.
BASE_CONTEXT = """
=== CONTEXTO BASE DO PROJETO ===

Você está apoiando um projeto de empreendedorismo/negócio/impacto.
Use linguagem clara, objetiva e prática.

Diretrizes gerais:
- Evite jargão desnecessário.
- Quando usar números, explique o raciocínio.
- Se faltar dado exato, sinalize como estimativa.
- Priorize recomendações acionáveis para as próximas semanas.
- Adapte a resposta ao nível de maturidade do projeto informado pelo usuário.

=== FIM DO CONTEXTO ===
"""


class TeamState(TypedDict):
    messages: Annotated[list, operator.add]
    task: str
    route: str
    roteirista_output: str
    pesquisador_output: str
    estrategista_output: str
    conteudista_output: str
    critico_output: str
    final_output: str


def create_initial_state(task: str) -> TeamState:
    return {
        "messages": [],
        "task": task,
        "route": "",
        "roteirista_output": "",
        "pesquisador_output": "",
        "estrategista_output": "",
        "conteudista_output": "",
        "critico_output": "",
        "final_output": "",
    }


def validate_task(task: str) -> str:
    if not task or not task.strip():
        raise ValueError("A tarefa nao pode ser vazia.")

    cleaned_task = task.strip()
    if len(cleaned_task) > MAX_TASK_LENGTH:
        raise ValueError(f"A tarefa excede o limite de {MAX_TASK_LENGTH} caracteres.")

    # Bloqueio basico para entradas obviamente maliciosas em contexto CLI.
    if re.search(r"(^|\s)(rm\s+-rf|shutdown|format\s+c:|del\s+/f\s+/s)(\s|$)", cleaned_task, flags=re.IGNORECASE):
        raise ValueError("A tarefa contem padroes potencialmente perigosos e foi bloqueada.")

    return cleaned_task


def invoke_with_retry(prompt: str, agent_name: str) -> str:
    last_error = None

    for attempt in range(1, LLM_MAX_RETRIES + 1):
        try:
            start = time.time()
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(llm.invoke, prompt)
                output = future.result(timeout=LLM_TIMEOUT_SECONDS)

            duration = time.time() - start
            logger.info("agent=%s attempt=%d status=ok duration_s=%.2f", agent_name, attempt, duration)
            return output
        except FuturesTimeoutError as exc:
            last_error = exc
            logger.warning(
                "agent=%s attempt=%d status=timeout timeout_s=%d",
                agent_name,
                attempt,
                LLM_TIMEOUT_SECONDS,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.warning("agent=%s attempt=%d status=error error=%s", agent_name, attempt, exc)

        if attempt < LLM_MAX_RETRIES:
            backoff = 2 ** (attempt - 1)
            logger.info("agent=%s next_retry_in_s=%d", agent_name, backoff)
            time.sleep(backoff)

    logger.error("agent=%s status=failed error=%s", agent_name, last_error)
    return (
        "Nao foi possivel gerar uma resposta agora. "
        "Verifique se o Ollama esta em execucao e tente novamente em instantes."
    )


def agent_manager(state: TeamState) -> TeamState:
    logger.info("manager_start")

    prompt = f"""
Você é o gerente de um time de estratégia com especialistas.
Sua função é ler a tarefa e escolher o agente certo para respondê-la.

AGENTES DISPONÍVEIS:
- roteirista   → texto para comunicação: roteiro, pitch, slogan, narrativa, copy
- pesquisador  → dados externos: mercado, benchmark, tendências, concorrentes
- estrategista → lógica de negócio: modelo, monetização, metas, plano de execução
- conteudista  → presença digital: calendário, ideias de post, tom de voz, canais
- critico      → revisão de conteúdo: pontos fortes, falhas, correções claras

TAREFA DO USUÁRIO:
{state["task"]}

Responda APENAS com uma palavra (sem pontuação, sem explicação):
roteirista | pesquisador | estrategista | conteudista | critico
"""
    raw = invoke_with_retry(prompt, "manager").strip().lower()
    route = next((r for r in ROUTES if r in raw), DEFAULT_ROUTE)

    if route == DEFAULT_ROUTE and DEFAULT_ROUTE not in raw:
        logger.warning("manager_route_fallback raw=%s fallback=estrategista", raw)
    logger.info("manager_route_selected route=%s", route)

    return {
        **state,
        "route": route,
        "messages": [HumanMessage(content=state["task"])],
    }


def agent_roteirista(state: TeamState) -> TeamState:
    logger.info("agent_start name=roteirista")

    prompt = f"""
{BASE_CONTEXT}

Você é o ROTEIRISTA, especialista em comunicação estratégica e storytelling.

SEU PAPEL:
- Transformar ideias complexas em linguagem simples e persuasiva.
- Produzir texto com foco em clareza, impacto e ação.

PRINCÍPIOS:
- Comece pelo problema humano ou de negócio.
- Mostre valor com objetividade.
- Evite frases vazias e jargão.
- Se for roteiro de vídeo, sugira blocos com tempo aproximado.

TAREFA:
{state["task"]}

Escreva agora:
"""
    output = invoke_with_retry(prompt, "roteirista")
    logger.info("agent_done name=roteirista chars=%d", len(output))

    return {
        **state,
        "roteirista_output": output,
        "messages": [AIMessage(content=f"[ROTEIRISTA]\n{output}")],
    }


def agent_pesquisador(state: TeamState) -> TeamState:
    logger.info("agent_start name=pesquisador")

    prompt = f"""
{BASE_CONTEXT}

Você é o PESQUISADOR, analista de mercado e benchmark.

SEU PAPEL:
- Fornecer dados e contexto externo que fortaleçam decisões.
- Explicar implicações práticas para o projeto.

FORMATO DE RESPOSTA:
1. DADO CENTRAL
2. CONTEXTO
3. IMPLICAÇÃO PRÁTICA
4. FONTE RECOMENDADA

Se faltar dado exato, marque como estimativa e explique o raciocínio.

TAREFA:
{state["task"]}

Produza a análise agora:
"""
    output = invoke_with_retry(prompt, "pesquisador")
    logger.info("agent_done name=pesquisador chars=%d", len(output))

    return {
        **state,
        "pesquisador_output": output,
        "messages": [AIMessage(content=f"[PESQUISADOR]\n{output}")],
    }


def agent_estrategista(state: TeamState) -> TeamState:
    logger.info("agent_start name=estrategista")

    prompt = f"""
{BASE_CONTEXT}

Você é o ESTRATEGISTA, consultor de negócios.

SEU PAPEL:
- Construir recomendações de modelo de negócio, monetização e execução.
- Priorizar o que gera impacto no curto prazo sem perder visão de médio prazo.

FERRAMENTAS:
- Business Model Canvas
- SWOT
- Priorização por impacto x esforço
- Metas e marcos por semana

COMO RESPONDER:
- Seja direto e prescritivo.
- Explique o porquê de cada recomendação.
- Em projeções, mostre o cálculo/resumo lógico.

TAREFA:
{state["task"]}

Desenvolva a estratégia agora:
"""
    output = invoke_with_retry(prompt, "estrategista")
    logger.info("agent_done name=estrategista chars=%d", len(output))

    return {
        **state,
        "estrategista_output": output,
        "messages": [AIMessage(content=f"[ESTRATEGISTA]\n{output}")],
    }


def agent_critico(state: TeamState) -> TeamState:
    logger.info("agent_start name=critico")

    prompt = f"""
{BASE_CONTEXT}

Você é o CRÍTICO, revisor editorial e estratégico.

SEU PAPEL:
- Encontrar falhas reais, riscos e lacunas.
- Sugerir correções concretas e testáveis.

FORMATO OBRIGATÓRIO:

✅ PONTOS FORTES (mínimo 2)

❌ PROBLEMAS CRÍTICOS

🔧 COMO CORRIGIR (ações específicas)

📊 NOTA: X/10 (1 frase de justificativa)

CONTEÚDO A REVISAR:
{state["task"]}

Escreva a revisão agora:
"""
    output = invoke_with_retry(prompt, "critico")
    logger.info("agent_done name=critico chars=%d", len(output))

    return {
        **state,
        "critico_output": output,
        "messages": [AIMessage(content=f"[CRÍTICO]\n{output}")],
    }


def agent_conteudista(state: TeamState) -> TeamState:
    logger.info("agent_start name=conteudista")

    prompt = f"""
{BASE_CONTEXT}

Você é o CONTEUDISTA, estrategista de presença digital.

SEU PAPEL:
- Definir plano editorial multicanal.
- Adaptar formato e tom por plataforma e público.

ENTREGÁVEIS COMUNS:
- Calendário editorial
- Ideias de post com gancho, desenvolvimento e CTA
- Tom de voz
- Bio de perfil
- Hashtags por nicho

TAREFA:
{state["task"]}

Produza agora:
"""
    output = invoke_with_retry(prompt, "conteudista")
    logger.info("agent_done name=conteudista chars=%d", len(output))

    return {
        **state,
        "conteudista_output": output,
        "messages": [AIMessage(content=f"[CONTEUDISTA]\n{output}")],
    }


def consolidate(state: TeamState) -> TeamState:
    route = state.get("route", DEFAULT_ROUTE)
    output_map = {
        "roteirista": state.get("roteirista_output", ""),
        "pesquisador": state.get("pesquisador_output", ""),
        DEFAULT_ROUTE: state.get("estrategista_output", ""),
        "conteudista": state.get("conteudista_output", ""),
        "critico": state.get("critico_output", ""),
    }
    selected_output = output_map.get(route)
    if selected_output:
        return {**state, "final_output": selected_output}

    logger.warning("consolidate_route_fallback route=%s fallback=%s", route, DEFAULT_ROUTE)
    return {**state, "final_output": output_map[DEFAULT_ROUTE]}


def route_task(state: TeamState) -> str:
    return state.get("route", DEFAULT_ROUTE)


def build_graph():
    graph = StateGraph(TeamState)

    graph.add_node("manager", agent_manager)
    graph.add_node("roteirista", agent_roteirista)
    graph.add_node("pesquisador", agent_pesquisador)
    graph.add_node("estrategista", agent_estrategista)
    graph.add_node("conteudista", agent_conteudista)
    graph.add_node("critico", agent_critico)
    graph.add_node("consolidate", consolidate)

    graph.set_entry_point("manager")

    graph.add_conditional_edges(
        "manager",
        route_task,
        {
            "roteirista": "roteirista",
            "pesquisador": "pesquisador",
            "estrategista": "estrategista",
            "conteudista": "conteudista",
            "critico": "critico",
        },
    )

    for node in ["roteirista", "pesquisador", "estrategista", "conteudista", "critico"]:
        graph.add_edge(node, "consolidate")

    graph.add_edge("consolidate", END)

    return graph.compile()


def run_team(task: str) -> str:
    app = build_graph()

    validated_task = validate_task(task)
    initial_state = create_initial_state(validated_task)

    print(f"\n{'═' * 62}")
    print("  TIME DE ESTRATÉGIA MULTIAGENTE")
    print(f"  Tarefa: {validated_task[:75]}{'...' if len(validated_task) > 75 else ''}")
    print(f"{'═' * 62}")

    result = app.invoke(initial_state)

    print(f"\n{'─' * 62}")
    print("  RESULTADO")
    print(f"{'─' * 62}\n")
    print(result["final_output"])
    print(f"\n{'═' * 62}\n")

    return result["final_output"]


EXEMPLOS = [
    "escreva um pitch de 1 minuto para este projeto",
    "quais dados de mercado devo levantar para validar a ideia?",
    "monte uma estratégia de lançamento para as próximas 3 semanas",
    "revise este rascunho: [cole seu texto aqui]",
    "crie 5 opções de slogan com no máximo 8 palavras",
    "monte calendário editorial do Instagram para o próximo mês",
    "escreva 3 ideias de post para LinkedIn",
    "faça um mini canvas do modelo de negócio",
]


def interactive_mode():
    print(
        f"""
╔══════════════════════════════════════════════════════════════╗
║       TIME DE ESTRATÉGIA MULTIAGENTE — Modo Interativo      ║
╠══════════════════════════════════════════════════════════════╣
║  Digite sua tarefa. 'sair' para encerrar.                   ║
╠══════════════════════════════════════════════════════════════╣
║  EXEMPLOS:                                                   ║"""
    )
    for ex in EXEMPLOS:
        print(f"║  → {ex[:56]:<56} ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    while True:
        task = input("\n>>> ").strip()
        if task.lower() in ("sair", "exit", "q"):
            print("\nEncerrando. Até a próxima.")
            break
        if not task:
            continue
        try:
            run_team(task)
        except ValueError as exc:
            logger.warning("task_validation_error error=%s", exc)
            print(f"\n[entrada invalida] {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Time de Estratégia Multiagente — LangGraph + Ollama")
    parser.add_argument("--task", "-t", type=str, default=None)
    args = parser.parse_args()

    if args.task:
        try:
            run_team(args.task)
        except ValueError as exc:
            logger.warning("task_validation_error error=%s", exc)
            print(f"\n[entrada invalida] {exc}")
    else:
        interactive_mode()
