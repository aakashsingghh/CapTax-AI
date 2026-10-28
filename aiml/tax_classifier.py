"""
CapTax AI - LTCG / STCG Tax Classification Module
Owner: Shraddha Singh (Team Lead & AI/Interpretation Lead) — interpretation layer for LTCG/STCG
(currently rule-based; Week 5 scope is to swap in LLM-assisted interpretation via LangChain)

Classifies each realized gain/loss record as Long-Term or Short-Term
Capital Gain based on Indian holding-period rules for listed equity
(> 365 days = LTCG), and applies simplified current-regime tax rates.

Simplifications for this academic version:
  - Grandfathering (FMV as on 31-Jan-2018) is NOT applied; full gain is
    taxed. This is flagged clearly as a v2 item.
  - LTCG equity exemption threshold (₹1,25,000 aggregate/year) is applied
    as a simple annual reduction, not lot-by-lot.
  - Flat rates used: LTCG 12.5%, STCG 20% (equity, per Budget 2024 regime).

Run: python tax_classifier.py
Reads:  ./data/realized_gains.csv
Writes: ./data/classified_gains.csv, ./data/tax_summary.csv
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "backend" / "data"

LTCG_THRESHOLD_DAYS = 365
LTCG_RATE = 0.125
STCG_RATE = 0.20
LTCG_ANNUAL_EXEMPTION_INR = 125_000


def classify(realized: pd.DataFrame) -> pd.DataFrame:
    df = realized[realized["realized_gain_inr"].notna()].copy()
    df["sell_date"] = pd.to_datetime(df["sell_date"])
    df["financial_year"] = df["sell_date"].apply(fy_label)
    df["gain_type"] = df["holding_period_days"].apply(
        lambda d: "LTCG" if d > LTCG_THRESHOLD_DAYS else "STCG"
    )
    return df


def fy_label(date) -> str:
    # Indian FY: 1 Apr - 31 Mar
    year = date.year if date.month >= 4 else date.year - 1
    return f"FY{year}-{str(year + 1)[-2:]}"


def summarize_tax(classified: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for fy, fy_df in classified.groupby("financial_year"):
        ltcg_gain = fy_df.loc[fy_df["gain_type"] == "LTCG", "realized_gain_inr"].sum()
        stcg_gain = fy_df.loc[fy_df["gain_type"] == "STCG", "realized_gain_inr"].sum()

        taxable_ltcg = max(ltcg_gain - LTCG_ANNUAL_EXEMPTION_INR, 0)
        ltcg_tax = round(taxable_ltcg * LTCG_RATE, 2)
        stcg_tax = round(max(stcg_gain, 0) * STCG_RATE, 2)

        rows.append({
            "financial_year": fy,
            "ltcg_gain_inr": round(ltcg_gain, 2),
            "stcg_gain_inr": round(stcg_gain, 2),
            "ltcg_exemption_applied_inr": min(ltcg_gain, LTCG_ANNUAL_EXEMPTION_INR) if ltcg_gain > 0 else 0,
            "taxable_ltcg_inr": round(taxable_ltcg, 2),
            "ltcg_tax_inr": ltcg_tax,
            "stcg_tax_inr": stcg_tax,
            "total_tax_inr": round(ltcg_tax + stcg_tax, 2),
        })
    return pd.DataFrame(rows).sort_values("financial_year")


def main():
    realized = pd.read_csv(DATA_DIR / "realized_gains.csv")
    classified = classify(realized)
    classified.to_csv(DATA_DIR / "classified_gains.csv", index=False)

    summary = summarize_tax(classified)
    summary.to_csv(DATA_DIR / "tax_summary.csv", index=False)

    print(f"Classified {len(classified)} realized gain records")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
