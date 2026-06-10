import streamlit as st

def show_kpi_layer():
    st.header("Executive KPI Layer")

    # --- Strategic KPI Layer ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Recruiter Adoption", "72%", "▲ +5% vs last month")
    with col2:
        st.metric("ROI Outcomes", "18% faster", "▼ -2d time-to-hire")
    with col3:
        st.metric("Candidate NPS", "8.2", "▲ +0.6 vs last month")
    with col4:
        st.metric("Leadership Validation", "Strong", "✔ Healthy")

    # --- Narrative Context ---
    st.caption("Recruiter adoption accelerating globally, ROI validated, candidate experience improving, and leadership confidence strong.")
