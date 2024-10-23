import pandas as pd
import streamlit as st
from auth import check_password


if not check_password():
    st.stop()

df = pd.read_pickle("fetch_base_data.pkl")
st.dataframe(df)