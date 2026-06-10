import streamlit as st
import pandas as pd

def show_forecast():
    st.subheader("Predictive Forecast Layer")
    data = pd.DataFrame({
        "Month": ["June", "July", "August"],
        "Adoption %": [72, 78, 82]
    })
    st.line_chart(data.set_index("Month"))
    st.caption("Recruiter adoption trajectory over 90 days")
