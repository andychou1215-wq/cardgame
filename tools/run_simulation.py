from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.game import Game
from src.deck.loader import GameData
from src.playtest.persistence import PlaytestStore
from src.playtest.simulation import run_batch, save_simulation_results

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--games", type=int, default=10)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--deck1", default="D001")
    p.add_argument("--deck2", default="D002")
    p.add_argument("--max-actions", type=int, default=1000)
    p.add_argument("--rules-version", default="M3")
    p.add_argument("--commit-hash", default="")
    p.add_argument("--no-persist", action="store_true")
    args = p.parse_args()

    data = GameData(ROOT)
    def factory(seed):
        return Game(data, args.deck1, args.deck2, seed=seed)

    store = None if args.no_persist else PlaytestStore(ROOT / "playtest_data")
    results = run_batch(
        factory,
        games=args.games,
        seed=args.seed,
        max_actions=args.max_actions,
        store=store,
        rules_version=args.rules_version,
        commit_hash=args.commit_hash,
    )
    out = ROOT / "playtest_data" / "summaries" / "simulation_results.csv"
    save_simulation_results(out, results)

    for status in ("finished","stalled","invalid_legal_action","action_limit"):
        print(f"{status}: {sum(r.status == status for r in results)}")
    print("saved:", out)

if __name__ == "__main__":
    main()
