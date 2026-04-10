import pytest

import agentes_estrategia as app


def test_validate_task_empty_raises():
    with pytest.raises(ValueError) as exc_info:
        app.validate_task("   ")

    assert "vazia" in str(exc_info.value).lower()


def test_validate_task_max_length(monkeypatch):
    monkeypatch.setattr(app, "MAX_TASK_LENGTH", 5)

    with pytest.raises(ValueError) as exc_info:
        app.validate_task("abcdef")

    assert "limite" in str(exc_info.value).lower()


def test_create_initial_state_sets_expected_defaults():
    state = app.create_initial_state("minha tarefa")

    assert state["task"] == "minha tarefa"
    assert state["route"] == ""
    assert state["final_output"] == ""
    assert state["messages"] == []


def test_route_task_defaults_to_estrategista():
    assert app.route_task({"route": ""}) == "estrategista"


def test_get_support_agents_returns_route_specific_pair():
    assert app.get_support_agents("estrategista") == ("pesquisador", "conteudista")


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
        "support_summary": "",
        "final_output": "",
    }

    result = app.agent_manager(state)
    assert result["route"] == "estrategista"


def test_consolidate_falls_back_to_estrategista_when_route_unknown():
    state: app.TeamState = {
        "messages": [],
        "task": "teste",
        "route": "rota_invalida",
        "roteirista_output": "r",
        "pesquisador_output": "p",
        "estrategista_output": "e",
        "conteudista_output": "c",
        "critico_output": "x",
        "support_summary": "",
        "final_output": "",
    }

    result = app.consolidate(state)
    assert result["final_output"] == "e"


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
        "support_summary": "",
        "final_output": "",
    }

    result = app.consolidate(state)
    assert result["final_output"] == "c"


def test_support_panel_collects_complementary_outputs(monkeypatch):
    def fake_run_agent_step(agent_name, state):
        return f"{agent_name}-resposta"

    monkeypatch.setattr(app, "run_agent_step", fake_run_agent_step)

    state = app.create_initial_state("teste")
    state["route"] = "estrategista"

    result = app.support_panel(state)

    assert result["pesquisador_output"] == "pesquisador-resposta"
    assert result["conteudista_output"] == "conteudista-resposta"
    assert "PESQUISADOR" in result["support_summary"]
    assert "CONTEUDISTA" in result["support_summary"]
    assert len(result["messages"]) == 2


def test_consolidate_synthesizes_when_support_exists(monkeypatch):
    def fake_invoke(prompt, agent_name):
        if agent_name == "sintese":
            return "resposta final sintetizada"
        raise AssertionError(f"Unexpected agent: {agent_name}")

    monkeypatch.setattr(app, "invoke_with_retry", fake_invoke)

    state: app.TeamState = {
        "messages": [],
        "task": "teste",
        "route": "estrategista",
        "roteirista_output": "",
        "pesquisador_output": "apoio pesquisa",
        "estrategista_output": "resposta principal",
        "conteudista_output": "apoio conteudo",
        "critico_output": "",
        "support_summary": "[PESQUISADOR]\napoio pesquisa\n\n[CONTEUDISTA]\napoio conteudo",
        "final_output": "",
    }

    result = app.consolidate(state)
    assert result["final_output"] == "resposta final sintetizada"
