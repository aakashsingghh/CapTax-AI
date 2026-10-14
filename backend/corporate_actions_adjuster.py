"""
CapTax AI - Corporate Action Adjustment Module
Owner: Anishka Jain (Backend & Data Lead) — reconciliation engine / corporate action & FX logic

Adjusts pre-existing BUY lots for splits and bonus issues so that FIFO
matching downstream works on split/bonus-adjusted quantity and cost basis.
Dividends and rights issues are logged for reference but do not alter
existing lot quantity/cost (dividends are separate taxable income; rights
issue application is treated as a fresh purchase, out of scope for v1).

Run: python corporate_actions_adjuster.py
Reads:  ./data/normalized_trades.csv, ./data/corporate_actions.csv
Writes: ./data/adjusted_trades.csv
"""

import re
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"


def parse_ratio(detail: str):
    """Extract a numeric multiplier from a split/bonus ratio string like '1:2' or '2:1'."""
    match = re.search(r"(\d+)\s*:\s*(\d+)", detail)
    if not match:
        return None
    old, new = int(match.group(1)), int(match.group(2))
    # "old : new" means: for every `old` shares held, you now have `new` shares (bonus/split),
    # e.g. Split "1:2" -> 1 share becomes 2 -> multiplier 2
    # e.g. Bonus "1:1" -> 1 share becomes 2 (1 original + 1 bonus) -> multiplier 2
    return new / old if "split" in detail.lower() else (old + new) / old


def load_actions() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "corporate_actions.csv")
    df["Ex-Date"] = pd.to_datetime(df["Ex-Date"])
    return df


def apply_adjustments(trades: pd.DataFrame, actions: pd.DataFrame) -> pd.DataFrame:
    trades = trades.copy()
    trades["trade_date"] = pd.to_datetime(trades["trade_date"])
    trades["adj_quantity"] = trades["quantity"]
    trades["adj_price"] = trades["price_inr"]
    trades["adjustment_note"] = ""

    relevant = actions[actions["Action Type"].isin(["Split", "Bonus"])]

    for _, action in relevant.iterrows():
        symbol = action["Ticker/Symbol"]
        ex_date = action["Ex-Date"]
        multiplier = parse_ratio(action["Ratio/Detail"])
        if multiplier is None:
            continue

        # Any BUY lot for this symbol dated before the ex-date gets its
        # quantity multiplied and price divided (cost basis preserved).
        mask = (
            (trades["symbol"] == symbol)
            & (trades["transaction_type"] == "BUY")
            & (trades["trade_date"] < ex_date)
        )
        trades.loc[mask, "adj_price"] = trades.loc[mask, "adj_price"] / multiplier
        trades.loc[mask, "adj_quantity"] = (trades.loc[mask, "adj_quantity"] * multiplier).round().astype(int)
        note = f"{action['Action Type']} {action['Ratio/Detail']} on {ex_date.date()}"
        trades.loc[mask, "adjustment_note"] = trades.loc[mask, "adjustment_note"] + note + "; "

    return trades


def main():
    trades = pd.read_csv(DATA_DIR / "normalized_trades.csv")
    actions = load_actions()
    adjusted = apply_adjustments(trades, actions)
    out_path = DATA_DIR / "adjusted_trades.csv"
    adjusted.to_csv(out_path, index=False)
    n_adjusted = (adjusted["adjustment_note"] != "").sum()
    print(f"Applied corporate action adjustments to {n_adjusted} lots")
    print(f"Wrote {out_path} ({len(adjusted)} rows)")


if __name__ == "__main__":
    main()
