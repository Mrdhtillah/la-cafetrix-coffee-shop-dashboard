from pathlib import Path
import re

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "coffee_shop.xlsx"


def parse_product_detail(text):
    """Split a product detail into a readable product name and optional size."""
    text = str(text).strip()
    match = re.search(r"^(.*?)\s+(Sm|Rg|Lg)$", text, flags=re.IGNORECASE)

    if match:
        product_name = match.group(1).strip().title()
        product_size = match.group(2).strip().upper()
    else:
        product_name = text.title()
        product_size = "RG"

    return pd.Series(
        [product_name, product_size],
        index=["product_name_clean", "product_size"],
    )


@st.cache_data(show_spinner=False)
def load_data():
    """Load and validate the transaction dataset without changing source values."""
    df = pd.read_excel(DATA_PATH, sheet_name="Transactions")
    df = df.loc[:, ~df.columns.duplicated()].copy()

    required_columns = [
        "transaction_id",
        "transaction_date",
        "transaction_time",
        "transaction_qty",
        "unit_price",
        "Revenue",
        "Month",
        "Hour",
        "store_location",
        "product_category",
        "product_detail",
    ]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(
            "The Transactions sheet is missing required columns: "
            + ", ".join(missing)
        )

    for column in ["transaction_id", "store_id", "product_id"]:
        if column in df.columns:
            df[column] = df[column].astype(str)

    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df["transaction_time"] = pd.to_datetime(
        df["transaction_time"].astype(str), format="%H:%M:%S", errors="coerce"
    ).dt.time

    df = df.dropna(
        subset=[
            "transaction_id",
            "transaction_date",
            "Revenue",
            "transaction_qty",
            "unit_price",
            "Hour",
            "Month",
            "store_location",
            "product_category",
            "product_detail",
        ]
    ).copy()

    df = df[(df["transaction_qty"] > 0) & (df["unit_price"] > 0)].copy()

    product_detail = df["product_detail"].astype(str).str.strip()
    extracted_size = product_detail.str.extract(
        r"\s+(Sm|Rg|Lg)$", expand=False, flags=re.IGNORECASE
    )
    df["product_size"] = extracted_size.fillna("RG").str.upper()
    df["product_name_clean"] = (
        product_detail
        .str.replace(r"\s+(Sm|Rg|Lg)$", "", regex=True, flags=re.IGNORECASE)
        .str.strip()
        .str.title()
    )

    def assign_time_session(hour):
        if hour < 11:
            return "Morning"
        if hour < 15:
            return "Midday"
        if hour < 18:
            return "Afternoon"
        return "Evening"

    df["Time Session"] = df["Hour"].astype(int).apply(assign_time_session)

    month_map = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "Apr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dec",
    }
    df["Month Name"] = df["Month"].astype(int).map(month_map)

    if "Weekday.1" in df.columns:
        df["Weekday Name"] = df["Weekday.1"].astype(str)
    else:
        df["Weekday Name"] = df["transaction_date"].dt.strftime("%a")

    return df


def get_data():
    try:
        return load_data()
    except FileNotFoundError:
        st.error(
            "The dataset could not be found. Make sure **data/coffee_shop.xlsx** exists."
        )
        st.stop()
    except Exception as error:
        st.error(f"Unable to load the dataset.\n\n{error}")
        st.stop()
