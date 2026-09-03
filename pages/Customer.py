import plotly.express as px
import streamlit as st

from sidebar import show_sidebar
from utils.filters import sidebar_filters
from utils.load_data import get_data
from utils.ui import COFFEE_COLORS, chart_config, empty_state, insight_box, style_plotly, compact_currency, compact_number, compact_table


st.set_page_config(page_title="Customer Insights", layout="wide", page_icon="☕")
show_sidebar()

st.title("Customer Insights")
st.caption("How much do customers spend, how large are their baskets, and when is purchase activity strongest?")

df = get_data()
filtered = sidebar_filters(df, page_key="customer", include_session=True)

if filtered.empty:
    empty_state()
    st.stop()

# One row in the source data represents one transaction. This aggregation remains
# robust if the source later contains multiple line items per transaction.
transaction_summary = (
    filtered.groupby("transaction_id", as_index=False)
    .agg(
        Spend=("Revenue", "sum"),
        Items=("transaction_qty", "sum"),
        Hour=("Hour", "first"),
        Store=("store_location", "first"),
        Time_Session=("Time Session", "first"),
    )
)

total_transactions = len(transaction_summary)
average_spend = transaction_summary["Spend"].mean()
median_spend = transaction_summary["Spend"].median()
average_items = transaction_summary["Items"].mean()
largest_basket = transaction_summary["Items"].max()
single_item_percentage = transaction_summary["Items"].eq(1).mean() * 100

hour_summary = (
    transaction_summary.groupby("Hour", as_index=False)
    .agg(Transactions=("transaction_id", "count"), Average_Spend=("Spend", "mean"))
    .sort_values("Hour")
)
store_summary = (
    transaction_summary.groupby("Store", as_index=False)
    .agg(
        Average_Spend=("Spend", "mean"),
        Average_Basket=("Items", "mean"),
        Transactions=("transaction_id", "count"),
    )
)

peak_hour = hour_summary.loc[hour_summary["Transactions"].idxmax()]
common_basket = int(transaction_summary["Items"].value_counts().idxmax())
highest_spend_store = store_summary.sort_values("Average_Spend", ascending=False).iloc[0]

st.subheader("Customer Purchase Overview")
k1, k2, k3 = st.columns(3)
k4, k5, k6 = st.columns(3)
k1.metric("Total Transactions", compact_number(total_transactions))
k2.metric("Average Spend", compact_currency(average_spend))
k3.metric("Median Spend", compact_currency(median_spend))
k4.metric("Average Basket Size", f"{average_items:.2f} items")
k5.metric("Single-Item Orders", f"{single_item_percentage:.1f}%")
k6.metric("Largest Basket", f"{compact_number(largest_basket)} items")

st.divider()
st.subheader("What do typical purchases look like?")
left, right = st.columns(2)

with left:
    st.markdown("#### Transaction value distribution")
    st.caption("The 99th percentile display limit prevents unusually large values from flattening the main pattern; source rows are not removed.")
    spend_limit = transaction_summary["Spend"].quantile(0.99)
    spend_plot = transaction_summary[transaction_summary["Spend"] <= spend_limit]
    fig = px.histogram(
        spend_plot,
        x="Spend",
        nbins=24,
        color_discrete_sequence=[COFFEE_COLORS[0]],
    )
    fig.update_traces(
        hovertemplate="Transaction value: $%{x:.2f}<br>Transactions: %{y:~s}<extra></extra>"
    )
    style_plotly(fig, x_title="Transaction value ($)", y_title="Transactions", height=390, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

with right:
    st.markdown("#### Basket size distribution")
    st.caption("Shows how many items customers typically purchase in one transaction.")
    basket = (
        transaction_summary.groupby("Items", as_index=False)
        .agg(Transactions=("transaction_id", "count"))
        .sort_values("Items")
    )
    fig = px.bar(
        basket,
        x="Items",
        y="Transactions",
        color_discrete_sequence=[COFFEE_COLORS[2]],
    )
    fig.update_traces(
        hovertemplate="Basket size: %{x:.0f} items<br>Transactions: %{y:~s}<extra></extra>"
    )
    style_plotly(fig, x_title="Items per transaction", y_title="Transactions", height=390, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

st.divider()
st.subheader("When and where do customers spend more?")
left, right = st.columns(2)

with left:
    st.markdown("#### Average spend by hour")
    st.caption("Identifies hours where the average transaction is worth more.")
    fig = px.line(
        hour_summary,
        x="Hour",
        y="Average_Spend",
        markers=True,
        color_discrete_sequence=[COFFEE_COLORS[0]],
    )
    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=7),
        customdata=hour_summary[["Transactions"]],
        hovertemplate="%{x}:00<br>Average spend: $%{y:.2f}<br>Transactions: %{customdata[0]:~s}<extra></extra>",
    )
    style_plotly(fig, x_title="Hour of day", y_title="Average spend ($)", height=390, showlegend=False)
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

with right:
    st.markdown("#### Store purchase behaviour")
    st.caption("Stores toward the upper-right combine larger baskets with higher average transaction values.")
    fig = px.scatter(
        store_summary,
        x="Average_Basket",
        y="Average_Spend",
        size="Transactions",
        text="Store",
        color="Store",
        color_discrete_sequence=COFFEE_COLORS,
        size_max=32,
    )
    fig.update_traces(
        textposition="top center",
        hovertemplate="%{text}<br>Average basket: %{x:.2f} items<br>Average spend: $%{y:.2f}<br>Transactions: %{marker.size:~s}<extra></extra>",
    )
    style_plotly(fig, x_title="Average items per transaction", y_title="Average spend ($)", height=390, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

st.divider()
st.subheader("How does spending differ by time session?")
session_order = ["Morning", "Midday", "Afternoon", "Evening"]
session_summary = (
    transaction_summary.groupby("Time_Session", as_index=False)
    .agg(
        Transactions=("transaction_id", "count"),
        Average_Spend=("Spend", "mean"),
        Average_Basket=("Items", "mean"),
    )
)
session_summary["Order"] = session_summary["Time_Session"].map({name: i for i, name in enumerate(session_order)})
session_summary = session_summary.sort_values("Order")
fig = px.bar(
    session_summary,
    x="Time_Session",
    y="Transactions",
    color_discrete_sequence=[COFFEE_COLORS[3]],
)
fig.update_traces(
    customdata=session_summary[["Average_Spend", "Average_Basket"]],
    hovertemplate="%{x}<br>Transactions: %{y:~s}<br>Average spend: $%{customdata[0]:.2f}<br>Average basket: %{customdata[1]:.2f} items<extra></extra>",
)
style_plotly(fig, x_title="Time session", y_title="Transactions", height=350, showlegend=False)
st.plotly_chart(fig, use_container_width=True, config=chart_config())

insight_box(
    [
        f"Customers spend an average of <strong>{compact_currency(average_spend)}</strong> per transaction; the median is <strong>{compact_currency(median_spend)}</strong>.",
        f"The most common basket contains <strong>{common_basket} item(s)</strong>, while <strong>{single_item_percentage:.1f}%</strong> of transactions contain one item.",
        f"Transaction activity peaks around <strong>{int(peak_hour['Hour'])}:00</strong> with <strong>{compact_number(peak_hour['Transactions'])}</strong> transactions.",
        f"<strong>{highest_spend_store['Store']}</strong> records the highest average transaction value at <strong>${highest_spend_store['Average_Spend']:.2f}</strong>.",
    ]
)

with st.expander("View customer transaction data"):
    store_table = store_summary.rename(
        columns={
            "Store": "Store Location",
            "Average_Spend": "Average Spend",
            "Average_Basket": "Average Basket",
        }
    )
    store_display = store_table.copy()
    store_display["Average Spend"] = store_display["Average Spend"].map(lambda value: f"${value:.2f}")
    store_display["Average Basket"] = store_display["Average Basket"].map(lambda value: f"{value:.2f}")
    store_display["Transactions"] = store_display["Transactions"].map(compact_number)
    st.dataframe(store_display, use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered transaction summary",
        transaction_summary.to_csv(index=False).encode("utf-8"),
        file_name="coffee_shop_customer_transactions.csv",
        mime="text/csv",
    )
