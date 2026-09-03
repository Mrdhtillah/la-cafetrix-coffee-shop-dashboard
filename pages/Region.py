import plotly.express as px
import streamlit as st

from sidebar import show_sidebar
from utils.filters import sidebar_filters
from utils.load_data import get_data
from utils.ui import COFFEE_COLORS, chart_config, empty_state, insight_box, style_plotly, compact_currency, compact_number, compact_table


st.set_page_config(page_title="Region Insights", layout="wide", page_icon="☕")
show_sidebar()

st.title("Region Insights")
st.caption("Which stores perform best, and how do their sales patterns differ?")

df = get_data()
filtered = sidebar_filters(df, page_key="region")

if filtered.empty:
    empty_state()
    st.stop()

store_summary = (
    filtered.groupby("store_location", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Transactions=("transaction_id", "nunique"),
        Quantity=("transaction_qty", "sum"),
    )
)
store_summary["Revenue per Transaction"] = store_summary["Revenue"] / store_summary["Transactions"]
store_summary["Items per Transaction"] = store_summary["Quantity"] / store_summary["Transactions"]

best_store = store_summary.sort_values("Revenue", ascending=False).iloc[0]
highest_ticket = store_summary.sort_values("Revenue per Transaction", ascending=False).iloc[0]
largest_basket = store_summary.sort_values("Items per Transaction", ascending=False).iloc[0]
lowest_store = store_summary.sort_values("Revenue", ascending=True).iloc[0]

st.subheader("Store Overview")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Active Stores", compact_number(store_summary['store_location'].nunique()))
k2.metric("Top Revenue Store", best_store["store_location"], help=f"{compact_currency(best_store['Revenue'])} revenue")
k3.metric("Highest Avg Transaction", highest_ticket["store_location"], help=f"{compact_currency(highest_ticket['Revenue per Transaction'])} per transaction")
k4.metric("Largest Avg Basket", largest_basket["store_location"], help=f"{largest_basket['Items per Transaction']:.2f} items per transaction")

st.divider()
st.subheader("How do stores compare?")
metric_choice = st.radio(
    "Compare stores by",
    ["Revenue", "Transactions", "Units Sold", "Average Transaction Value", "Average Basket Size"],
    horizontal=True,
    key="region_metric",
)
metric_map = {
    "Revenue": "Revenue",
    "Transactions": "Transactions",
    "Units Sold": "Quantity",
    "Average Transaction Value": "Revenue per Transaction",
    "Average Basket Size": "Items per Transaction",
}
metric = metric_map[metric_choice]
metric_label = {
    "Revenue": "Revenue ($)",
    "Transactions": "Transactions",
    "Quantity": "Units sold",
    "Revenue per Transaction": "Average transaction value ($)",
    "Items per Transaction": "Average items per transaction",
}[metric]
store_plot = store_summary.sort_values(metric, ascending=True)
fig = px.bar(
    store_plot,
    x=metric,
    y="store_location",
    orientation="h",
    color_discrete_sequence=[COFFEE_COLORS[1]],
)
fig.update_traces(
    customdata=store_plot[["Revenue", "Transactions", "Quantity", "Revenue per Transaction", "Items per Transaction"]],
    hovertemplate=(
        "%{y}<br>Revenue: $%{customdata[0]:~s}<br>Transactions: %{customdata[1]:~s}<br>Units sold: %{customdata[2]:~s}<br>Avg transaction: $%{customdata[3]:.2f}<br>Avg basket: %{customdata[4]:.2f} items<extra></extra>"
    ),
)
style_plotly(fig, x_title=metric_label, y_title=None, height=340, showlegend=False)
st.plotly_chart(fig, use_container_width=True, config=chart_config())

st.divider()
st.subheader("How is each store performing over time?")
st.caption("Monthly revenue comparison makes it easier to see whether store leadership is consistent or changes over time.")
store_month = (
    filtered.assign(Month_Start=filtered["transaction_date"].dt.to_period("M").dt.to_timestamp())
    .groupby(["Month_Start", "store_location"], as_index=False)
    .agg(Revenue=("Revenue", "sum"), Transactions=("transaction_id", "nunique"))
    .sort_values("Month_Start")
)
store_month["Month"] = store_month["Month_Start"].dt.strftime("%b %Y")
fig = px.line(
    store_month,
    x="Month_Start",
    y="Revenue",
    color="store_location",
    markers=True,
    color_discrete_sequence=COFFEE_COLORS,
    custom_data=["Month", "Transactions"],
)
fig.update_traces(
    line=dict(width=3),
    marker=dict(size=7),
    hovertemplate="%{customdata[0]}<br>Revenue: $%{y:~s}<br>Transactions: %{customdata[1]:~s}<extra></extra>",
)
style_plotly(fig, x_title="Month", y_title="Revenue ($)", height=400)
st.plotly_chart(fig, use_container_width=True, config=chart_config())

st.divider()
st.subheader("What drives each store's revenue?")
st.caption("Category composition is shown as a stacked bar because the goal is to compare each store's revenue mix.")
store_category = (
    filtered.groupby(["store_location", "product_category"], as_index=False)
    .agg(Revenue=("Revenue", "sum"))
)
fig = px.bar(
    store_category,
    x="store_location",
    y="Revenue",
    color="product_category",
    color_discrete_sequence=COFFEE_COLORS,
)
fig.update_traces(hovertemplate="%{x}<br>%{fullData.name}: $%{y:~s}<extra></extra>")
style_plotly(fig, x_title="Store location", y_title="Revenue ($)", height=430)
st.plotly_chart(fig, use_container_width=True, config=chart_config())

st.divider()
st.subheader("Do larger baskets correspond to higher transaction values?")
st.caption("Each bubble is a store; bubble size represents transaction count.")
fig = px.scatter(
    store_summary,
    x="Items per Transaction",
    y="Revenue per Transaction",
    size="Transactions",
    text="store_location",
    color="store_location",
    color_discrete_sequence=COFFEE_COLORS,
    size_max=32,
)
fig.update_traces(
    textposition="top center",
    hovertemplate=(
        "%{text}<br>Avg basket: %{x:.2f} items<br>Avg transaction: $%{y:.2f}<br>Transactions: %{marker.size:~s}<extra></extra>"
    ),
)
style_plotly(fig, x_title="Average items per transaction", y_title="Average transaction value ($)", height=390, showlegend=False)
st.plotly_chart(fig, use_container_width=True, config=chart_config())

revenue_share = best_store["Revenue"] / store_summary["Revenue"].sum() * 100
insight_items = [
    f"<strong>{best_store['store_location']}</strong> generates the most revenue at <strong>{compact_currency(best_store['Revenue'])}</strong>, or <strong>{revenue_share:.1f}%</strong> of revenue across the currently selected stores.",
    f"<strong>{highest_ticket['store_location']}</strong> has the highest average transaction value at <strong>{compact_currency(highest_ticket['Revenue per Transaction'])}</strong>.",
    f"<strong>{largest_basket['store_location']}</strong> has the largest average basket at <strong>{largest_basket['Items per Transaction']:.2f} items</strong>.",
]
if len(store_summary) > 1:
    insight_items.append(
        f"<strong>{lowest_store['store_location']}</strong> currently has the lowest revenue among the selected stores, making it the clearest location to inspect for performance gaps."
    )
insight_box(insight_items)

with st.expander("View store data"):
    table = store_summary.rename(
        columns={
            "store_location": "Store Location",
            "Quantity": "Units Sold",
            "Revenue per Transaction": "Avg Transaction Value",
            "Items per Transaction": "Avg Basket Size",
        }
    ).sort_values("Revenue", ascending=False)
    table_display = table.copy()
    table_display["Revenue"] = table_display["Revenue"].map(compact_currency)
    table_display["Transactions"] = table_display["Transactions"].map(compact_number)
    table_display["Units Sold"] = table_display["Units Sold"].map(compact_number)
    table_display["Avg Transaction Value"] = table_display["Avg Transaction Value"].map(lambda value: f"${value:.2f}")
    table_display["Avg Basket Size"] = table_display["Avg Basket Size"].map(lambda value: f"{value:.2f}")
    st.dataframe(table_display, use_container_width=True, hide_index=True)
    st.download_button(
        "Download store breakdown",
        table.to_csv(index=False).encode("utf-8"),
        file_name="coffee_shop_store_breakdown.csv",
        mime="text/csv",
    )
