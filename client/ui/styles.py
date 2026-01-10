import streamlit as st

def inject_css():
    st.markdown("""
    <style>
        .block-container { max-width: 1000px; }
        .role-card {
            background: white; padding: 20px; border-radius: 10px; border: 1px solid #ddd;
            text-align: center; height: 200px; display: flex; flex-direction: column;
            justify-content: center; align-items: center; cursor: pointer;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .role-card:hover { border-color: #4CAF50; transform: translateY(-3px); }
        .status-graded { color: #2e7d32; font-weight: bold; }
        .status-pending { color: #f57c00; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)
