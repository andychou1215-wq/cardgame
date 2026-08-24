from types import SimpleNamespace
from src.playtest.auto_persist import AutoPersistGuard

class Store:
    def __init__(self):
        self.calls = 0

    def save_game(self, recorder, game, **kwargs):
        self.calls += 1
        return {"game_id": recorder.game_id}

def test_save_only_once():
    store = Store()
    guard = AutoPersistGuard(store)
    game = SimpleNamespace(
        winner_index=0,
        telemetry=SimpleNamespace(game_id="g1"),
    )
    assert guard.save_if_finished(game) is not None
    assert guard.save_if_finished(game) is None
    assert store.calls == 1

def test_unfinished_game_not_saved():
    store = Store()
    guard = AutoPersistGuard(store)
    game = SimpleNamespace(
        winner_index=None,
        telemetry=SimpleNamespace(game_id="g1"),
    )
    assert guard.save_if_finished(game) is None
    assert store.calls == 0
