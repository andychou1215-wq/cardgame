from src.playtest.persistence import PlaytestStore

class AutoPersistGuard:
    def __init__(self, store=None):
        self.store = store or PlaytestStore()
        self.saved_game_ids = set()

    def save_if_finished(self, game, *, rules_version="", commit_hash=""):
        recorder = getattr(game, "telemetry", None)
        if recorder is None or getattr(game, "winner_index", None) is None:
            return None
        game_id = recorder.game_id
        if game_id in self.saved_game_ids:
            return None
        result = self.store.save_game(
            recorder,
            game,
            rules_version=rules_version,
            commit_hash=commit_hash,
        )
        self.saved_game_ids.add(game_id)
        return result
