#!/bin/bash

# Activate virtual environment and start Streamlit
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run Home.py
