import streamlit as st
from utils.ui import apply_global_styles


def show_sidebar():
    apply_global_styles()

    with st.sidebar:
        st.markdown(
            """
            <div class="logo-small">La ☕</div>
            <div class="logo-big">Cafètrix</div>
            <div class="subtitle">Coffee Shop Dashboard</div>
            """,
            unsafe_allow_html=True,
        )
        st.divider()
        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()
        st.markdown(
            "<div class='footer'>Jan – Jun 2023</div>",
            unsafe_allow_html=True,
        )
