from pathlib import Path

import plotly.graph_objects as go
import streamlit as st


def compact_number(value, decimals=1):
    """Format displayed values compactly while leaving source data unchanged."""
    if value is None:
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    sign = "-" if number < 0 else ""
    number = abs(number)
    for threshold, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "k")):
        if number >= threshold:
            scaled = number / threshold
            precision = 0 if scaled >= 100 or scaled.is_integer() else decimals
            text = f"{scaled:.{precision}f}".rstrip("0").rstrip(".")
            return f"{sign}{text}{suffix}"

    if number.is_integer():
        return f"{sign}{number:,.0f}"
    return f"{sign}{number:,.2f}"


def compact_currency(value, decimals=1):
    return f"${compact_number(value, decimals=decimals)}"


def compact_table(df, currency_columns=(), number_columns=()):
    """Return a display-only copy with compact number strings; downloads can use the original dataframe."""
    display = df.copy()
    for column in currency_columns:
        if column in display.columns:
            display[column] = display[column].map(compact_currency)
    for column in number_columns:
        if column in display.columns:
            display[column] = display[column].map(compact_number)
    return display


COFFEE_COLORS = [
    "#4A3326",
    "#6F4E37",
    "#A67C52",
    "#B08968",
    "#C69C72",
    "#DDB892",
    "#E6CCB2",
    "#7F5539",
    "#D9C8B6",
]

TEXT = "#3A2B24"
MUTED = "#77665B"
GRID = "#E7DDD3"
CREAM = "#F8F5F2"
CARD = "#FFFDFC"


def apply_global_styles():
    css_path = Path(__file__).resolve().parents[1] / "assets" / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def style_plotly(fig, x_title=None, y_title=None, height=380, showlegend=None):
    fig.update_layout(
        height=height,
        font=dict(family="Poppins, Arial, sans-serif", color=TEXT, size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=18, r=18, t=28, b=18),
        hoverlabel=dict(bgcolor="white", font_size=13, font_family="Poppins, Arial"),
        xaxis_title=x_title,
        yaxis_title=y_title,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            title_text="",
        ),
    )
    if showlegend is not None:
        fig.update_layout(showlegend=showlegend)

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=GRID,
        tickfont=dict(color=MUTED),
        title_font=dict(color=TEXT),
    )
    fig.update_yaxes(
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        linecolor=GRID,
        tickfont=dict(color=MUTED),
        title_font=dict(color=TEXT),
    )

    # Compact aggregate chart axes (1K, 1.2K, 1M) without changing data.
    for axis_name, title in (("x", x_title), ("y", y_title)):
        if not title:
            continue
        normalized = title.lower()
        is_aggregate = any(token in normalized for token in ("revenue", "transactions", "units sold", "product rank"))
        is_percentage = "%" in title or "percentage" in normalized or "share" in normalized
        if is_aggregate and not is_percentage:
            axis = fig.update_xaxes if axis_name == "x" else fig.update_yaxes
            kwargs = {"tickformat": "~s"}
            if "revenue" in normalized and "($)" in title:
                kwargs["tickprefix"] = "$"
            axis(**kwargs)
    return fig


def chart_config():
    return {
        "displaylogo": False,
        "responsive": True,
        "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    }


def empty_state(message="No data found. Try adjusting your filters."):
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-icon">☕</div>
            <strong>No data found</strong>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_box(items, title="Key Insight"):
    list_items = "".join(f"<li>{item}</li>" for item in items)
    st.markdown(
        f"""
        <div class="insight-box">
            <div class="insight-title">💡 {title}</div>
            <ul>{list_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_label(metric):
    return {
        "Revenue": "Revenue ($)",
        "Units Sold": "Units sold",
        "Transactions": "Transactions",
    }.get(metric, metric)


def format_metric_value(metric, value):
    if metric == "Revenue":
        return compact_currency(value)
    return compact_number(value)
