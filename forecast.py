import streamlit as st
import pandas as pd
import altair as alt

def show_forecast():
    st.header("Recruiter Adoption Forecast")

    # --- Sample Data ---
    data = pd.DataFrame({
        "Month": ["June", "July", "August", "September"],
        "Adoption %": [65, 72, 80, 88]
    })

    # --- Chart Styling ---
    chart = (
        alt.Chart(data)
        .mark_line(point=True, strokeWidth=3, color="#2E86C1")
        .encode(
            x=alt.X("Month", title="Month"),
            y=alt.Y("Adoption %", title="Recruiter Adoption (%)"),
            tooltip=["Month", "Adoption %"]
        )
        .properties(width=600, height=400)
    )

    # --- Render Chart ---
    st.altair_chart(chart, use_container_width=True)

    # --- Narrative Context ---
    st.caption(
        "Recruiter adoption is projected to accelerate from 65% in June to 88% by September, "
        "indicating strong momentum and institutionalization across the enterprise."
    )
