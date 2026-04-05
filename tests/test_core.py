import agentes_estrategia as app


def test_validate_task_empty_raises():
    try:
        app.validate_task("   ")
        assert False, "Expected ValueError for empty task"
    except ValueError as exc:
        assert "vazia" in str(exc).lower()


def test_validate_task_max_length(monkeypatch):
    monkeypatch.setattr(app, "MAX_TASK_LENGTH", 5)

    try:
        app.validate_task("abcdef")
        assert False, "Expected ValueError for max length"
    except ValueError as exc:
        assert "limite" in str(exc).lower()


def test_manager_fallback_to_estrategista(monkeypatch):
    monkeypatch.setattr(app, "invoke_with_retry", lambda prompt, agent_name: "unknown_agent")

    state: app.TeamState = {
        "messages": [],
        "task": "teste",
        "route": "",
        "roteirista_output": "",
        "pesquisador_output": "",
        "estrategista_output": "",
        "conteudista_output": "",
        "critico_output": "",
        "final_output": "",
    }

    result = app.agent_manager(state)
    assert result["route"] == "estrategista"


def test_consolidate_uses_route_output():
    state: app.TeamState = {
        "messages": [],
        "task": "teste",
        "route": "conteudista",
        "roteirista_output": "r",
        "pesquisador_output": "p",
        "estrategista_output": "e",
        "conteudista_output": "c",
        "critico_output": "x",
        "final_output": "",
    }

    result = app.consolidate(state)
    assert result["final_output"] == "c"
