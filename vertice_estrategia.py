"""
Compatibilidade: este arquivo foi mantido para quem ja usava o nome antigo.

Use preferencialmente:
    python agentes_estrategia.py
"""

from agentes_estrategia import interactive_mode, run_team


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Time de Estrategia Multiagente — LangGraph + Ollama")
    parser.add_argument("--task", "-t", type=str, default=None)
    args = parser.parse_args()

    if args.task:
        run_team(args.task)
    else:
        interactive_mode()
