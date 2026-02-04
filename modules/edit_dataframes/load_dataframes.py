import streamlit as st
import pandas as pd

def load_notes(data_path):
    return pd.read_csv(data_path, sep=";", header=0)

def save_notes(data_path, df: pd.DataFrame):
    df.to_csv(data_path, sep=";", index=False)