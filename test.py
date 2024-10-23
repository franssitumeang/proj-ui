import pandas as pd
import streamlit as st


df = pd.read_pickle("fetch_base_data.pkl")
st.dataframe(df)