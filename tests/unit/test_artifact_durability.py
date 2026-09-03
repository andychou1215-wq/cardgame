from src.cards.models import CardDefinition, CardInstance
from src.core.game import Game
from src.deck.loader import GameData
from src.ui.components import card_html
from tests.integration.test_engine_core import make_repo


def make_artifact(durability: int = 2) -> CardInstance:
    return CardInstance(
        CardDefinition(
            card_id="A001",
            name="測試神器",
            card_type="artifact",
            cost=1,
            faction_id="F001",
            durability=durability,
        )
    )


def make_game(tmp_path) -> Game:
    make_repo(tmp_path)
    return Game(GameData(tmp_path), "D001", "D002", seed=810)


def test_artifact_starts_at_its_printed_durability() -> None:
    artifact = make_artifact(3)

    assert artifact.current_durability == 3


def test_turn_start_decays_only_active_player_artifacts(tmp_path) -> None:
    game = make_game(tmp_path)
    active_artifact = make_artifact(3)
    opponent_artifact = make_artifact(3)
    game.players[0].artifacts = [active_artifact]
    game.players[1].artifacts = [opponent_artifact]
    game.active_player_index = 0

    game._start_turn(initial=True)

    assert active_artifact.current_durability == 2
    assert opponent_artifact.current_durability == 3
    event = next(e for e in game.telemetry.events if e.event_type == "artifact_durability_changed")
    assert event.source_id == active_artifact.instance_id
    assert event.metadata == {"before": 3, "after": 2}


def test_zero_durability_artifact_is_destroyed_at_turn_start(tmp_path) -> None:
    game = make_game(tmp_path)
    artifact = make_artifact(1)
    player = game.players[0]
    player.artifacts = [artifact]
    game.active_player_index = 0

    game._start_turn(initial=True)

    assert artifact.current_durability == 0
    assert artifact not in player.artifacts
    assert artifact in player.graveyard
    destroyed = [e for e in game.telemetry.events if e.event_type == "artifact_destroyed"]
    assert len(destroyed) == 1
    assert destroyed[0].source_id == artifact.instance_id
    assert destroyed[0].metadata == {"reason": "durability"}


def test_artifact_card_html_shows_current_and_max_durability() -> None:
    artifact = make_artifact(3)
    artifact.current_durability = 2

    rendered = card_html(artifact)

    assert "耐久度 2/3" in rendered
