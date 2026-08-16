import streamlit as st
import time

def show_card_skeleton():
    st.markdown("""
    <style>
    @keyframes shimmer {
        0% {background-position:-400px 0;}
        100% {background-position:400px 0;}
    }

    .skeleton-card{
        height:120px;
        border-radius:14px;
        margin:10px 0;
        background:linear-gradient(
            90deg,
            #e5e7eb 25%,
            #f3f4f6 50%,
            #e5e7eb 75%
        );
        background-size:800px 100%;
        animation:shimmer 1.5s infinite;
    }
    </style>

    <div class="skeleton-card"></div>
    """, unsafe_allow_html=True)

def show_chart_skeleton():
    st.markdown("""
    <div class="skeleton-card" style="height:320px;"></div>
    """, unsafe_allow_html=True)