from datetime import date

import pandas as pd
import streamlit as st


MONTH_LABELS = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def clear_filter_state():
    for key in list(st.session_state.keys()):
        if key.startswith("coffee_filter_"):
            del st.session_state[key]


def sidebar_filters(df, page_key="core", include_product=False, include_session=False):
    """Apply one consistent filter state to all metrics and charts on a page."""
    min_date = df["transaction_date"].min().date()
    max_date = df["transaction_date"].max().date()

    month_numbers = sorted(df["Month"].dropna().astype(int).unique())
    period_options = ["Full period"] + [MONTH_LABELS[m] for m in month_numbers] + ["Custom range"]

    st.sidebar.markdown("### Filter data")
    st.sidebar.caption("These filters update every KPI, chart, insight, and table on this page.")

    period = st.sidebar.selectbox(
        "Period",
        options=period_options,
        key="coffee_filter_period",
    )

    if period == "Full period":
        start_date, end_date = min_date, max_date
    elif period == "Custom range":
        selected_range = st.sidebar.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="coffee_filter_custom_dates",
        )
        if isinstance(selected_range, (tuple, list)) and len(selected_range) == 2:
            start_date, end_date = selected_range
        else:
            start_date = end_date = selected_range
    else:
        selected_month = next(
            month for month, label in MONTH_LABELS.items() if label == period
        )
        month_dates = df.loc[df["Month"].astype(int).eq(selected_month), "transaction_date"]
        start_date = month_dates.min().date()
        end_date = month_dates.max().date()

    stores = sorted(df["store_location"].dropna().unique().tolist())
    categories = sorted(df["product_category"].dropna().unique().tolist())

    selected_stores = st.sidebar.multiselect(
        "Store location",
        options=stores,
        default=stores,
        key="coffee_filter_stores",
    )
    selected_categories = st.sidebar.multiselect(
        "Product category",
        options=categories,
        default=categories,
        key="coffee_filter_categories",
    )

    selected_products = None
    if include_product:
        products = sorted(df["product_name_clean"].dropna().unique().tolist())
        selected_products = st.sidebar.multiselect(
            "Product",
            options=products,
            default=products,
            key="coffee_filter_products",
        )

    selected_sessions = None
    if include_session:
        session_order = ["Morning", "Midday", "Afternoon", "Evening"]
        sessions = [s for s in session_order if s in df["Time Session"].unique()]
        selected_sessions = st.sidebar.multiselect(
            "Time session",
            options=sessions,
            default=sessions,
            key="coffee_filter_sessions",
        )

    date_mask = df["transaction_date"].dt.date.between(start_date, end_date)
    filtered = df[
        date_mask
        & df["store_location"].isin(selected_stores)
        & df["product_category"].isin(selected_categories)
    ].copy()

    if include_product:
        filtered = filtered[filtered["product_name_clean"].isin(selected_products)].copy()
    if include_session:
        filtered = filtered[filtered["Time Session"].isin(selected_sessions)].copy()

    active_filters = []
    if period != "Full period":
        active_filters.append(period if period != "Custom range" else f"{start_date:%d %b} – {end_date:%d %b}")
    if len(selected_stores) != len(stores):
        active_filters.append(f"{len(selected_stores)} store(s)")
    if len(selected_categories) != len(categories):
        active_filters.append(f"{len(selected_categories)} category(s)")
    if include_product:
        total_products = df["product_name_clean"].nunique()
        if len(selected_products) != total_products:
            active_filters.append(f"{len(selected_products)} product(s)")
    if include_session:
        total_sessions = df["Time Session"].nunique()
        if len(selected_sessions) != total_sessions:
            active_filters.append(f"{len(selected_sessions)} session(s)")

    if active_filters:
        st.sidebar.markdown("**Active:** " + " · ".join(active_filters))
    else:
        st.sidebar.caption("Showing the full dataset.")

    st.sidebar.button(
        "Clear filters",
        key=f"clear_filters_{page_key}",
        on_click=clear_filter_state,
        use_container_width=True,
    )

    st.sidebar.caption(f"Data range: {min_date:%d %b %Y} – {max_date:%d %b %Y}")

    return filtered
