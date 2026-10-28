"""
CapTax AI - DTAA Relief Computation Module (Schedule FSI)
Owner: Shraddha Singh (Team Lead & AI/Interpretation Lead) — DTAA rules (US; UK/UAE/SG planned Week 6)

Computes Double Taxation Avoidance Agreement (India-US) relief on foreign
dividend income: relief is the LOWER of (a) tax already withheld abroad,
and (b) the equivalent Indian tax liability on that income — per Section
90/91 and Article 25 (Relief from Double Taxation) of the India-US DTAA.

Simplification for this academic version: Indian tax rate on foreign
dividend income is treated as a flat rate representing the taxpayer's
slab (configurable), rather than a full slab computation.

Run: python dtaa_relief.py
Reads:  ./data/foreign_dividends.csv
Writes: ./data/dtaa_relief.csv
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "backend" / "data"

ASSUMED_INDIAN_SLAB_RATE = 0.30  # configurable: taxpayer's applicable slab rate


def compute_relief(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Payment Date"] = pd.to_datetime(out["Payment Date"], format="%m/%d/%Y")
    out["financial_year"] = out["Payment Date"].apply(
        lambda d: f"FY{d.year - (0 if d.month >= 4 else 1)}-{str(d.year + (1 if d.month >= 4 else 0))[-2:]}"
    )

    out["gross_dividend_inr"] = (out["Gross Dividend (USD)"] * out["USD-INR Rate"]).round(2)
    out["foreign_tax_withheld_inr"] = (out["Withholding Tax (USD)"] * out["USD-INR Rate"]).round(2)
    out["indian_tax_on_income_inr"] = (out["gross_dividend_inr"] * ASSUMED_INDIAN_SLAB_RATE).round(2)
    out["dtaa_relief_inr"] = out[["foreign_tax_withheld_inr", "indian_tax_on_income_inr"]].min(axis=1).round(2)
    out["net_indian_tax_payable_inr"] = (out["indian_tax_on_income_inr"] - out["dtaa_relief_inr"]).round(2)

    return out[[
        "Security", "financial_year", "Country of Source", "DTAA Article",
        "gross_dividend_inr", "foreign_tax_withheld_inr",
        "indian_tax_on_income_inr", "dtaa_relief_inr",
        "net_indian_tax_payable_inr", "TDS Certificate Ref",
    ]]


def main():
    df = pd.read_csv(DATA_DIR / "foreign_dividends.csv")
    relief = compute_relief(df)
    out_path = DATA_DIR / "dtaa_relief.csv"
    relief.to_csv(out_path, index=False)

    print(f"Computed DTAA relief for {len(relief)} foreign dividend entries")
    by_fy = relief.groupby("financial_year")[
        ["gross_dividend_inr", "dtaa_relief_inr", "net_indian_tax_payable_inr"]
    ].sum().round(2)
    print(by_fy.to_string())
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
