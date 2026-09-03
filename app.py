import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sidebar import show_sidebar
from utils.filters import sidebar_filters
from utils.load_data import get_data
from utils.ui import COFFEE_COLORS, chart_config, empty_state, insight_box, style_plotly, compact_currency, compact_number, compact_table


st.set_page_config(
    page_title="La Cafètrix Dashboard",
    page_icon="☕",
    layout="wide",
)
show_sidebar()

st.title("Coffee Shop Performance Overview")
st.caption(
    "A quick view of what is happening, what is driving performance, where sales are strongest, and when customers are most active."
)

df = get_data()
filtered = sidebar_filters(df, page_key="overview")

if filtered.empty:
    empty_state()
    st.stop()

# -------------------------------------------------------------------
# KPI overview
# -------------------------------------------------------------------
total_revenue = filtered["Revenue"].sum()
total_transactions = filtered["transaction_id"].nunique()
units_sold = filtered["transaction_qty"].sum()
avg_transaction = total_revenue / total_transactions if total_transactions else 0

product_summary = (
    filtered.groupby("product_name_clean", as_index=False)
    .agg(Revenue=("Revenue", "sum"), Units=("transaction_qty", "sum"))
    .sort_values("Revenue", ascending=False)
)
store_summary = (
    filtered.groupby("store_location", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Transactions=("transaction_id", "nunique"),
        Units=("transaction_qty", "sum"),
    )
    .sort_values("Revenue", ascending=False)
)
category_summary = (
    filtered.groupby("product_category", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Transactions=("transaction_id", "nunique"),
        Units=("transaction_qty", "sum"),
    )
    .sort_values("Revenue", ascending=False)
)

top_product = product_summary.iloc[0]
top_store = store_summary.iloc[0]

st.subheader("Overview")
k1, k2, k3 = st.columns(3)
k4, k5, k6 = st.columns(3)

k1.metric("Total Revenue", compact_currency(total_revenue), help="Revenue from the filtered transaction data.")
k2.metric("Transactions", compact_number(total_transactions), help="Unique transaction IDs in the filtered data.")
k3.metric("Units Sold", compact_number(units_sold), help="Sum of transaction quantity.")
k4.metric("Average Transaction", compact_currency(avg_transaction), help="Revenue divided by unique transactions.")
k5.metric("Top Revenue Product", top_product["product_name_clean"], help=f"{compact_currency(top_product['Revenue'])} revenue.")
k6.metric("Top Revenue Store", top_store["store_location"], help=f"{compact_currency(top_store['Revenue'])} revenue.")

# -------------------------------------------------------------------
# Performance trend
# -------------------------------------------------------------------
st.divider()
st.subheader("What is happening over time?")
st.caption("Revenue trend with transaction counts available in the tooltip.")

span_days = (filtered["transaction_date"].max() - filtered["transaction_date"].min()).days
if span_days <= 45:
    trend = (
        filtered.groupby("transaction_date", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Transactions=("transaction_id", "nunique"))
        .sort_values("transaction_date")
    )
    trend["Period"] = trend["transaction_date"].dt.strftime("%d %b")
    x_col = "transaction_date"
    x_title = "Date"
else:
    trend = (
        filtered.assign(Month_Start=filtered["transaction_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("Month_Start", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Transactions=("transaction_id", "nunique"))
        .sort_values("Month_Start")
    )
    trend["Period"] = trend["Month_Start"].dt.strftime("%b %Y")
    x_col = "Month_Start"
    x_title = "Month"

trend_fig = px.line(
    trend,
    x=x_col,
    y="Revenue",
    markers=True,
    color_discrete_sequence=[COFFEE_COLORS[0]],
    custom_data=["Period", "Transactions"],
)
trend_fig.update_traces(
    line=dict(width=3),
    marker=dict(size=8),
    hovertemplate=(
        "%{customdata[0]}<br>Revenue: $%{y:~s}<br>Transactions: %{customdata[1]:~s}<extra></extra>"
    ),
)
style_plotly(trend_fig, x_title=x_title, y_title="Revenue ($)", height=390, showlegend=False)
st.plotly_chart(trend_fig, use_container_width=True, config=chart_config())

# -------------------------------------------------------------------
# Product/category drivers
# -------------------------------------------------------------------
st.divider()
st.subheader("What is driving performance?")
left, right = st.columns(2)

with left:
    st.markdown("#### Top products by revenue")
    st.caption("The ten products contributing the most revenue in the current filter state.")
    top_products = product_summary.head(10).sort_values("Revenue", ascending=True)
    fig = px.bar(
        top_products,
        x="Revenue",
        y="product_name_clean",
        orientation="h",
        color_discrete_sequence=[COFFEE_COLORS[1]],
    )
    fig.update_traces(
        hovertemplate="%{y}<br>Revenue: $%{x:~s}<extra></extra>"
    )
    style_plotly(fig, x_title="Revenue ($)", y_title=None, height=430, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

with right:
    st.markdown("#### Product category performance")
    st.caption("A category-level revenue ranking, making contribution differences easy to compare.")
    category_plot = category_summary.sort_values("Revenue", ascending=True)
    fig = px.bar(
        category_plot,
        x="Revenue",
        y="product_category",
        orientation="h",
        color_discrete_sequence=[COFFEE_COLORS[2]],
    )
    fig.update_traces(
        customdata=category_plot[["Units", "Transactions"]],
        hovertemplate=(
            "%{y}<br>Revenue: $%{x:~s}<br>Units sold: %{customdata[0]:~s}<br>Transactions: %{customdata[1]:~s}<extra></extra>"
        ),
    )
    style_plotly(fig, x_title="Revenue ($)", y_title=None, height=430, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

# -------------------------------------------------------------------
# Store performance
# -------------------------------------------------------------------
st.divider()
st.subheader("Where is performance strongest?")
st.caption("Compare store revenue directly; exact transaction and unit figures are available on hover.")
store_plot = store_summary.sort_values("Revenue", ascending=True)
fig = px.bar(
    store_plot,
    x="Revenue",
    y="store_location",
    orientation="h",
    color_discrete_sequence=[COFFEE_COLORS[0]],
)
fig.update_traces(
    customdata=store_plot[["Transactions", "Units"]],
    texttemplate="$%{x:~s}",
    textposition="outside",
    cliponaxis=False,
    hovertemplate=(
        "%{y}<br>Revenue: $%{x:~s}<br>Transactions: %{customdata[0]:~s}<br>Units sold: %{customdata[1]:~s}<extra></extra>"
    ),
)
style_plotly(fig, x_title="Revenue ($)", y_title=None, height=330, showlegend=False)
st.plotly_chart(fig, use_container_width=True, config=chart_config())

# -------------------------------------------------------------------
# Time analysis
# -------------------------------------------------------------------
st.divider()
st.subheader("When are customers most active?")
st.caption("Transaction volume by weekday and hour. Darker cells indicate busier periods.")

weekday_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
hourly = (
    filtered.groupby(["Weekday Name", "Hour"], as_index=False)
    .agg(Transactions=("transaction_id", "nunique"), Revenue=("Revenue", "sum"))
)
pivot = (
    hourly.pivot(index="Weekday Name", columns="Hour", values="Transactions")
    .reindex(weekday_order)
    .fillna(0)
)

heatmap = go.Figure(
    data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, "#F3EAE1"],
            [0.35, "#DDB892"],
            [0.7, "#A67C52"],
            [1.0, "#4A3326"],
        ],
        colorbar=dict(title="Transactions"),
        hovertemplate="%{y}, %{x}:00<br>Transactions: %{z:~s}<extra></extra>",
    )
)
style_plotly(heatmap, x_title="Hour of day", y_title=None, height=390, showlegend=False)
heatmap.update_xaxes(dtick=1)
st.plotly_chart(heatmap, use_container_width=True, config=chart_config())

# -------------------------------------------------------------------
# Dynamic insights + detail
# -------------------------------------------------------------------
peak_hour_row = (
    filtered.groupby("Hour", as_index=False)
    .agg(Transactions=("transaction_id", "nunique"), Revenue=("Revenue", "sum"))
    .sort_values("Transactions", ascending=False)
    .iloc[0]
)
peak_day_row = (
    filtered.groupby("Weekday Name", as_index=False)
    .agg(Transactions=("transaction_id", "nunique"), Revenue=("Revenue", "sum"))
    .sort_values("Revenue", ascending=False)
    .iloc[0]
)
top_category = category_summary.iloc[0]

insight_box(
    [
        f"<strong>{top_product['product_name_clean']}</strong> is the highest-revenue product at <strong>{compact_currency(top_product['Revenue'])}</strong>.",
        f"<strong>{top_category['product_category']}</strong> is the highest-revenue category, contributing <strong>{top_category['Revenue'] / total_revenue * 100:.1f}%</strong> of filtered revenue.",
        f"<strong>{top_store['store_location']}</strong> leads store revenue at <strong>{compact_currency(top_store['Revenue'])}</strong>.",
        f"Customer activity is busiest around <strong>{int(peak_hour_row['Hour'])}:00</strong> with <strong>{compact_number(peak_hour_row['Transactions'])}</strong> transactions.",
        f"<strong>{peak_day_row['Weekday Name']}</strong> generates the most revenue by weekday in the current filter state.",
    ]
)

with st.expander("View detailed breakdown"):
    detail = (
        filtered.groupby(["store_location", "product_category"], as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Transactions=("transaction_id", "nunique"),
            Units_Sold=("transaction_qty", "sum"),
        )
        .sort_values("Revenue", ascending=False)
        .rename(
            columns={
                "store_location": "Store Location",
                "product_category": "Product Category",
                "Units_Sold": "Units Sold",
            }
        )
    )
    detail_display = compact_table(detail, currency_columns=["Revenue"], number_columns=["Transactions", "Units Sold"])
    st.dataframe(detail_display, use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered breakdown",
        detail.to_csv(index=False).encode("utf-8"),
        file_name="coffee_shop_filtered_breakdown.csv",
        mime="text/csv",
    )
