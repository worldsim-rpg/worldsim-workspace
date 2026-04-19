"""Валидация pydantic-моделей канона."""

import json

import pytest
from pydantic import ValidationError

from worldsim_schemas import (
    Arc,
    ArcStage,
    Attributes,
    Character,
    Condition,
    Faction,
    GameSettings,
    Goal,
    Intent,
    Location,
    PatchOp,
    PlayerProgression,
    PlotState,
    Secret,
    TimelineEvent,
    TurnPatch,
    WorldInspiration,
    WorldMeta,
)


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------


def test_location_minimal():
    loc = Location(id="loc_docks", name="Доки", short_description="Соль, верёвки, тихий прибой.")
    assert loc.connected_to == []
    assert loc.discovered is False
    assert loc.visited is False
    assert loc.full_description is None


def test_location_full():
    loc = Location(
        id="loc_market",
        name="Рынок",
        short_description="Шум и запах рыбы.",
        full_description="Широкая площадь с рядами прилавков.",
        tags=["commerce", "public"],
        connected_to=["loc_docks", "loc_inn"],
        parent_region_id="region_harbor",
        active_elements=["merchant_elena"],
        discovered=True,
        visited=True,
    )
    assert loc.tags == ["commerce", "public"]
    assert loc.visited is True


def test_location_roundtrip():
    loc = Location(
        id="loc_x",
        name="X",
        short_description="desc",
        connected_to=["loc_y"],
        discovered=True,
    )
    assert Location.model_validate(loc.model_dump()) == loc


def test_location_roundtrip_json():
    loc = Location(id="loc_z", name="Z", short_description="d")
    assert Location.model_validate_json(loc.model_dump_json()) == loc


# ---------------------------------------------------------------------------
# Character
# ---------------------------------------------------------------------------


def test_character_minimal_npc():
    npc = Character(id="npc_mira", name="Мира", location_id="loc_docks")
    assert npc.is_player is False
    assert npc.alive is True
    assert npc.condition is Condition.OK
    assert npc.attitude_to_player == 0.0


def test_character_player():
    pc = Character(id="pc", name="Странник", is_player=True, location_id="loc_docks")
    assert pc.is_player is True


def test_attitude_clamped():
    with pytest.raises(ValidationError):
        Character(id="npc_x", name="X", location_id="loc_x", attitude_to_player=2.0)


def test_attitude_clamped_negative():
    with pytest.raises(ValidationError):
        Character(id="npc_x", name="X", location_id="loc_x", attitude_to_player=-1.5)


def test_character_condition_enum():
    npc = Character(id="npc_t", name="T", location_id="l", condition=Condition.WOUNDED)
    assert npc.condition == Condition.WOUNDED


def test_character_invalid_condition():
    with pytest.raises(ValidationError):
        Character(id="npc_t", name="T", location_id="l", condition="dead")


def test_character_roundtrip():
    npc = Character(
        id="npc_mira",
        name="Мира",
        location_id="loc_docks",
        goals=[Goal(text="выжить", priority=0.9)],
        knowledge=["secret_1"],
    )
    assert Character.model_validate(npc.model_dump()) == npc


# ---------------------------------------------------------------------------
# Goal
# ---------------------------------------------------------------------------


def test_goal_priority_clamped():
    with pytest.raises(ValidationError):
        Goal(text="go", priority=1.5)


def test_goal_priority_clamped_negative():
    with pytest.raises(ValidationError):
        Goal(text="go", priority=-0.1)


def test_goal_defaults():
    g = Goal(text="survive")
    assert g.priority == 0.5


# ---------------------------------------------------------------------------
# Faction
# ---------------------------------------------------------------------------


def test_faction_minimal():
    f = Faction(id="f_guild", name="Гильдия", public_role="Торговцы")
    assert f.hidden_agenda is None
    assert f.relations == {}
    assert f.status == "stable"


def test_faction_relations():
    f = Faction(
        id="f_guild",
        name="Гильдия",
        public_role="Торговцы",
        relations={"f_watch": 0.3, "f_cult": -0.8},
    )
    assert f.relations["f_cult"] == -0.8


def test_faction_roundtrip():
    f = Faction(
        id="f_cult",
        name="Культ",
        public_role="Храм",
        hidden_agenda="Пробудить древнего",
        resources=["gold", "influence"],
        goals=[Goal(text="расширить влияние")],
        relations={"f_guild": -0.5},
    )
    assert Faction.model_validate(f.model_dump()) == f


# ---------------------------------------------------------------------------
# Secret
# ---------------------------------------------------------------------------


def test_secret_defaults():
    s = Secret(id="s_pact", truth="Мэр — предатель")
    assert s.known_by == []
    assert s.status == "hidden"
    assert s.discoverability == pytest.approx(0.3)


def test_secret_discoverability_clamped():
    with pytest.raises(ValidationError):
        Secret(id="s", truth="t", discoverability=1.5)


def test_secret_status_literals():
    for status in ("hidden", "hinted", "revealed"):
        s = Secret(id="s", truth="t", status=status)
        assert s.status == status


def test_secret_invalid_status():
    with pytest.raises(ValidationError):
        Secret(id="s", truth="t", status="burned")


def test_secret_roundtrip():
    s = Secret(id="s1", truth="правда", known_by=["npc_mira"], status="hinted")
    assert Secret.model_validate(s.model_dump()) == s


# ---------------------------------------------------------------------------
# Arc
# ---------------------------------------------------------------------------


def test_arc_default_stage():
    arc = Arc(id="arc_1", title="Sealed Crate")
    assert arc.stage is ArcStage.HOOK
    assert arc.progress == 0.0


def test_arc_progress_clamped():
    with pytest.raises(ValidationError):
        Arc(id="a", title="t", progress=1.1)


def test_arc_urgency_clamped():
    with pytest.raises(ValidationError):
        Arc(id="a", title="t", urgency=-0.1)


def test_arc_stage_all_values():
    for stage in ArcStage:
        arc = Arc(id="a", title="t", stage=stage)
        assert arc.stage == stage


def test_arc_roundtrip():
    arc = Arc(
        id="arc_main",
        title="Тайна Причала",
        stage=ArcStage.DEVELOPMENT,
        progress=0.4,
        involved_entities=["npc_mira", "loc_docks"],
    )
    assert Arc.model_validate(arc.model_dump()) == arc


# ---------------------------------------------------------------------------
# TimelineEvent
# ---------------------------------------------------------------------------


def test_timeline_event():
    ev = TimelineEvent(tick=5, type="discovery", summary="Игрок нашёл ключ.")
    assert ev.tick == 5
    data = ev.model_dump()
    assert TimelineEvent.model_validate(data) == ev


# ---------------------------------------------------------------------------
# Attributes
# ---------------------------------------------------------------------------


def test_attributes_defaults():
    a = Attributes()
    for field in ("perception", "empathy", "lore", "athletics", "subterfuge"):
        assert getattr(a, field) == 1


def test_attributes_custom():
    a = Attributes(perception=3, subterfuge=5)
    assert a.perception == 3
    assert a.subterfuge == 5


# ---------------------------------------------------------------------------
# PlayerProgression
# ---------------------------------------------------------------------------


def test_player_progression_defaults():
    pp = PlayerProgression()
    assert pp.attributes.perception == 1
    assert pp.inventory == []
    assert pp.reputation == {}


def test_player_progression_roundtrip():
    pp = PlayerProgression(
        character_id="pc",
        skill_counters={"talked_to_npcs": 7},
        reputation={"f_guild": 0.5},
        known_facts=["npc_mira_is_spy"],
        inventory=["dagger", "lantern"],
        flags=["completed_intro"],
        condition=Condition.TIRED,
    )
    assert PlayerProgression.model_validate(pp.model_dump()) == pp


# ---------------------------------------------------------------------------
# PlotState
# ---------------------------------------------------------------------------


def test_plot_state_defaults():
    ps = PlotState()
    assert ps.main_tensions == []
    assert ps.active_arcs == []
    assert ps.dramatic_pressure == pytest.approx(0.3)


def test_plot_state_pressure_clamped():
    with pytest.raises(ValidationError):
        PlotState(dramatic_pressure=1.5)


def test_plot_state_with_arcs():
    arc = Arc(id="a1", title="T")
    ps = PlotState(main_tensions=["власть рушится"], active_arcs=[arc], dramatic_pressure=0.7)
    assert len(ps.active_arcs) == 1
    assert PlotState.model_validate(ps.model_dump()) == ps


# ---------------------------------------------------------------------------
# WorldInspiration
# ---------------------------------------------------------------------------


def test_inspiration():
    i = WorldInspiration(genre="фэнтези", tone=["меланхоличное"])
    assert i.scale == "town"


def test_inspiration_all_fields():
    i = WorldInspiration(
        genre="sci-fi",
        tone=["dark"],
        references=["Dune"],
        themes=["power"],
        desired_player_activity="exploration",
        magic_level="none",
        scale="city",
        harshness="grim",
        free_notes="No lightsabers.",
    )
    assert i.magic_level == "none"
    assert i.scale == "city"


def test_inspiration_invalid_magic_level():
    with pytest.raises(ValidationError):
        WorldInspiration(genre="x", magic_level="ultra")


def test_inspiration_invalid_scale():
    with pytest.raises(ValidationError):
        WorldInspiration(genre="x", scale="universe")


def test_inspiration_roundtrip():
    i = WorldInspiration(genre="фэнтези", tone=["мрачное"], scale="region")
    assert WorldInspiration.model_validate(i.model_dump()) == i


# ---------------------------------------------------------------------------
# WorldMeta
# ---------------------------------------------------------------------------


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
    assert WorldMeta.model_validate(meta.model_dump()) == meta


def test_world_meta_tick():
    meta = WorldMeta(id="w", title="t", genre="g", premise="p", tick=42)
    assert meta.tick == 42


# ---------------------------------------------------------------------------
# GameSettings
# ---------------------------------------------------------------------------


def test_game_settings_defaults():
    s = GameSettings()
    assert s.language == "ru"
    assert s.difficulty == "normal"
    assert s.generation_depth == "compact"
    assert s.turn_tempo == "scene"


def test_game_settings_invalid_language():
    with pytest.raises(ValidationError):
        GameSettings(language="fr")


def test_game_settings_invalid_difficulty():
    with pytest.raises(ValidationError):
        GameSettings(difficulty="easy")


def test_game_settings_roundtrip():
    s = GameSettings(language="en", difficulty="hardcore", generation_depth="rich", turn_tempo="hour")
    assert GameSettings.model_validate(s.model_dump()) == s


# ---------------------------------------------------------------------------
# Intent
# ---------------------------------------------------------------------------


def test_intent_roundtrip():
    i = Intent(intent="converse", target="npc_mira", raw_text="говорю с Мирой")
    dump = i.model_dump()
    assert Intent.model_validate(dump) == i


def test_intent_risk_levels():
    for risk in ("low", "medium", "high"):
        i = Intent(intent="move", raw_text="иду", risk_level=risk)
        assert i.risk_level == risk


def test_intent_invalid_risk():
    with pytest.raises(ValidationError):
        Intent(intent="move", raw_text="иду", risk_level="extreme")


def test_intent_optional_fields():
    i = Intent(intent="wait", raw_text="жду")
    assert i.method is None
    assert i.target is None
    assert i.tone is None


def test_intent_json_roundtrip():
    i = Intent(intent="examine", target_raw="старый ящик", raw_text="осматриваю ящик")
    assert Intent.model_validate_json(i.model_dump_json()) == i


# ---------------------------------------------------------------------------
# PatchOp
# ---------------------------------------------------------------------------


def test_patch_op_set():
    op = PatchOp(entity_type="character", id="npc_mira", field="attitude_to_player", value=0.3)
    assert op.op == "set"


def test_patch_op_inc():
    op = PatchOp(entity_type="player_progression", id="_", field="skill_counters.talked_to_npcs", op="inc", value=1)
    assert op.op == "inc"
    assert op.field == "skill_counters.talked_to_npcs"


def test_patch_op_append():
    op = PatchOp(entity_type="character", id="pc", field="knowledge", op="append", value="secret_1")
    assert op.op == "append"


def test_patch_op_remove():
    op = PatchOp(entity_type="player_progression", id="_", field="flags", op="remove", value="old_flag")
    assert op.op == "remove"


def test_patch_op_invalid_entity_type():
    with pytest.raises(ValidationError):
        PatchOp(entity_type="monster", id="x", field="hp")


def test_patch_op_invalid_op():
    with pytest.raises(ValidationError):
        PatchOp(entity_type="character", id="x", field="name", op="delete")


def test_patch_op_singleton_id():
    for singleton in ("player_progression", "world_meta", "plot_state"):
        op = PatchOp(entity_type=singleton, id="_", field="tick", value=1)
        assert op.id == "_"


def test_patch_op_roundtrip():
    op = PatchOp(entity_type="arc", id="arc_1", field="progress", op="set", value=0.6)
    assert PatchOp.model_validate(op.model_dump()) == op


# ---------------------------------------------------------------------------
# TurnPatch
# ---------------------------------------------------------------------------


def test_turn_patch_empty():
    tp = TurnPatch()
    assert tp.world_changes == []
    assert tp.new_facts == []
    assert tp.timeline_event is None
    assert tp.narrative_summary is None


def test_turn_patch_full():
    op = PatchOp(entity_type="character", id="npc_mira", field="alive", value=False)
    ev = TimelineEvent(tick=10, type="death", summary="Мира погибла.")
    tp = TurnPatch(
        world_changes=[op],
        new_facts=["мира_мертва"],
        timeline_event=ev,
        narrative_summary="Трагический конец.",
    )
    assert len(tp.world_changes) == 1
    assert tp.timeline_event.tick == 10


def test_turn_patch_roundtrip():
    op = PatchOp(entity_type="location", id="loc_docks", field="visited", value=True)
    tp = TurnPatch(world_changes=[op], new_facts=["visited_docks"])
    restored = TurnPatch.model_validate(tp.model_dump())
    assert restored == tp


def test_turn_patch_json_roundtrip():
    tp = TurnPatch(new_facts=["fact_a", "fact_b"], narrative_summary="summary")
    assert TurnPatch.model_validate_json(tp.model_dump_json()) == tp
