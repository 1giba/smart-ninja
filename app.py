import streamlit as st
import os
import pathlib
from app.ui.components import create_logo, display_sidebar
from app.ui.pages.home import render_home
from app.ui.pages.comparisons import render_comparisons
from app.ui.pages.history import render_history
from app.ui.pages.alerts import render_alerts
from app.ui.pages.settings import render_settings
from app.ui.async_bridge import AsyncBridge

# Ensure assets directory exists
if not os.path.exists("assets"):
    os.makedirs("assets")

# Configure favicon path
favicon_path = "assets/favicon.ico"

# Configure page settings
st.set_page_config(
    page_title="SmartNinja",
    page_icon=favicon_path if os.path.exists(favicon_path) else "📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for theme and hide development/deployment options
st.markdown("""
<style>
    /* Theme styling */
    .main {
        background-color: #1B2A41;
        color: #FFFFFF;
    }
    .stApp {
        background-color: #1B2A41;
    }
    .stButton button {
        background-color: #50FA7B;
        color: #1B2A41;
        font-weight: bold;
    }
    .stTextInput > div > div > input {
        background-color: #2E2E2E;
        color: #FFFFFF;
    }
    .stSelectbox > div > div > select {
        background-color: #2E2E2E;
        color: #FFFFFF;
    }
    .stNumberInput > div > div > input {
        background-color: #2E2E2E;
        color: #FFFFFF;
    }
    .stHeader {
        color: #50FA7B;
    }

    /* Hide development options in header */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none;}
    .stDeployButton {display:none;}
</style>
""", unsafe_allow_html=True)

# Display logo and title in header
col1, col2 = st.columns([1, 6])

with col1:
    logo_path = create_logo(width=80)
    if os.path.exists(logo_path):
        st.image(logo_path, width=80)

with col2:
    st.title("Smartphone Price Tracker Agent")

# Add a separator below the header
st.markdown("<hr style='margin-top: 0; margin-bottom: 20px; border-color: #2E2E2E;'>", unsafe_allow_html=True)

# Sidebar navigation
selected, selected_regions, selected_brands = display_sidebar()

# Main content based on selection
if selected == "🏠 Home":
    render_home(selected_regions, selected_brands)
elif selected == "📊 Comparisons":
    # Use AsyncBridge to call the async render_comparisons function
    AsyncBridge.run_async(render_comparisons(selected_regions, selected_brands))
elif selected == "📜 History":
    # Use AsyncBridge to call the async render_history function
    AsyncBridge.run_async(render_history(selected_regions, selected_brands))
elif selected == "🔔 Alerts":
    render_alerts(selected_regions, selected_brands)
elif selected == "⚙️ Settings":
    render_settings()

# Footer
st.markdown("---")
footer = """
<div style='text-align: center; margin-top: 20px;'>
    <p>Built with 🤖 and 📊 by
        <a href="https://github.com/1giba/smart-ninja">@1giba</a>
    </p>
    <p>© 2025 Code Happy Tecnologia Ltda. All rights reserved.</p>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
