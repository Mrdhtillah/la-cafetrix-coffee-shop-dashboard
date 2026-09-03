import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import streamlit as st

from sidebar import show_sidebar
from utils.filters import sidebar_filters
from utils.load_data import get_data
from utils.ui import COFFEE_COLORS, chart_config, empty_state, format_metric_value, insight_box, metric_label, style_plotly, compact_currency, compact_number, compact_table


st.set_page_config(page_title="Product Insights", layout="wide", page_icon="☕")
show_sidebar()

st.title("Product Insights")
st.caption("Which products and categories drive revenue, volume, and transactions?")

df = get_data()
filtered = sidebar_filters(df, page_key="product", include_product=True)

if filtered.empty:
    empty_state()
    st.stop()

product_summary = (
    filtered.groupby("product_name_clean", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        **{
            "Units Sold": ("transaction_qty", "sum"),
            "Transactions": ("transaction_id", "nunique"),
        },
    )
)
category_summary = (
    filtered.groupby("product_category", as_index=False)
    .agg(
        Revenue=("Revenue", "sum"),
        **{
            "Units Sold": ("transaction_qty", "sum"),
            "Transactions": ("transaction_id", "nunique"),
        },
    )
)

top_revenue_product = product_summary.sort_values("Revenue", ascending=False).iloc[0]
top_units_product = product_summary.sort_values("Units Sold", ascending=False).iloc[0]
top_category = category_summary.sort_values("Revenue", ascending=False).iloc[0]

st.subheader("Product Overview")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Product Categories", compact_number(filtered['product_category'].nunique()))
k2.metric("Unique Products", compact_number(filtered['product_name_clean'].nunique()))
k3.metric("Top Revenue Product", top_revenue_product["product_name_clean"], help=f"{compact_currency(top_revenue_product['Revenue'])} revenue")
k4.metric("Top Volume Product", top_units_product["product_name_clean"], help=f"{compact_number(top_units_product['Units Sold'])} units sold")

st.divider()
st.subheader("Which products perform best?")
control1, control2 = st.columns([2, 1])
with control1:
    metric = st.radio(
        "Compare products by",
        ["Revenue", "Units Sold", "Transactions"],
        horizontal=True,
        key="product_metric",
    )
with control2:
    top_choice = st.selectbox("Products shown", ["Top 5", "Top 10", "All"], index=1)

sorted_products = product_summary.sort_values(metric, ascending=False)
if top_choice == "Top 5":
    product_plot = sorted_products.head(5)
elif top_choice == "Top 10":
    product_plot = sorted_products.head(10)
else:
    product_plot = sorted_products
product_plot = product_plot.sort_values(metric, ascending=True)

fig = px.bar(
    product_plot,
    x=metric,
    y="product_name_clean",
    orientation="h",
    color_discrete_sequence=[COFFEE_COLORS[1]],
)
fig.update_traces(
    customdata=product_plot[["Revenue", "Units Sold", "Transactions"]],
    hovertemplate=(
        "%{y}<br>Revenue: $%{customdata[0]:~s}<br>Units sold: %{customdata[1]:~s}<br>Transactions: %{customdata[2]:~s}<extra></extra>"
    ),
)
height = max(390, min(900, 42 * len(product_plot) + 100))
style_plotly(fig, x_title=metric_label(metric), y_title=None, height=height, showlegend=False)
st.plotly_chart(fig, use_container_width=True, config=chart_config())

st.divider()
st.subheader("Which categories are strongest?")
st.caption("The category comparison uses the same performance metric selected above.")
category_plot = category_summary.sort_values(metric, ascending=True)
fig = px.bar(
    category_plot,
    x=metric,
    y="product_category",
    orientation="h",
    color_discrete_sequence=[COFFEE_COLORS[2]],
)
fig.update_traces(
    customdata=category_plot[["Revenue", "Units Sold", "Transactions"]],
    hovertemplate=(
        "%{y}<br>Revenue: $%{customdata[0]:~s}<br>Units sold: %{customdata[1]:~s}<br>Transactions: %{customdata[2]:~s}<extra></extra>"
    ),
)
style_plotly(fig, x_title=metric_label(metric), y_title=None, height=430, showlegend=False)
st.plotly_chart(fig, use_container_width=True, config=chart_config())

st.divider()
st.subheader("Portfolio concentration and lower performers")
left, right = st.columns([1.35, 1])

with left:
    st.markdown("#### Revenue Pareto analysis")
    st.caption("Shows how quickly product revenue accumulates from highest to lowest performers.")
    pareto = product_summary.sort_values("Revenue", ascending=False).reset_index(drop=True).copy()
    pareto["Cumulative %"] = pareto["Revenue"].cumsum() / pareto["Revenue"].sum() * 100
    pareto["Rank"] = pareto.index + 1

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=pareto["Rank"],
            y=pareto["Revenue"],
            name="Revenue",
            marker_color=COFFEE_COLORS[2],
            customdata=pareto[["product_name_clean"]],
            hovertemplate="#%{x} %{customdata[0]}<br>Revenue: $%{y:~s}<extra></extra>",
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=pareto["Rank"],
            y=pareto["Cumulative %"],
            name="Cumulative share",
            mode="lines+markers",
            line=dict(color=COFFEE_COLORS[0], width=3),
            marker=dict(size=5),
            hovertemplate="Rank %{x}<br>Cumulative revenue: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )
    fig.add_hline(y=80, line_dash="dash", line_color="#8D8178", secondary_y=True)
    style_plotly(fig, x_title="Product rank", y_title="Revenue ($)", height=430)
    fig.update_yaxes(title_text="Cumulative revenue (%)", range=[0, 105], secondary_y=True, gridcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

with right:
    st.markdown(f"#### Lowest products by {metric.lower()}")
    st.caption("Kept as a diagnostic view rather than mixing lower performers into the main ranking.")
    bottom = product_summary.sort_values(metric, ascending=True).head(5)
    fig = px.bar(
        bottom.sort_values(metric, ascending=False),
        x=metric,
        y="product_name_clean",
        orientation="h",
        color_discrete_sequence=[COFFEE_COLORS[5]],
    )
    fig.update_traces(
        customdata=bottom.sort_values(metric, ascending=False)[["Revenue", "Units Sold", "Transactions"]],
        hovertemplate=(
            "%{y}<br>Revenue: $%{customdata[0]:~s}<br>Units sold: %{customdata[1]:~s}<br>Transactions: %{customdata[2]:~s}<extra></extra>"
        ),
    )
    style_plotly(fig, x_title=metric_label(metric), y_title=None, height=430, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config=chart_config())

category_share = top_category["Revenue"] / filtered["Revenue"].sum() * 100
products_to_80 = int((pareto["Cumulative %"] < 80).sum() + 1)
insight_box(
    [
        f"<strong>{top_revenue_product['product_name_clean']}</strong> leads product revenue at <strong>{compact_currency(top_revenue_product['Revenue'])}</strong>.",
        f"<strong>{top_units_product['product_name_clean']}</strong> sells the most units at <strong>{compact_number(top_units_product['Units Sold'])}</strong>.",
        f"<strong>{top_category['product_category']}</strong> is the largest revenue category and contributes <strong>{category_share:.1f}%</strong> of filtered revenue.",
        f"The top <strong>{products_to_80}</strong> products are needed to reach roughly 80% of product revenue in the current filter state.",
    ]
)

with st.expander("View product data"):
    table = product_summary.sort_values("Revenue", ascending=False).rename(columns={"product_name_clean": "Product"})
    table_display = compact_table(table, currency_columns=["Revenue"], number_columns=["Units Sold", "Transactions"])
    st.dataframe(table_display, use_container_width=True, hide_index=True)
    st.download_button(
        "Download product breakdown",
        table.to_csv(index=False).encode("utf-8"),
        file_name="coffee_shop_product_breakdown.csv",
        mime="text/csv",
    )
