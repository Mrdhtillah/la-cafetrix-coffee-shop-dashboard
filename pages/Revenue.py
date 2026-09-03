import plotly.express as px
import streamlit as st

from sidebar import show_sidebar
from utils.filters import sidebar_filters
from utils.load_data import get_data
from utils.ui import COFFEE_COLORS, chart_config, empty_state, insight_box, style_plotly, compact_currency, compact_number, compact_table


st.set_page_config(page_title="Revenue Analysis", layout="wide", page_icon="☕")
show_sidebar()

st.title("Revenue Analysis")
st.caption("How is revenue changing, and which categories and stores contribute most?")

df = get_data()
filtered = sidebar_filters(df, page_key="revenue")

if filtered.empty:
    empty_state()
    st.stop()

total_revenue = filtered["Revenue"].sum()
total_transactions = filtered["transaction_id"].nunique()
avg_transaction = total_revenue / total_transactions if total_transactions else 0

monthly = (
    filtered.assign(Month_Start=filtered["transaction_date"].dt.to_period("M").dt.to_timestamp())
    .groupby("Month_Start", as_index=False)
    .agg(Revenue=("Revenue", "sum"), Transactions=("transaction_id", "nunique"))
    .sort_values("Month_Start")
)
monthly["Month"] = monthly["Month_Start"].dt.strftime("%b %Y")
category = (
    filtered.groupby("product_category", as_index=False)
    .agg(Revenue=("Revenue", "sum"), Transactions=("transaction_id", "nunique"), Units=("transaction_qty", "sum"))
    .sort_values("Revenue", ascending=False)
)
store = (
    filtered.groupby("store_location", as_index=False)
    .agg(Revenue=("Revenue", "sum"), Transactions=("transaction_id", "nunique"))
    .sort_values("Revenue", ascending=False)
)

best_period = monthly.iloc[monthly["Revenue"].argmax()]
best_category = category.iloc[0]
best_store = store.iloc[0]

st.subheader("Revenue Overview")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", compact_currency(total_revenue))
k2.metric("Average Transaction", compact_currency(avg_transaction))
k3.metric("Best Month", best_period["Month"], help=f"{compact_currency(best_period['Revenue'])} revenue")
k4.metric("Top Revenue Category", best_category["product_category"], help=f"{compact_currency(best_category['Revenue'])} revenue")

st.divider()
st.subheader("How is revenue changing over time?")
span_days = (filtered["transaction_date"].max() - filtered["transaction_date"].min()).days
if span_days <= 45:
    trend = (
        filtered.groupby("transaction_date", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Transactions=("transaction_id", "nunique"))
        .sort_values("transaction_date")
    )
    trend["Label"] = trend["transaction_date"].dt.strftime("%d %b")
    x = "transaction_date"
    x_title = "Date"
else:
    trend = monthly.copy()
    trend["Label"] = trend["Month"]
    x = "Month_Start"
    x_title = "Month"

fig = px.line(
    trend,
    x=x,
    y="Revenue",
    markers=True,
    custom_data=["Label", "Transactions"],
    color_discrete_sequence=[COFFEE_COLORS[0]],
)
fig.update_traces(
    line=dict(width=3),
    marker=dict(size=8),
    hovertemplate="%{customdata[0]}<br>Revenue: $%{y:~s}<br>Transactions: %{customdata[1]:~s}<extra></extra>",
)
style_plotly(fig, x_title=x_title, y_title="Revenue ($)", height=390, showlegend=False)
st.plotly_chart(fig, use_container_width=True, config=chart_config())

st.divider()
st.subheader("What contributes most to revenue?")
left, right = st.columns(2)

with left:
    st.markdown("#### Revenue by product category")
    st.caption("A ranking is easier to compare than a multi-slice pie for nine categories.")
    plot = category.sort_values("Revenue", ascending=True)
    fig = px.bar(
        plot,
        x="Revenue",
        y="product_category",
        orientation="h",
        color_discrete_sequence=[COFFEE_COLORS[2]],
    )
    fig.update_traces(
        customdata=plot[["Transactions", "Units"]],
        hovertemplate="%{y}<br>Revenue: $%{x:~s}<br>Transactions: %{customdata[0]:~s}<br>Units sold: %{customdata[1]:~s}<extra></extra>",
    )
    style_plotly(fig, x_title="Revenue ($)", y_title=None, height=430, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

with right:
    st.markdown("#### Revenue share by category")
    st.caption("Exact share is shown as a sorted percentage bar rather than a crowded donut.")
    share = category.copy()
    share["Revenue Share"] = share["Revenue"] / share["Revenue"].sum() * 100
    share = share.sort_values("Revenue Share", ascending=True)
    fig = px.bar(
        share,
        x="Revenue Share",
        y="product_category",
        orientation="h",
        color_discrete_sequence=[COFFEE_COLORS[4]],
    )
    fig.update_traces(
        texttemplate="%{x:.1f}%",
        textposition="outside",
        hovertemplate="%{y}<br>Revenue share: %{x:.1f}%<extra></extra>",
    )
    style_plotly(fig, x_title="Share of revenue (%)", y_title=None, height=430, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

st.divider()
st.subheader("Which locations contribute most?")
plot = store.sort_values("Revenue", ascending=True)
fig = px.bar(
    plot,
    x="Revenue",
    y="store_location",
    orientation="h",
    color_discrete_sequence=[COFFEE_COLORS[1]],
)
fig.update_traces(
    customdata=plot[["Transactions"]],
    texttemplate="$%{x:~s}",
    textposition="outside",
    hovertemplate="%{y}<br>Revenue: $%{x:~s}<br>Transactions: %{customdata[0]:~s}<extra></extra>",
)
style_plotly(fig, x_title="Revenue ($)", y_title=None, height=330, showlegend=False)
st.plotly_chart(fig, use_container_width=True, config=chart_config())

category_share = best_category["Revenue"] / total_revenue * 100
store_share = best_store["Revenue"] / total_revenue * 100
insight_box(
    [
        f"<strong>{best_period['Month']}</strong> is the strongest month in the current view at <strong>{compact_currency(best_period['Revenue'])}</strong> revenue.",
        f"<strong>{best_category['product_category']}</strong> contributes the most category revenue at <strong>{category_share:.1f}%</strong> of the filtered total.",
        f"<strong>{best_store['store_location']}</strong> contributes the most store revenue at <strong>{store_share:.1f}%</strong> of the filtered total.",
        "Profit and margin are intentionally not shown because the source dataset contains revenue and price data but no cost fields.",
    ]
)

with st.expander("View revenue data"):
    tab1, tab2, tab3 = st.tabs(["Monthly", "Category", "Store"])
    with tab1:
        st.dataframe(compact_table(monthly[["Month", "Revenue", "Transactions"]], currency_columns=["Revenue"], number_columns=["Transactions"]), use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(compact_table(category, currency_columns=["Revenue"], number_columns=["Transactions", "Units"]), use_container_width=True, hide_index=True)
    with tab3:
        st.dataframe(compact_table(store, currency_columns=["Revenue"], number_columns=["Transactions"]), use_container_width=True, hide_index=True)
