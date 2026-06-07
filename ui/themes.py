"""
ui/themes.py - Crypto dark theme (v3 Phase B)

Simple, non-intrusive theming using Streamlit's markdown + CSS.
Can be toggled via ENABLE_UI_THEMES flag.
"""

import streamlit as st


def apply_crypto_theme():
    """Apply a clean crypto-inspired dark theme (green accents, dark bg)."""
    st.markdown(
        """
        <style>
        /* Main background and text */
        .stApp {
            background-color: #0d1117;
            color: #c9d1d9;
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: #161b22;
        }
        
        /* Headers */
        h1, h2, h3 {
            color: #58a6ff;
        }
        
        /* Metrics */
        .stMetric {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 8px;
        }
        
        /* Dataframes / tables */
        .stDataFrame {
            background-color: #161b22;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #238636;
            color: white;
            border: 1px solid #2ea043;
        }
        .stButton > button:hover {
            background-color: #2ea043;
            border-color: #3fb950;
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            background-color: #161b22;
            color: #58a6ff;
        }
        
        /* Success / warning / info */
        .stAlert {
            background-color: #161b22;
            border-left-color: #238636;
        }
        
        /* Pro tip / captions */
        .stCaption {
            color: #8b949e;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
