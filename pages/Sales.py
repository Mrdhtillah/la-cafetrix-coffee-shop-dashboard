import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sidebar import show_sidebar
from utils.filters import sidebar_filters
from utils.load_data import get_data
from utils.ui import COFFEE_COLORS, chart_config, empty_state, insight_box, style_plotly, compact_currency, compact_number, compact_table


st.set_page_config(page_title="Sales & Operations", layout="wide", page_icon="☕")
show_sidebar()

st.title("Sales & Operations")
st.caption("When are sales happening, and which periods carry the most customer activity?")

df = get_data()
filtered = sidebar_filters(df, page_key="sales")

if filtered.empty:
    empty_state()
    st.stop()

hour_summary = (
    filtered.groupby("Hour", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Transactions=("transaction_id", "nunique"),
        Units=("transaction_qty", "sum"),
    )
    .sort_values("Hour")
)
weekday_summary = (
    filtered.groupby("Weekday Name", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Transactions=("transaction_id", "nunique"),
        Units=("transaction_qty", "sum"),
    )
)
monthly_summary = (
    filtered.assign(Month_Start=filtered["transaction_date"].dt.to_period("M").dt.to_timestamp())
    .groupby("Month_Start", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        Transactions=("transaction_id", "nunique"),
        Units=("transaction_qty", "sum"),
    )
    .sort_values("Month_Start")
)

total_revenue = filtered["Revenue"].sum()
total_transactions = filtered["transaction_id"].nunique()
units_sold = filtered["transaction_qty"].sum()
peak_hour = hour_summary.loc[hour_summary["Transactions"].idxmax()]
peak_revenue_hour = hour_summary.loc[hour_summary["Revenue"].idxmax()]
peak_day = weekday_summary.loc[weekday_summary["Revenue"].idxmax()]

st.subheader("Sales Overview")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Revenue", compact_currency(total_revenue))
k2.metric("Transactions", compact_number(total_transactions))
k3.metric("Units Sold", compact_number(units_sold))
k4.metric("Busiest Hour", f"{int(peak_hour['Hour'])}:00", help=f"{compact_number(peak_hour['Transactions'])} transactions")
k5.metric("Top Revenue Day", peak_day["Weekday Name"], help=f"{compact_currency(peak_day['Revenue'])} revenue")

st.divider()
st.subheader("How is performance changing over time?")
span_days = (filtered["transaction_date"].max() - filtered["transaction_date"].min()).days
if span_days <= 45:
    trend = (
        filtered.groupby("transaction_date", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Transactions=("transaction_id", "nunique"))
        .sort_values("transaction_date")
    )
    trend["Label"] = trend["transaction_date"].dt.strftime("%d %b")
    x_col = "transaction_date"
    x_title = "Date"
else:
    trend = monthly_summary.copy()
    trend["Label"] = trend["Month_Start"].dt.strftime("%b %Y")
    x_col = "Month_Start"
    x_title = "Month"

fig = px.line(
    trend,
    x=x_col,
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
st.subheader("What times are busiest?")
left, right = st.columns(2)

with left:
    st.markdown("#### Transactions by hour")
    st.caption("Use this to identify staffing and service-demand peaks.")
    fig = px.bar(
        hour_summary,
        x="Hour",
        y="Transactions",
        color_discrete_sequence=[COFFEE_COLORS[2]],
    )
    fig.update_traces(
        customdata=hour_summary[["Revenue", "Units"]],
        hovertemplate="%{x}:00<br>Transactions: %{y:~s}<br>Revenue: $%{customdata[0]:~s}<br>Units sold: %{customdata[1]:~s}<extra></extra>",
    )
    style_plotly(fig, x_title="Hour of day", y_title="Transactions", height=380, showlegend=False)
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

with right:
    st.markdown("#### Revenue by hour")
    st.caption("Shows whether the busiest periods are also the highest-value periods.")
    fig = px.line(
        hour_summary,
        x="Hour",
        y="Revenue",
        markers=True,
        color_discrete_sequence=[COFFEE_COLORS[0]],
    )
    fig.update_traces(
        line=dict(width=3),
        marker=dict(size=7),
        customdata=hour_summary[["Transactions"]],
        hovertemplate="%{x}:00<br>Revenue: $%{y:~s}<br>Transactions: %{customdata[0]:~s}<extra></extra>",
    )
    style_plotly(fig, x_title="Hour of day", y_title="Revenue ($)", height=380, showlegend=False)
    fig.update_xaxes(dtick=1)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

st.divider()
st.subheader("How do weekday and hour patterns interact?")
st.caption("Transaction heatmap: darker cells represent higher customer activity.")
weekday_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
heat = (
    filtered.groupby(["Weekday Name", "Hour"], as_index=False)
    .agg(Transactions=("transaction_id", "nunique"))
    .pivot(index="Weekday Name", columns="Hour", values="Transactions")
    .reindex(weekday_order)
    .fillna(0)
)
fig = go.Figure(
    go.Heatmap(
        z=heat.values,
        x=heat.columns.tolist(),
        y=heat.index.tolist(),
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
style_plotly(fig, x_title="Hour of day", y_title=None, height=390, showlegend=False)
fig.update_xaxes(dtick=1)
st.plotly_chart(fig, use_container_width=True, config=chart_config())

st.divider()
st.subheader("Period comparison")
if len(monthly_summary) > 1:
    monthly_summary["Month"] = monthly_summary["Month_Start"].dt.strftime("%b")
    fig = px.bar(
        monthly_summary,
        x="Month",
        y="Revenue",
        color_discrete_sequence=[COFFEE_COLORS[1]],
    )
    fig.update_traces(
        customdata=monthly_summary[["Transactions", "Units"]],
        texttemplate="$%{y:~s}",
        textposition="outside",
        hovertemplate="%{x}<br>Revenue: $%{y:~s}<br>Transactions: %{customdata[0]:~s}<br>Units sold: %{customdata[1]:~s}<extra></extra>",
    )
    style_plotly(fig, x_title="Month", y_title="Revenue ($)", height=360, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())
else:
    st.info("The current filter contains one month. Use the trend and hourly views above for more detail.")

slow_hour = hour_summary.loc[hour_summary["Transactions"].idxmin()]
insight_box(
    [
        f"The busiest hour is <strong>{int(peak_hour['Hour'])}:00</strong> with <strong>{compact_number(peak_hour['Transactions'])}</strong> transactions.",
        f"Revenue peaks at <strong>{int(peak_revenue_hour['Hour'])}:00</strong> with <strong>{compact_currency(peak_revenue_hour['Revenue'])}</strong>.",
        f"<strong>{peak_day['Weekday Name']}</strong> is the strongest weekday by revenue at <strong>{compact_currency(peak_day['Revenue'])}</strong>.",
        f"The lowest-traffic hour is <strong>{int(slow_hour['Hour'])}:00</strong>, which is the clearest period to examine for demand-building opportunities.",
    ]
)

with st.expander("View hourly and weekday data"):
    tab1, tab2 = st.tabs(["Hourly", "Weekday"])
    with tab1:
        st.dataframe(compact_table(hour_summary, currency_columns=["Revenue"], number_columns=["Transactions", "Units"]), use_container_width=True, hide_index=True)
    with tab2:
        weekday_display = weekday_summary.copy()
        weekday_display["Weekday Name"] = weekday_display["Weekday Name"].astype(str)
        st.dataframe(compact_table(weekday_display, currency_columns=["Revenue"], number_columns=["Transactions", "Units"]), use_container_width=True, hide_index=True)
