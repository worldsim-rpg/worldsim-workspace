"""Валидация pydantic-моделей канона."""

import pytest
from pydantic import ValidationError

from worldsim_schemas import (
    Arc,
    ArcStage,
    Character,
    Condition,
    GameSettings,
    Goal,
    Intent,
    Location,
    PatchOp,
    PlayerProgression,
    TurnPatch,
    WorldInspiration,
    WorldMeta,
)


def test_location_minimal():
    loc = Location(id="loc_docks", name="Доки", short_description="Соль, верёвки, тихий прибой.")
    assert loc.connected_to == []
    assert loc.discovered is False
    assert loc.visited is False
    assert loc.full_description is None


def test_character_minimal_npc():
    npc = Character(id="npc_mira", name="Мира", location_id="loc_docks")
    assert npc.is_player is False
    assert npc.alive is True
    assert npc.condition is Condition.OK
    assert npc.attitude_to_player == 0.0


def test_attitude_clamped():
    with pytest.raises(ValidationError):
        Character(id="npc_x", name="X", location_id="loc_x", attitude_to_player=2.0)


def test_goal_priority_clamped():
    with pytest.raises(ValidationError):
        Goal(text="go", priority=1.5)


def test_arc_default_stage():
    arc = Arc(id="arc_1", title="Sealed Crate")
    assert arc.stage is ArcStage.HOOK
    assert arc.progress == 0.0


def test_player_progression_defaults():
    pp = PlayerProgression()
    assert pp.attributes.perception == 1
    assert pp.inventory == []
    assert pp.reputation == {}


def test_patch_op_set():
    op = PatchOp(entity_type="character", id="npc_mira", field="attitude_to_player", value=0.3)
    assert op.op == "set"


def test_turn_patch_empty():
    tp = TurnPatch()
    assert tp.world_changes == []
    assert tp.new_facts == []


def test_intent_roundtrip():
    i = Intent(intent="converse", target="npc_mira", raw_text="говорю с Мирой")
    dump = i.model_dump()
    assert Intent.model_validate(dump) == i


def test_world_meta_roundtrip():
    meta = WorldMeta(
        id="w1",
        title="Соляная Корона",
        genre="морское тёмное фэнтези",
        tone=["меланхоличное"],
        themes=["упадок"],
        premise="Приморский город гниёт под старыми пактами.",
    )
    assert meta.tick == 0
    assert meta.player_character_id == "pc"


def test_game_settings_defaults():
    s = GameSettings()
    assert s.language == "ru"
    assert s.difficulty == "normal"


def test_inspiration():
    i = WorldInspiration(genre="фэнтези", tone=["меланхоличное"])
    assert i.scale == "town"
