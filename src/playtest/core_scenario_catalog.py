from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoreScenarioSpec:
    scenario_id: str
    name: str
    expected_rule: str


CORE_SCENARIOS = (
    CoreScenarioSpec("S001", "庇護限制攻擊目標", "存在可攻擊的庇護單位時，只能攻擊庇護。"),
    CoreScenarioSpec("S002", "迴避不能被 Unit 攻擊", "迴避單位不出現在敵方 Unit 合法攻擊目標。"),
    CoreScenarioSpec("S003", "庇護與迴避交互", "另一單位有迴避時，可攻擊庇護仍保持優先。"),
    CoreScenarioSpec("S004", "格檔減少戰鬥傷害", "格檔每次受到戰鬥傷害時減少 1，最低為 0。"),
    CoreScenarioSpec("S005", "格檔不減效果傷害", "damage 效果不受格檔減傷。"),
    CoreScenarioSpec("S006", "吸血依實際主動攻擊傷害治療", "吸血只治療攻擊者，且以實際造成傷害計算。"),
    CoreScenarioSpec("S007", "最大生命增加同步治療", "最大生命 +X 時現有生命同步 +X。"),
    CoreScenarioSpec("S008", "同批死亡", "同批生命歸零單位先全部離場，再處理離場觸發。"),
    CoreScenarioSpec("S009", "AP/NAP on_leave", "同批死亡的 on_leave 依主動玩家、非主動玩家順序排隊。"),
    CoreScenarioSpec("S010", "Transform → on_flip snapshot", "翻面後 on_flip 使用 back side snapshot。"),
)
