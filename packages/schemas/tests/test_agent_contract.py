"""Тесты моделей контракта агентов."""

import pytest
from pydantic import ValidationError

from worldsim_schemas import AgentManifest, AgentPhase, AgentRegistryFile, ModelTier


# ---------------------------------------------------------------------------
# AgentPhase
# ---------------------------------------------------------------------------


def test_agent_phase_values():
    expected = {
        "world_init", "location_detail", "npc_respond",
        "world_update", "progression_update", "canon_validate", "scene_render",
    }
    assert {p.value for p in AgentPhase} == expected


def test_agent_phase_ordering():
    phases = list(AgentPhase)
    assert phases[0] == AgentPhase.WORLD_INIT
    assert phases[-1] == AgentPhase.SCENE_RENDER


# ---------------------------------------------------------------------------
# AgentManifest
# ---------------------------------------------------------------------------


def test_manifest_minimal():
    m = AgentManifest(
        name="world-builder.turn",
        package="worldsim_world_builder",
        entrypoint="run_turn_update",
        phase=AgentPhase.WORLD_UPDATE,
    )
    assert m.version == "0.1.0"
    assert m.optional is False
    assert m.model_tier == "default"
    assert m.description == ""


def test_manifest_full():
    m = AgentManifest(
        name="world-builder.init",
        package="worldsim_world_builder",
        entrypoint="run_world_init",
        phase=AgentPhase.WORLD_INIT,
        version="0.2.0",
        optional=True,
        model_tier="heavy",
        description="Инициализация мира.",
    )
    assert m.optional is True
    assert m.model_tier == "heavy"
    assert m.version == "0.2.0"


def test_manifest_invalid_phase():
    with pytest.raises(ValidationError):
        AgentManifest(
            name="x",
            package="x",
            entrypoint="run",
            phase="nonexistent_phase",
        )


def test_manifest_invalid_model_tier():
    with pytest.raises(ValidationError):
        AgentManifest(
            name="x",
            package="x",
            entrypoint="run",
            phase=AgentPhase.SCENE_RENDER,
            model_tier="ultra",
        )


def test_manifest_roundtrip():
    m = AgentManifest(
        name="canon-keeper.validate",
        package="worldsim_canon_keeper",
        entrypoint="validate",
        phase=AgentPhase.CANON_VALIDATE,
        model_tier="heavy",
        description="Проверка консистентности.",
    )
    assert AgentManifest.model_validate(m.model_dump()) == m


def test_manifest_json_roundtrip():
    m = AgentManifest(
        name="scene-master.render",
        package="worldsim_scene_master",
        entrypoint="run",
        phase=AgentPhase.SCENE_RENDER,
    )
    assert AgentManifest.model_validate_json(m.model_dump_json()) == m


# ---------------------------------------------------------------------------
# AgentRegistryFile
# ---------------------------------------------------------------------------


def test_registry_empty():
    r = AgentRegistryFile(agents=[])
    assert r.schema_version == "0.1.0"
    assert r.agents == []


def test_registry_with_agents():
    manifests = [
        AgentManifest(
            name=f"agent-{i}.run",
            package=f"worldsim_agent_{i}",
            entrypoint="run",
            phase=phase,
        )
        for i, phase in enumerate(AgentPhase)
    ]
    r = AgentRegistryFile(agents=manifests)
    assert len(r.agents) == len(list(AgentPhase))


def test_registry_roundtrip():
    r = AgentRegistryFile(
        schema_version="0.1.0",
        agents=[
            AgentManifest(
                name="world-builder.init",
                package="worldsim_world_builder",
                entrypoint="run_world_init",
                phase=AgentPhase.WORLD_INIT,
            ),
            AgentManifest(
                name="scene-master.render",
                package="worldsim_scene_master",
                entrypoint="run",
                phase=AgentPhase.SCENE_RENDER,
            ),
        ],
    )
    restored = AgentRegistryFile.model_validate(r.model_dump())
    assert restored == r
    assert restored.agents[0].name == "world-builder.init"


def test_registry_json_roundtrip():
    r = AgentRegistryFile(
        agents=[
            AgentManifest(
                name="npc-mind.respond",
                package="worldsim_npc_mind",
                entrypoint="run",
                phase=AgentPhase.NPC_RESPOND,
                optional=True,
            )
        ]
    )
    assert AgentRegistryFile.model_validate_json(r.model_dump_json()) == r


# ---------------------------------------------------------------------------
# ModelTier (literal type guard)
# ---------------------------------------------------------------------------


def test_model_tier_valid_values():
    for tier in ("default", "heavy"):
        m = AgentManifest(
            name="x",
            package="x",
            entrypoint="run",
            phase=AgentPhase.WORLD_UPDATE,
            model_tier=tier,
        )
        assert m.model_tier == tier
