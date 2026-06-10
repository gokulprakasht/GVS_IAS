import streamlit as st

def show_infographic():
    st.subheader("Infographic Storyboard")
    stages = {
        "ROI": "Efficiency gains, cost savings, faster time-to-hire",
        "Adoption": "Recruiter cadence adoption globally at 72%",
        "Institutionalization": "Cadence embedded in processes, advisory council established"
    }
    for stage, desc in stages.items():
        st.markdown(f"**{stage}** → {desc}")
