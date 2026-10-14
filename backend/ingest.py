"""
CapTax AI - Data Ingestion & Normalization Module (Week 3)
Owner: Anishka Jain (Backend & Data Lead) — broker adapters

Reads the six raw broker-format exports and normalizes them into a single
unified trade schema, resolving:
  - Varied column names across brokers
  - Varied date formats (YYYY-MM-DD, DD/MM/YYYY, DD-Mon-YYYY, YYYYMMDD, MM/DD/YYYY)
  - Varied buy/sell notation (buy/sell, BUY/SELL, B/S, Buy/Sell)
  - Foreign currency trades (Interactive Brokers) converted to INR using
    the provided FX rate, with original currency/amount retained for audit

Unified schema (per trade row):
    broker, symbol, company_name, isin, trade_date, transaction_type,
    quantity, price, price_currency, fx_rate_to_inr, price_inr,
    gross_amount_inr, charges_inr, exchange, source_ref

Run: python ingest.py
Reads:  ./data/*.csv
Writes: ./data/normalized_trades.csv
"""

from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

UNIFIED_COLUMNS = [
    "broker", "symbol", "company_name", "isin", "trade_date",
    "transaction_type", "quantity", "price", "price_currency",
    "fx_rate_to_inr", "price_inr", "gross_amount_inr", "charges_inr",
    "exchange", "source_ref",
]


def _std_side(value: str) -> str:
    """Normalize buy/sell notation to 'BUY' / 'SELL'."""
    v = str(value).strip().upper()
    if v in ("BUY", "B"):
        return "BUY"
    if v in ("SELL", "S"):
        return "SELL"
    raise ValueError(f"Unrecognized transaction side: {value!r}")


def load_zerodha() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "zerodha_trades.csv")
    out = pd.DataFrame({
        "broker": "Zerodha",
        "symbol": df["Symbol"],
        "company_name": pd.NA,
        "isin": df["ISIN"],
        "trade_date": pd.to_datetime(df["Trade Date"], format="%Y-%m-%d"),
        "transaction_type": df["Trade Type"].apply(_std_side),
        "quantity": df["Quantity"].astype(int),
        "price": df["Price"].astype(float),
        "price_currency": "INR",
        "fx_rate_to_inr": 1.0,
        "charges_inr": (df["Brokerage"] + df["STT"]).astype(float),
        "exchange": df["Exchange"],
        "source_ref": df["Trade ID"],
    })
    return out


def load_groww() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "groww_trades.csv")
    out = pd.DataFrame({
        "broker": "Groww",
        "symbol": df["Ticker"],
        "company_name": df["Stock Name"],
        "isin": pd.NA,
        "trade_date": pd.to_datetime(df["Date"], format="%d/%m/%Y"),
        "transaction_type": df["Txn Type"].apply(_std_side),
        "quantity": df["Qty"].astype(int),
        "price": df["Avg Price"].astype(float),
        "price_currency": "INR",
        "fx_rate_to_inr": 1.0,
        "charges_inr": df["Charges"].astype(float),
        "exchange": df["Exchange Segment"],
        "source_ref": df["Order Ref"],
    })
    return out


def load_icici_direct() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "icici_direct_trades.csv")
    out = pd.DataFrame({
        "broker": "ICICI Direct",
        "symbol": df["Scrip Code"],
        "company_name": df["Company Name"],
        "isin": pd.NA,
        "trade_date": pd.to_datetime(df["Execution Date"], format="%d-%b-%Y"),
        "transaction_type": df["B/S Indicator"].apply(_std_side),
        "quantity": df["Quantity Traded"].astype(int),
        "price": df["Rate"].astype(float),
        "price_currency": "INR",
        "fx_rate_to_inr": 1.0,
        "charges_inr": df["Transaction Charges"].astype(float),
        "exchange": df["Exchange"],
        "source_ref": df["Contract Note No"],
    })
    return out


def load_interactive_brokers() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "interactive_brokers_trades.csv")
    out = pd.DataFrame({
        "broker": "Interactive Brokers",
        "symbol": df["Symbol"],
        "company_name": df["Description"],
        "isin": pd.NA,
        "trade_date": pd.to_datetime(df["TradeDate"], format="%Y%m%d"),
        "transaction_type": df["Buy/Sell"].apply(_std_side),
        "quantity": df["Quantity"].astype(int),
        "price": df["TradePrice"].astype(float),
        "price_currency": df["Currency"],
        "fx_rate_to_inr": df["FXRateToINR"].astype(float),
        "charges_inr": (df["Commission"] * df["FXRateToINR"]).astype(float),
        "exchange": df["Exchange"],
        "source_ref": df["TransactionID"],
    })
    return out


LOADERS = {
    "zerodha": load_zerodha,
    "groww": load_groww,
    "icici_direct": load_icici_direct,
    "interactive_brokers": load_interactive_brokers,
}


def normalize_all() -> pd.DataFrame:
    frames = [loader() for loader in LOADERS.values()]
    combined = pd.concat(frames, ignore_index=True)

    # Derived fields
    combined["price_inr"] = (combined["price"] * combined["fx_rate_to_inr"]).round(2)
    combined["gross_amount_inr"] = (combined["price_inr"] * combined["quantity"]).round(2)
    combined["charges_inr"] = combined["charges_inr"].round(2)

    combined = combined[UNIFIED_COLUMNS]
    combined = combined.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
    return combined


def validate(df: pd.DataFrame) -> None:
    """Basic sanity checks before handing off to FIFO matching."""
    assert df["quantity"].gt(0).all(), "Found non-positive quantity"
    assert df["price"].gt(0).all(), "Found non-positive price"
    assert df["transaction_type"].isin(["BUY", "SELL"]).all(), "Bad transaction_type"
    assert df["trade_date"].notna().all(), "Found missing trade_date"
    print(f"Validation passed: {len(df)} normalized trade rows")


def main():
    normalized = normalize_all()
    validate(normalized)
    out_path = DATA_DIR / "normalized_trades.csv"
    normalized.to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(normalized)} rows)")
    print(normalized["broker"].value_counts().to_string())


if __name__ == "__main__":
    main()
