"""
JalSaarthi (जलसारथी) - Modern Climate-Resilient Agricultural Decision Support
Matcha Green Theme & Clean Multi-Screen UI
Trilingual Support: English, Marathi, Hindi
"""

import sys
import os
import base64
import importlib
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path for clean engine imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import engine.crop_database
    import engine.water_engine
    import engine.climate_risk
    import engine.optimizer
    import engine.translations
    
    importlib.reload(engine.crop_database)
    importlib.reload(engine.water_engine)
    importlib.reload(engine.climate_risk)
    importlib.reload(engine.optimizer)
    importlib.reload(engine.translations)
    
    from engine.crop_database import (
        CROPS, SOIL_PROFILES, IRRIGATION_COSTS, MANDI_DF, get_mandi_price,
        PUMP_SPECS, DISTRICT_REGIONAL_BASELINES, calculate_irrigation_volume
    )
    from engine.water_engine import simulate_crop_water_balance
    from engine.climate_risk import analyze_climate_risk
    from engine.optimizer import optimize_farming_strategy, evaluate_annual_rotation, get_historical_weather
    from engine.translations import get_text, TRANSLATIONS
except ImportError as e:
    st.error(f"Error loading JalSaarthi engine: {e}")

# Page Configuration
st.set_page_config(
    page_title="JalSaarthi - Smart Climate-Resilient Agriculture",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------------------------------------------
# Session State Initialization & Automatic Pop-up Trigger
# -------------------------------------------------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state["lang"] = "en"

if "nav_view" not in st.session_state:
    st.session_state["nav_view"] = "home"

# Helper for seamless view navigation across buttons and sidebar radio
def navigate_to(target_view):
    st.session_state["nav_view"] = target_view

# Safe on_click callbacks to update scenario shock states before widget redraws
def reset_scenario_shocks():
    st.session_state["whatif_rain"] = 0
    st.session_state["whatif_water"] = 0
    st.session_state["whatif_temp"] = 0.0
    st.session_state["whatif_budget"] = 0
    st.session_state["slider_rain"] = 0
    st.session_state["slider_water"] = 0
    st.session_state["slider_temp"] = 0.0
    st.session_state["slider_budget"] = 0

def apply_preset_shock(rain=0, water=0, temp=0.0, budget=0, target_view=None):
    st.session_state["whatif_rain"] = rain
    st.session_state["whatif_water"] = water
    st.session_state["whatif_temp"] = temp
    st.session_state["whatif_budget"] = budget
    st.session_state["slider_rain"] = rain
    st.session_state["slider_water"] = water
    st.session_state["slider_temp"] = temp
    st.session_state["slider_budget"] = budget
    if target_view:
        st.session_state["nav_view"] = target_view

# Automatically trigger pop-up guide as soon as user opens app
if "has_seen_guide" not in st.session_state:
    st.session_state["has_seen_guide"] = False
    st.session_state["auto_popup_pending"] = True

if "current_district" not in st.session_state:
    st.session_state["current_district"] = "solapur"
    p_init = DISTRICT_REGIONAL_BASELINES["solapur"]
    st.session_state["farm_size"] = float(p_init["farm_size_acres"])
    st.session_state["budget"] = int(p_init["budget_rs"])
    st.session_state["soil_select"] = p_init["soil_type"]
    st.session_state["irr_method_select"] = p_init["irrigation_method"]
    st.session_state["pump_hp_select"] = float(p_init["pump_hp"])
    st.session_state["pump_hours_slider"] = float(p_init["daily_pumping_hours"])
    st.session_state["pump_days_slider"] = int(p_init["pumping_days_season"])
    st.session_state["direct_water_slider"] = int(p_init["default_water_m3"])
    st.session_state["water_mode"] = "direct"

# Stress Simulator State
if "whatif_rain" not in st.session_state:
    st.session_state["whatif_rain"] = 0
if "whatif_water" not in st.session_state:
    st.session_state["whatif_water"] = 0
if "whatif_temp" not in st.session_state:
    st.session_state["whatif_temp"] = 0.0
if "whatif_budget" not in st.session_state:
    st.session_state["whatif_budget"] = 0

lang = st.session_state["lang"]

def on_district_change():
    new_d = st.session_state["district_select"]
    st.session_state["current_district"] = new_d
    p_base = DISTRICT_REGIONAL_BASELINES.get(new_d, DISTRICT_REGIONAL_BASELINES["solapur"])
    st.session_state["farm_size"] = float(p_base["farm_size_acres"])
    st.session_state["budget"] = int(p_base["budget_rs"])
    st.session_state["soil_select"] = p_base["soil_type"]
    st.session_state["irr_method_select"] = p_base["irrigation_method"]
    st.session_state["pump_hp_select"] = float(p_base["pump_hp"])
    st.session_state["pump_hours_slider"] = float(p_base["daily_pumping_hours"])
    st.session_state["pump_days_slider"] = int(p_base["pumping_days_season"])
    st.session_state["direct_water_slider"] = int(p_base["default_water_m3"])
    
    # Synchronize UI widget keys if they already exist in session_state
    if "home_budget_slider" in st.session_state:
        st.session_state["home_budget_slider"] = int(p_base["budget_rs"])
    if "home_water_quick_slider" in st.session_state:
        st.session_state["home_water_quick_slider"] = int(p_base["default_water_m3"])
    if "home_soil_select" in st.session_state:
        st.session_state["home_soil_select"] = p_base["soil_type"]
    if "home_land_size_slider" in st.session_state:
        st.session_state["home_land_size_slider"] = float(p_base["farm_size_acres"])
    if "home_irr_select" in st.session_state:
        st.session_state["home_irr_select"] = p_base["irrigation_method"]
    if "home_power_hours_slider" in st.session_state:
        st.session_state["home_power_hours_slider"] = float(p_base["daily_pumping_hours"])

# Helper for translating
def t(key, **kwargs):
    return get_text(key, lang=st.session_state["lang"], **kwargs)

# Helper to load and cache header banner image as base64
@st.cache_data
def get_banner_base64():
    banner_path = os.path.join(os.path.dirname(__file__), "assets", "hero_banner.jpg")
    if os.path.exists(banner_path):
        with open(banner_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    return ""

# -------------------------------------------------------------------------------------------------
# Matcha Green Custom Theme & Styling
# -------------------------------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Creamy Matcha Main Background */
    .stApp {
        background-color: #f4f8f4 !important;
    }
    
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1200px;
    }
    
    /* Sidebar Styling - Deep Earthy Matcha Green */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1c3d23 0%, #254d2e 60%, #2d5a37 100%) !important;
        color: #ffffff !important;
        box-shadow: 2px 0 12px rgba(0,0,0,0.15) !important;
    }
    
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.18) !important;
    }
    
    [data-testid="stSidebar"] .stMarkdown p, 
    [data-testid="stSidebar"] label {
        color: #e5f2e5 !important;
    }

    /* Sidebar Brand Box */
    .sidebar-brand {
        padding: 8px 0 18px 0;
        text-align: left;
    }
    .sidebar-brand-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #ffffff !important;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 8px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .sidebar-brand-tagline {
        font-size: 0.8rem;
        color: #c8e6c9 !important;
        margin-top: 3px;
        font-weight: 500;
    }

    /* Sidebar Navigation Radio Buttons: PURE WHITE VISIBLE TEXT & MATCHA PILLS */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] {
        gap: 10px;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label {
        background-color: rgba(255, 255, 255, 0.12) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 24px !important;
        padding: 10px 18px !important;
        margin-bottom: 6px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
    }

    /* Force all text inside sidebar radio to be bright pure white */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label p,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label span,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label div {
        color: #ffffff !important;
        font-size: 1.0rem !important;
        font-weight: 700 !important;
        opacity: 1 !important;
        text-shadow: 0 1px 3px rgba(0,0,0,0.4) !important;
    }

    /* Hover State */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background-color: #4a7c59 !important;
        border-color: #a3b18a !important;
        transform: translateX(2px);
    }

    /* Active Checked State - Vibrant Matcha */
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"],
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
        background-color: #588157 !important;
        border-color: #c8e6c9 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] p,
    [data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p {
        color: #ffffff !important;
        font-weight: 800 !important;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
        accent-color: #a3b18a !important;
    }

    /* Horizontal Tabs Styled as Modern Green Button Pills */
    [data-testid="stTabs"] {
        gap: 12px;
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        background: transparent !important;
        gap: 10px !important;
        border-bottom: none !important;
        padding: 6px 0 16px 0 !important;
    }

    /* Unselected Tab Button */
    [data-testid="stTabs"] [data-baseweb="tab"] {
        background-color: #e3ede3 !important;
        border: 1.5px solid #a3b18a !important;
        border-radius: 24px !important;
        padding: 8px 22px !important;
        color: #254d2e !important;
        font-weight: 700 !important;
        font-size: 0.94rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03) !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab"]:hover {
        background-color: #d4e6d4 !important;
        border-color: #588157 !important;
        transform: translateY(-1px) !important;
    }

    /* Active Tab Button - Deep Matcha Green with Pure White Text */
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
        background-color: #386641 !important;
        border-color: #254d2e !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 12px rgba(40, 75, 48, 0.28) !important;
    }

    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] p,
    [data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] span {
        color: #ffffff !important;
    }

    /* Hide default tab indicator line */
    [data-testid="stTabs"] [data-baseweb="tab-border"],
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* Matcha Hero Banner with Scenic Farm Landscape */
    .hero-banner {
        position: relative;
        border-radius: 20px;
        padding: 34px 38px;
        margin-bottom: 24px;
        border: 1.5px solid #a3b18a;
        box-shadow: 0 6px 20px rgba(37,77,46,0.08);
        overflow: hidden;
        min-height: 175px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        background-size: cover !important;
        background-position: right center !important;
        background-repeat: no-repeat !important;
    }
    .hero-banner-content {
        position: relative;
        z-index: 2;
        max-width: 620px;
    }
    .hero-title {
        font-size: 2.25rem;
        font-weight: 800;
        color: #123017;
        margin-bottom: 6px;
        line-height: 1.22;
        letter-spacing: -0.5px;
        text-shadow: 0 1px 3px rgba(255, 255, 255, 0.7);
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #274c2e;
        font-weight: 600;
        line-height: 1.48;
        text-shadow: 0 1px 2px rgba(255, 255, 255, 0.7);
    }
    .hero-badge {
        position: absolute;
        top: 20px;
        right: 24px;
        z-index: 2;
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(8px);
        padding: 6px 14px;
        border-radius: 24px;
        border: 1px solid rgba(56, 102, 65, 0.25);
        font-size: 0.82rem;
        font-weight: 700;
        color: #1c3d23;
        display: flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    @media (max-width: 768px) {
        .hero-banner-content {
            max-width: 100% !important;
        }
        .hero-badge {
            display: none !important;
        }
    }

    /* Main Modern White Cards with Matcha Green Accents */
    .modern-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 24px;
        border: 1.5px solid #d4e6d4;
        box-shadow: 0 4px 16px rgba(40,75,48,0.04);
        margin-bottom: 20px;
    }

    /* Pastel Insight Cards */
    .pastel-card {
        border-radius: 14px;
        padding: 16px 18px;
        text-align: center;
        border: 1.5px solid transparent;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .pastel-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.06);
    }
    .pastel-card-green {
        background-color: #e8f4e8;
        border-color: #b8d8b8;
        color: #1f3d24;
    }
    .pastel-card-blue {
        background-color: #e3f0f7;
        border-color: #b5d6e8;
        color: #1b5275;
    }
    .pastel-card-amber {
        background-color: #fbf1e4;
        border-color: #ebd0ad;
        color: #8c4a00;
    }
    .pastel-card-purple {
        background-color: #f4edf7;
        border-color: #dac7e3;
        color: #5c246f;
    }
    .pastel-card-label {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
        margin-bottom: 4px;
    }
    .pastel-card-val {
        font-size: 1.38rem;
        font-weight: 800;
        margin: 4px 0;
    }
    .pastel-card-sub {
        font-size: 0.78rem;
        opacity: 0.9;
    }

    /* Scenario Shock Cards */
    .scenario-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 20px 18px;
        border: 1.5px solid #d4e6d4;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        height: 100%;
        transition: all 0.2s ease;
    }
    .scenario-card:hover {
        border-color: #386641;
        box-shadow: 0 4px 12px rgba(40,75,48,0.1);
    }
    .scenario-card-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1c3d23;
        margin-bottom: 4px;
    }
    .scenario-card-sub {
        font-size: 0.84rem;
        color: #555;
        margin-bottom: 12px;
    }
    .scenario-card-crop {
        font-size: 1.25rem;
        font-weight: 800;
        color: #254d2e;
        background: #e3ede3;
        border-radius: 8px;
        padding: 6px 14px;
        display: inline-block;
        margin-bottom: 14px;
    }

    /* Matcha Primary Action Buttons */
    .stButton > button {
        background-color: #386641 !important;
        color: #ffffff !important;
        border-radius: 22px !important;
        font-weight: 700 !important;
        padding: 9px 26px !important;
        border: none !important;
        box-shadow: 0 3px 8px rgba(40,75,48,0.25) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #4a7c59 !important;
        box-shadow: 0 5px 14px rgba(40,75,48,0.35) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Secondary Back Buttons */
    .back-btn > button {
        background-color: #e3ede3 !important;
        color: #254d2e !important;
        border: 1px solid #a3b18a !important;
        box-shadow: none !important;
    }

    /* Checklist Points */
    .check-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        margin-bottom: 12px;
        font-size: 0.96rem;
        color: #222;
        line-height: 1.4;
    }
    .check-icon {
        color: #386641;
        font-weight: 800;
        font-size: 1.15rem;
        flex-shrink: 0;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------------------------------------
# Interactive Pop-up Guide Definition (@st.dialog)
# -------------------------------------------------------------------------------------------------
@st.dialog(t("popup_title"))
def show_popup_guide():
    st.markdown(f"""
    <p style="font-size: 1.0rem; color: #2d5a37; font-weight: 600; line-height: 1.45; margin-bottom: 14px;">
        {t("popup_welcome")}
    </p>
    
    <div style="background: #eef5ee; border-left: 4px solid #386641; padding: 12px 14px; border-radius: 6px; margin-bottom: 10px; color: #1c3d23;">
        {t("popup_step_1")}
    </div>
    
    <div style="background: #eef5ee; border-left: 4px solid #386641; padding: 12px 14px; border-radius: 6px; margin-bottom: 10px; color: #1c3d23;">
        {t("popup_step_2")}
    </div>
    
    <div style="background: #eef5ee; border-left: 4px solid #386641; padding: 12px 14px; border-radius: 6px; margin-bottom: 10px; color: #1c3d23;">
        {t("popup_step_3")}
    </div>
    
    <div style="background: #eef5ee; border-left: 4px solid #386641; padding: 12px 14px; border-radius: 6px; margin-bottom: 18px; color: #1c3d23;">
        {t("popup_step_4")}
    </div>
    """, unsafe_allow_html=True)
    
    if st.button(t("popup_close_btn"), use_container_width=True, key="popup_dismiss_btn"):
        st.session_state["has_seen_guide"] = True
        st.session_state["auto_popup_pending"] = False
        st.rerun()

# Automatically show dialog on first open
if st.session_state.get("auto_popup_pending", False):
    show_popup_guide()

# -------------------------------------------------------------------------------------------------
# Sidebar Navigation & Settings
# -------------------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-brand">
        <div class="sidebar-brand-title">🌾 {t("brand_name")}</div>
        <div class="sidebar-brand-tagline">{t("tagline")}</div>
    </div>
    """, unsafe_allow_html=True)

    # Language Switcher
    lang_labels = {"en": "English", "mr": "मराठी (Marathi)", "hi": "हिंदी (Hindi)"}
    curr_lang_idx = ["en", "mr", "hi"].index(st.session_state["lang"])
    selected_lang = st.selectbox(
        t("language_select"),
        options=["en", "mr", "hi"],
        format_func=lambda x: lang_labels[x],
        index=curr_lang_idx,
        key="lang_selector"
    )
    if selected_lang != st.session_state["lang"]:
        st.session_state["lang"] = selected_lang
        st.rerun()

    st.markdown("<hr style='margin: 12px 0 16px 0;'>", unsafe_allow_html=True)

    # Navigation Options (Styled with Crisp Pure White Text)
    nav_keys = ["home", "reports", "scenario", "info"]
    nav_labels = {
        "home": f"🏠  {t('nav_home')}",
        "reports": f"📊  {t('nav_reports')}",
        "scenario": f"🔄  {t('nav_scenario')}",
        "info": f"ℹ️  {t('nav_info')}"
    }
    
    curr_nav = st.session_state.get("nav_view", "home")
    curr_nav_idx = nav_keys.index(curr_nav) if curr_nav in nav_keys else 0

    selected_nav = st.radio(
        "Navigation",
        options=nav_keys,
        format_func=lambda k: nav_labels[k],
        index=curr_nav_idx,
        label_visibility="collapsed"
    )
    if selected_nav != st.session_state["nav_view"]:
        st.session_state["nav_view"] = selected_nav
        st.rerun()

    st.markdown("<hr style='margin: 16px 0;'>", unsafe_allow_html=True)

    # Pop-up Guide Re-open Button
    if st.button(t("guide_button"), use_container_width=True, key="sidebar_guide_btn"):
        show_popup_guide()

    # Sidebar Bottom Mascot & Tagline (Matching Mockup)
    st.markdown(f"""
    <div style="margin-top: 32px; padding: 14px 12px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 14px; text-align: center;">
        <div style="font-size: 1.45rem; margin-bottom: 4px;">🚜 🌾</div>
        <div style="color: #ffffff; font-weight: 700; font-size: 0.84rem; letter-spacing: -0.2px;">🌱 {t('tagline')}</div>
        <div style="color: #c8e6c9; font-size: 0.72rem; margin-top: 4px; opacity: 0.85;">NASA POWER • IMD • FAO-56 • APMC</div>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------------------------------------------
# Core Engine Execution (Feeds All Views Live)
# -------------------------------------------------------------------------------------------------
farm_size_acres = float(st.session_state.get("farm_size", 2.5))
available_budget_rs = float(st.session_state.get("budget", 50000))
location_option = st.session_state.get("current_district", "solapur")
soil_type = st.session_state.get("soil_select", "Medium Black (Vertisol)")
irrigation_method = st.session_state.get("irr_method_select", "flood_furrow")

# Calculate available water based on mode
if st.session_state.get("water_mode", "direct") == "pump":
    p_calc = calculate_irrigation_volume(
        pump_hp=float(st.session_state.get("pump_hp_select", 5.0)),
        daily_hours=float(st.session_state.get("pump_hours_slider", 5.0)),
        pumping_days=int(st.session_state.get("pump_days_slider", 32))
    )
    available_water_m3 = p_calc["total_water_m3"]
else:
    available_water_m3 = float(st.session_state.get("direct_water_slider", 4000))

# Execute Master Optimization Pipeline
results = optimize_farming_strategy(
    farm_size_acres=farm_size_acres,
    available_budget_rs=available_budget_rs,
    available_water_m3=available_water_m3,
    location=location_option,
    soil_type=soil_type,
    irrigation_method=irrigation_method,
    rainfall_shift_pct=float(st.session_state["whatif_rain"]),
    temp_shift_c=float(st.session_state["whatif_temp"]),
    water_shift_pct=float(st.session_state["whatif_water"]),
    budget_shift_rs=float(st.session_state["whatif_budget"])
)

top = results["top_recommendation"]
all_ranked = results["all_ranked_options"]
ctx = results["context"]
why_won_text = results["why_this_crop_won"]
is_crisis = results.get("crisis_mode", False) or (not top.get("is_viable", True))
emit = results.get("emergency_mitigation", {})

top_crop = top["crop"]
top_fin = top["financial_metrics"]
top_wat = top["water_metrics"]
top_clim = top["climate_metrics"]
top_yld = top["yield_metrics"]

# Localized Crop Name
def get_crop_name(cname):
    c_info = CROPS.get(cname, {})
    if lang == "mr":
        return c_info.get("name_mr", cname).split(" ")[0]
    elif lang == "hi":
        return c_info.get("name_hi", cname).split(" ")[0]
    return cname

# =================================================================================================
# VIEW 1: 🏠 HOME (Landing & Crop Planner)
# =================================================================================================
if st.session_state["nav_view"] == "home":
    # 1. Hero Welcome Banner with Scenic Agricultural Field Image
    hero_b64 = get_banner_base64()
    if hero_b64:
        banner_style = f"background: linear-gradient(90deg, rgba(244, 248, 244, 0.96) 0%, rgba(244, 248, 244, 0.90) 42%, rgba(244, 248, 244, 0.42) 75%, rgba(244, 248, 244, 0.12) 100%), url('data:image/jpeg;base64,{hero_b64}');"
    else:
        banner_style = "background: linear-gradient(135deg, #e3ede3 0%, #d4e6d4 50%, #c1dcc1 100%);"

    curr_dist_label = t("district_solapur") if location_option == "solapur" else t("district_pune")
    st.markdown(f"""
    <div class="hero-banner" style="{banner_style}">
        <div class="hero-badge">
            <span style="background: #386641; color: white; border-radius: 50%; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 800;">JS</span>
            <span>JalSaarthi AI • {curr_dist_label}</span>
        </div>
        <div class="hero-banner-content">
            <div class="hero-title">{t("welcome_title")}</div>
            <div class="hero-subtitle">{t("welcome_subtitle")}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Plan Your Next Crop Main Card
    with st.container():
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
            <span style="font-size: 1.5rem;">🌱</span>
            <span style="font-size: 1.35rem; font-weight: 700; color: #1c3d23;">{t("plan_title")}</span>
        </div>
        <p style="color: #4a634e; font-size: 0.94rem; margin-bottom: 16px;">{t("plan_subtitle")}</p>
        """, unsafe_allow_html=True)
        
        # 3 Key Clean Inputs in One Row
        col_in1, col_in2, col_in3 = st.columns([1.2, 1.4, 1.2])
        
        with col_in1:
            st.selectbox(
                t("location_label"),
                options=["solapur", "pune"],
                format_func=lambda x: "Solapur (Drought Belt)" if x == "solapur" else "Pune (Transition Zone)",
                index=0 if location_option == "solapur" else 1,
                key="district_select",
                on_change=on_district_change
            )
        
        with col_in2:
            if "home_water_quick_slider" not in st.session_state:
                st.session_state["home_water_quick_slider"] = int(available_water_m3)
            st.slider(
                f"{t('water_label')} (m³)",
                min_value=500,
                max_value=10000,
                step=250,
                key="home_water_quick_slider",
                help="1 m³ = 1,000 Litres (4,000 m³ = 40 Lakh Litres)"
            )
            st.session_state["direct_water_slider"] = st.session_state["home_water_quick_slider"]
            st.session_state["water_mode"] = "direct"
            
        with col_in3:
            if "home_budget_slider" not in st.session_state:
                st.session_state["home_budget_slider"] = int(available_budget_rs)
            st.slider(
                t("budget_label"),
                min_value=10000,
                max_value=150000,
                step=5000,
                key="home_budget_slider",
                format="₹%d"
            )
            st.session_state["budget"] = st.session_state["home_budget_slider"]
        
        # Advanced Optional Settings Expander
        with st.expander(t("adv_settings"), expanded=False):
            col_adv1, col_adv2 = st.columns(2)
            with col_adv1:
                st.session_state["farm_size"] = st.slider(
                    t("land_size_label"),
                    min_value=0.5,
                    max_value=10.0,
                    value=float(st.session_state.get("farm_size", 2.5)),
                    step=0.5,
                    key="home_land_size_slider"
                )
                soil_opts = list(SOIL_PROFILES.keys())
                curr_soil = st.session_state.get("soil_select", "Medium Black (Vertisol)")
                s_idx = soil_opts.index(curr_soil) if curr_soil in soil_opts else 0
                st.session_state["soil_select"] = st.selectbox(
                    t("soil_label"),
                    options=soil_opts,
                    index=s_idx,
                    key="home_soil_select"
                )
            with col_adv2:
                irr_opts = ["flood_furrow", "sprinkler", "drip"]
                curr_irr = st.session_state.get("irr_method_select", "flood_furrow")
                irr_idx = irr_opts.index(curr_irr) if curr_irr in irr_opts else 0
                st.session_state["irr_method_select"] = st.selectbox(
                    t("irrigation_label"),
                    options=irr_opts,
                    index=irr_idx,
                    format_func=lambda x: IRRIGATION_COSTS[x].get("name_mr", x.title()),
                    key="home_irr_select"
                )
                st.session_state["pump_hours_slider"] = st.slider(
                    t("power_hours_label"),
                    min_value=2.0,
                    max_value=12.0,
                    value=float(st.session_state.get("pump_hours_slider", 5.0)),
                    step=0.5,
                    key="home_power_hours_slider"
                )
                
        # Big Call to Action Button
        col_btn_l, col_btn_r = st.columns([3, 1.2])
        with col_btn_r:
            if st.button(t("btn_get_recommendation"), use_container_width=True, key="home_cta_btn"):
                navigate_to("reports")
                st.rerun()

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # 3. Quick Insights Row (4 Pastel Cards)
    st.markdown(f"#### 📊 {t('quick_insights_title')}")
    q1, q2, q3, q4 = st.columns(4)
    
    with q1:
        st.markdown(f"""
        <div class="pastel-card pastel-card-green">
            <div style="font-size: 1.6rem;">🌱</div>
            <div class="pastel-card-label">{t('best_crop_label')}</div>
            <div class="pastel-card-val">{get_crop_name(top_crop)}</div>
            <div class="pastel-card-sub">RRI: {top['resilience_return_index']}/100</div>
        </div>
        """, unsafe_allow_html=True)
        
    with q2:
        water_val_str = "0 m³ (Rainfed)" if top_wat["water_required_m3"] <= 0 else f"{top_wat['water_required_m3']:,.0f} m³"
        st.markdown(f"""
        <div class="pastel-card pastel-card-blue">
            <div style="font-size: 1.6rem;">💧</div>
            <div class="pastel-card-label">{t('water_needed_label')}</div>
            <div class="pastel-card-val">{water_val_str}</div>
            <div class="pastel-card-sub">{top_wat.get('natural_contribution_pct', 70):.0f}% Rain Met</div>
        </div>
        """, unsafe_allow_html=True)
        
    with q3:
        st.markdown(f"""
        <div class="pastel-card pastel-card-amber">
            <div style="font-size: 1.6rem;">☀️</div>
            <div class="pastel-card-label">{t('climate_risk_label')}</div>
            <div class="pastel-card-val">{top_clim['risk_level']}</div>
            <div class="pastel-card-sub">Score: {top_clim['risk_score']}/100</div>
        </div>
        """, unsafe_allow_html=True)
        
    with q4:
        st.markdown(f"""
        <div class="pastel-card pastel-card-purple">
            <div style="font-size: 1.6rem;">📈</div>
            <div class="pastel-card-label">{t('expected_profit_label')}</div>
            <div class="pastel-card-val">₹{top_fin['expected_profit_rs']:,.0f}</div>
            <div class="pastel-card-sub">ROI: {top_fin['roi_pct']}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # 4. Did You Know? Card
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ffffff 0%, #f4fbf4 100%); border-radius: 14px; padding: 18px 24px; border: 1.5px solid #d4e6d4; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div style="display: flex; align-items: center; gap: 14px;">
            <span style="font-size: 2rem;">💡</span>
            <div>
                <b style="color: #1c3d23; font-size: 1.05rem;">{t('did_you_know_title')}</b>
                <p style="color: #4a634e; margin: 2px 0 0 0; font-size: 0.92rem;">{t('did_you_know_text')}</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =================================================================================================
# VIEW 2: 📊 MY REPORTS (Personalized Recommendation & Trade-Offs)
# =================================================================================================
elif st.session_state["nav_view"] == "reports":
    # Header with Navigation & Export
    col_nav_b, col_nav_m, col_nav_dl = st.columns([1.2, 3, 1.5])
    with col_nav_b:
        if st.button(t("back_to_home"), key="back_from_reports_btn"):
            navigate_to("home")
            st.rerun()
    with col_nav_m:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.4rem; color: #386641;">✔</span>
            <h3 style="margin: 0; color: #1c3d23;">{t('rec_title')}</h3>
        </div>
        """, unsafe_allow_html=True)
    with col_nav_dl:
        advisory_card = f"""JALSAARTHI CROP DECISION ADVISORY
District: {location_option.title()}
Farm Land: {farm_size_acres} Acres
Recommended Crop: {top_crop} ({get_crop_name(top_crop)})
Resilience-Return Index: {top['resilience_return_index']} / 100
Expected Net Profit: Rs. {top_fin['expected_profit_rs']:,.0f} ({top_fin['range_display_profit_rs']})
Irrigation Water Needed: {top_wat['water_required_m3']:,.0f} m3
Harvest Yield: {top_yld['total_yield_kg']:,.0f} kg ({top_yld['range_display_kg']})
Mandi Benchmark: Rs. {top_fin.get('market_price_per_q', 0)}/q ({top_fin.get('mandi_name', 'APMC')})
"""
        st.download_button(
            label=t("download_report"),
            data=advisory_card,
            file_name=f"JalSaarthi_Report_{top_crop}_{location_option}.txt",
            mime="text/plain",
            key="dl_report_btn"
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Active Scenario Stress Alert if any shock is applied
    if st.session_state["whatif_rain"] != 0 or st.session_state["whatif_water"] != 0 or st.session_state["whatif_temp"] != 0 or st.session_state["whatif_budget"] != 0:
        badges = []
        if st.session_state["whatif_rain"] != 0: badges.append(f"🌧️ Rainfall {st.session_state['whatif_rain']:+d}%")
        if st.session_state["whatif_water"] != 0: badges.append(f"💧 Borewell {st.session_state['whatif_water']}%")
        if st.session_state["whatif_temp"] != 0: badges.append(f"🌡️ Heatwave +{st.session_state['whatif_temp']}°C")
        if st.session_state["whatif_budget"] != 0: badges.append(f"💰 Budget ₹{st.session_state['whatif_budget']:,}")
        
        col_sb1, col_sb2 = st.columns([3.5, 1.2])
        with col_sb1:
            st.warning(f"⚡ **Active Climate Shock Applied**: {', '.join(badges)}. All metrics, yields, and RRI rankings reflect this scenario.")
        with col_sb2:
            st.button("🔄 Reset to Baseline", key="rep_clear_shock_btn", on_click=reset_scenario_shocks, use_container_width=True)

    # Top Row: 3 Highlight Cards
    r1, r2, r3 = st.columns(3)
    with r1:
        st.markdown(f"""
        <div class="pastel-card pastel-card-green" style="padding: 20px;">
            <div style="font-size: 2.2rem;">🌱</div>
            <div class="pastel-card-label">{t('rec_card_crop')}</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #1c3d23;">{get_crop_name(top_crop)}</div>
            <div class="pastel-card-sub">{top['category']} • {CROPS.get(top_crop, {}).get('duration_days', 110)} Days</div>
        </div>
        """, unsafe_allow_html=True)
        
    with r2:
        water_desc = "0 m³ (100% Rainfed)" if top_wat['water_required_m3'] <= 0 else f"{top_wat['water_required_m3']:,.0f} m³"
        st.markdown(f"""
        <div class="pastel-card pastel-card-blue" style="padding: 20px;">
            <div style="font-size: 2.2rem;">💧</div>
            <div class="pastel-card-label">{t('rec_card_water')}</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #1b5275;">{water_desc}</div>
            <div class="pastel-card-sub">Crop ETc: {top_wat.get('crop_demand_m3', 0):,.0f} m³</div>
        </div>
        """, unsafe_allow_html=True)
        
    with r3:
        st.markdown(f"""
        <div class="pastel-card pastel-card-purple" style="padding: 20px;">
            <div style="font-size: 2.2rem;">💰</div>
            <div class="pastel-card-label">{t('rec_card_profit')}</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #5c246f;">₹{top_fin['expected_profit_rs']:,.0f}</div>
            <div class="pastel-card-sub">{top_fin['range_display_profit_rs']}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # Two-Column Section: Yield vs Risk Overview Chart & "Why [Crop]?"
    col_chart, col_why = st.columns([1.5, 1.2])
    
    with col_chart:
        st.markdown(f"#### 📈 {t('chart_title')}")
        chart_data = []
        for p in all_ranked:
            chart_data.append({
                "Crop": get_crop_name(p["crop"]),
                "Yield": p["yield_metrics"]["yield_q_ha"],
                "Risk Level": p["climate_metrics"]["risk_score"]
            })
        df_chart = pd.DataFrame(chart_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_chart["Crop"],
            y=df_chart["Yield"],
            name=t("chart_yield_legend"),
            marker_color="#386641"
        ))
        fig.add_trace(go.Bar(
            x=df_chart["Crop"],
            y=df_chart["Risk Level"],
            name=t("chart_risk_legend"),
            marker_color="#d48b38"
        ))
        fig.update_layout(
            barmode="group",
            height=300,
            margin=dict(l=10, r=10, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col_why:
        st.markdown(f"#### 💡 {t('why_title', crop=get_crop_name(top_crop))}")
        st.markdown(f"""
        <div style="background: #ffffff; border-radius: 14px; padding: 18px; border: 1.5px solid #d4e6d4; box-shadow: 0 2px 8px rgba(40,75,48,0.03);">
            <div class="check-item"><span class="check-icon">✔</span><span>{t('why_point_1')}</span></div>
            <div class="check-item"><span class="check-icon">✔</span><span>{t('why_point_2')}</span></div>
            <div class="check-item"><span class="check-icon">✔</span><span>{t('why_point_3')} (<b>₹{top_fin.get('market_price_per_q', 0):,.0f}/q</b> at {top_fin.get('mandi_name', 'APMC')})</span></div>
            <div class="check-item"><span class="check-icon">✔</span><span>{t('why_point_4')}</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"💡 *{why_won_text}*")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Clean Comparative Summary Table (5-Second Scan)
    with st.expander(f"📋 {t('all_crops_title')}", expanded=True):
        tbl_data = []
        for p in all_ranked:
            c_fin = p["financial_metrics"]
            c_wat = p["water_metrics"]
            c_clim = p["climate_metrics"]
            c_yld = p["yield_metrics"]
            
            status_badge = "🔴 Deficit" if not c_wat["water_feasible"] else ("🟡 High Risk" if c_clim["risk_level"] == "High" else "🟢 Viable")
            water_req = "0 m³ (Rainfed)" if c_wat["water_required_m3"] <= 0 else f"{c_wat['water_required_m3']:,.0f} m³"
            
            tbl_data.append({
                "Crop": get_crop_name(p["crop"]),
                "RRI Score": f"{p['resilience_return_index']} / 100",
                "Status": status_badge,
                "Net Profit": f"₹{c_fin['expected_profit_rs']:,.0f}",
                "Mandi Rate": f"₹{c_fin.get('market_price_per_q', 0):,.0f} / q",
                "Water Needed": water_req,
                "Yield": c_yld["range_display_kg"],
                "Climate Vulnerability": f"{c_clim['risk_level']} ({c_clim['risk_score']}/100)"
            })
        st.dataframe(pd.DataFrame(tbl_data), use_container_width=True, hide_index=True)

    # Multi-Season Systems Crop Rotation Card
    with st.expander(f"{t('rotation_title')}", expanded=False):
        rot_res = evaluate_annual_rotation(
            farm_size_acres=farm_size_acres,
            available_budget_rs=available_budget_rs,
            available_water_m3=available_water_m3,
            location=location_option
        )
        st.info(f"🌾 **{rot_res.get('systems_verdict', '')}**")

    # Bottom Call to Action Button
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    if st.button(t("btn_explore_scenarios"), use_container_width=True, key="rep_explore_scen_btn"):
        navigate_to("scenario")
        st.rerun()

# =================================================================================================
# VIEW 3: 🔄 SCENARIO ANALYSIS (Climate Stress & Shocks)
# =================================================================================================
elif st.session_state["nav_view"] == "scenario":
    col_scen_b, col_scen_title = st.columns([1.2, 4.5])
    with col_scen_b:
        if st.button(t("back_to_home"), key="back_from_scen_btn"):
            navigate_to("reports")
            st.rerun()
    with col_scen_title:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 1.6rem;">🔄</span>
            <h2 style="margin: 0; color: #1c3d23;">{t('scenario_title')}</h2>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown(f"<p style='color: #4a634e; font-size: 0.95rem; margin-top: 4px; margin-bottom: 20px;'>{t('scenario_subtitle')}</p>", unsafe_allow_html=True)

    # Active Scenario Banner if any stress is active
    if st.session_state["whatif_rain"] != 0 or st.session_state["whatif_water"] != 0 or st.session_state["whatif_temp"] != 0 or st.session_state["whatif_budget"] != 0:
        badges = []
        if st.session_state["whatif_rain"] != 0: badges.append(f"Rainfall {st.session_state['whatif_rain']:+d}%")
        if st.session_state["whatif_water"] != 0: badges.append(f"Borewell {st.session_state['whatif_water']}%")
        if st.session_state["whatif_temp"] != 0: badges.append(f"Heatwave +{st.session_state['whatif_temp']}°C")
        if st.session_state["whatif_budget"] != 0: badges.append(f"Budget ₹{st.session_state['whatif_budget']:,}")
        st.warning(t("active_shock_alert", details=", ".join(badges)))

    # Dynamically compute actual winners for the 3 shock presets
    s1_res = optimize_farming_strategy(
        farm_size_acres=farm_size_acres, available_budget_rs=available_budget_rs,
        available_water_m3=available_water_m3, location=location_option,
        soil_type=soil_type, irrigation_method=irrigation_method,
        rainfall_shift_pct=-20.0
    )
    s1_crop = s1_res["top_recommendation"]["crop"]
    s1_rri = s1_res["top_recommendation"]["resilience_return_index"]

    s2_res = optimize_farming_strategy(
        farm_size_acres=farm_size_acres, available_budget_rs=available_budget_rs,
        available_water_m3=available_water_m3, location=location_option,
        soil_type=soil_type, irrigation_method=irrigation_method,
        water_shift_pct=-30.0
    )
    s2_crop = s2_res["top_recommendation"]["crop"]
    s2_rri = s2_res["top_recommendation"]["resilience_return_index"]

    s3_budget_cut = float(available_budget_rs * 0.20)
    s3_res = optimize_farming_strategy(
        farm_size_acres=farm_size_acres, available_budget_rs=available_budget_rs,
        available_water_m3=available_water_m3, location=location_option,
        soil_type=soil_type, irrigation_method=irrigation_method,
        budget_shift_rs=-s3_budget_cut
    )
    s3_crop = s3_res["top_recommendation"]["crop"]
    s3_rri = s3_res["top_recommendation"]["resilience_return_index"]

    # 3 Quick Shock Preset Cards (Fully Connected)
    st.markdown(f"#### {t('quick_scenarios_title')}")
    sc1, sc2, sc3 = st.columns(3)
    
    with sc1:
        st.markdown(f"""
        <div class="scenario-card">
            <div style="font-size: 2rem;">🌧️</div>
            <div class="scenario-card-title">{t('scen_rain_title')}</div>
            <div class="scenario-card-sub">{t('scen_rain_sub')}</div>
            <div class="scenario-card-crop">{get_crop_name(s1_crop)} <span style="font-size: 0.82rem; font-weight: normal; color: #555;">(RRI: {s1_rri})</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.button(
            t("btn_view_details"),
            key="btn_apply_shock_rain",
            on_click=apply_preset_shock,
            kwargs={"rain": -20, "target_view": "reports"},
            use_container_width=True
        )

    with sc2:
        st.markdown(f"""
        <div class="scenario-card">
            <div style="font-size: 2rem;">💧</div>
            <div class="scenario-card-title">{t('scen_water_title')}</div>
            <div class="scenario-card-sub">{t('scen_water_sub')}</div>
            <div class="scenario-card-crop">{get_crop_name(s2_crop)} <span style="font-size: 0.82rem; font-weight: normal; color: #555;">(RRI: {s2_rri})</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.button(
            t("btn_view_details"),
            key="btn_apply_shock_water",
            on_click=apply_preset_shock,
            kwargs={"water": -30, "target_view": "reports"},
            use_container_width=True
        )

    with sc3:
        st.markdown(f"""
        <div class="scenario-card">
            <div style="font-size: 2rem;">💰</div>
            <div class="scenario-card-title">{t('scen_budget_title')}</div>
            <div class="scenario-card-sub">{t('scen_budget_sub')}</div>
            <div class="scenario-card-crop">{get_crop_name(s3_crop)} <span style="font-size: 0.82rem; font-weight: normal; color: #555;">(RRI: {s3_rri})</span></div>
        </div>
        """, unsafe_allow_html=True)
        st.button(
            t("btn_view_details"),
            key="btn_apply_shock_budget",
            on_click=apply_preset_shock,
            kwargs={"budget": -int(s3_budget_cut), "target_view": "reports"},
            use_container_width=True
        )

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # Interactive Sliders for Custom Fine-Tuning
    st.markdown(f"#### {t('custom_simulator_title')}")
    
    if "slider_rain" not in st.session_state: st.session_state["slider_rain"] = int(st.session_state["whatif_rain"])
    if "slider_water" not in st.session_state: st.session_state["slider_water"] = int(st.session_state["whatif_water"])
    if "slider_temp" not in st.session_state: st.session_state["slider_temp"] = float(st.session_state["whatif_temp"])
    if "slider_budget" not in st.session_state: st.session_state["slider_budget"] = int(st.session_state["whatif_budget"])

    with st.container():
        c_s1, c_s2 = st.columns(2)
        with c_s1:
            st.slider(
                t("slider_rain"),
                min_value=-40,
                max_value=40,
                step=5,
                key="slider_rain"
            )
            st.session_state["whatif_rain"] = st.session_state["slider_rain"]
            
            st.slider(
                t("slider_water"),
                min_value=-50,
                max_value=0,
                step=10,
                key="slider_water"
            )
            st.session_state["whatif_water"] = st.session_state["slider_water"]
            
        with c_s2:
            st.slider(
                t("slider_temp"),
                min_value=0.0,
                max_value=3.5,
                step=0.5,
                key="slider_temp"
            )
            st.session_state["whatif_temp"] = st.session_state["slider_temp"]
            
            st.slider(
                t("slider_budget"),
                min_value=-25000,
                max_value=0,
                step=5000,
                format="₹%d",
                key="slider_budget"
            )
            st.session_state["whatif_budget"] = st.session_state["slider_budget"]

    # Action Buttons: Reset and View in Reports
    col_act1, col_act2 = st.columns([1, 1.6])
    with col_act1:
        st.button("🔄 Reset All Scenarios", key="reset_scenarios_btn", on_click=reset_scenario_shocks, use_container_width=True)
    with col_act2:
        if st.button("📊 " + t("btn_explore_scenarios"), key="view_rep_from_scen_btn", use_container_width=True):
            navigate_to("reports")
            st.rerun()

    # Dynamic Scenario Output Card
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    if is_crisis:
        st.error(f"🚨 **CRITICAL RESOURCE ALERT**: No crop is 100% viable at full {farm_size_acres} acres scale under this shock!")
        st.warning(f"🛡️ **Actionable Mitigation**: Downscale {top_crop} to **{emit.get('safe_cultivable_acres', 1.0)} Acres** to eliminate deficits, convert to drip irrigation, and preserve remaining soil under mulch.")
    else:
        st.success(f"🌾 **Optimal Adaptive Crop Under Active Scenario**: **{get_crop_name(top_crop)}** (RRI: {top['resilience_return_index']}/100, Net Profit: ₹{top_fin['expected_profit_rs']:,.0f})")

# =================================================================================================
# VIEW 4: ℹ️ HOW TO USE / INFORMATION (Horizontal Matcha Green Button Tabs)
# =================================================================================================
elif st.session_state["nav_view"] == "info":
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 4px;">
        <span style="font-size: 1.8rem;">ℹ️</span>
        <h2 style="margin: 0; color: #1c3d23;">{t('info_title')}</h2>
    </div>
    <p style="color: #4a634e; font-size: 0.95rem; margin-bottom: 20px;">{t('info_subtitle')}</p>
    """, unsafe_allow_html=True)

    # Horizontal Tabs Styled as Modern Green Button Pills
    tab_guide, tab_method, tab_mandi, tab_crops = st.tabs([
        "📖 User Guide",
        "🔬 Scientific Methodology",
        "📊 APMC Mandi Rates",
        "🌾 Regional Crop Profiles"
    ])

    with tab_guide:
        st.markdown(f"""
        <div style="background: #ffffff; border-radius: 14px; padding: 20px; border: 1.5px solid #d4e6d4; margin-bottom: 14px; box-shadow: 0 2px 8px rgba(40,75,48,0.03);">
            <h4 style="color: #1c3d23; margin-top: 0;">{t('guide_step_1_title')}</h4>
            <p style="color: #444; margin: 0; line-height: 1.45;">{t('guide_step_1_desc')}</p>
        </div>
        
        <div style="background: #ffffff; border-radius: 14px; padding: 20px; border: 1.5px solid #d4e6d4; margin-bottom: 14px; box-shadow: 0 2px 8px rgba(40,75,48,0.03);">
            <h4 style="color: #1c3d23; margin-top: 0;">{t('guide_step_2_title')}</h4>
            <p style="color: #444; margin: 0; line-height: 1.45;">{t('guide_step_2_desc')}</p>
        </div>
        
        <div style="background: #ffffff; border-radius: 14px; padding: 20px; border: 1.5px solid #d4e6d4; margin-bottom: 14px; box-shadow: 0 2px 8px rgba(40,75,48,0.03);">
            <h4 style="color: #1c3d23; margin-top: 0;">{t('guide_step_3_title')}</h4>
            <p style="color: #444; margin: 0; line-height: 1.45;">{t('guide_step_3_desc')}</p>
        </div>
        
        <div style="background: #ffffff; border-radius: 14px; padding: 20px; border: 1.5px solid #d4e6d4; margin-bottom: 14px; box-shadow: 0 2px 8px rgba(40,75,48,0.03);">
            <h4 style="color: #1c3d23; margin-top: 0;">{t('guide_step_4_title')}</h4>
            <p style="color: #444; margin: 0; line-height: 1.45;">{t('guide_step_4_desc')}</p>
        </div>
        """, unsafe_allow_html=True)

    with tab_method:
        st.markdown(r"""
        #### 1. Hydrological Modeling (FAO-56 Standard)
        - **Reference Evapotranspiration ($ET_0$)**: FAO-56 Hargreaves-Samani equation:
          $$ET_0 = 0.0023 	imes R_a 	imes (T_{	ext{mean}} + 17.8) 	imes (T_{	ext{max}} - T_{	ext{min}})^{0.5} 	imes 0.408$$
        - **Crop Demand ($ET_c$)**: Stage-wise interpolation: $ET_c(t) = K_c(t) 	imes ET_0(t)$.
        - **Net Irrigation Requirement**: $	ext{NIR} = \max(0, ET_c - P_{	ext{eff}})$.
        
        #### 2. Machine Learning Yield Model
        - **Model**: `RandomForestRegressor(n_estimators=150, max_depth=12, random_state=42)`
        - **Validation**: Test $R^2 = 0.9663$, Test RMSE = $182.8	ext{ kg/ha}$.
        - **Prediction Intervals**: 90% confidence bands ($\pm 9\%$) derived from residual variance.
        
        #### 3. Multi-Objective Resilience-Return Index (RRI)
        $$	ext{RRI} = 0.45 \cdot \widetilde{	ext{Profit}} + 0.30 \cdot (1 - \widetilde{	ext{WaterUsed}}) + 0.25 \cdot (1 - \widetilde{	ext{ClimateRisk}}) - 	ext{Penalties}$$
        
        #### 4. Rural Pump Discharge Standards (BIS 9283 & MSEDCL)
        $$V_{	ext{seasonal}} = Q_{	ext{flow}} (	ext{m}^3/	ext{hr}) 	imes H_{	ext{daily}} (	ext{hrs/day}) 	imes D_{	ext{season}} (	ext{days})$$
        """)

    with tab_mandi:
        st.markdown("#### 📊 Official Agmarknet APMC Price Benchmarks (Updated September 2026)")
        if MANDI_DF is not None and not MANDI_DF.empty:
            df_disp = MANDI_DF.copy().rename(columns={
                "crop": "Crop", "district": "District", "mandi_name": "APMC Mandi",
                "modal_price_rs_q": "Modal Price (₹/q)", "msp_rs_q": "Govt MSP (₹/q)",
                "arrival_tonnes": "Arrivals (T)", "as_of_date": "Updated As Of"
            })
            st.dataframe(df_disp, use_container_width=True, hide_index=True)
        else:
            st.info("Mandi snapshots loaded from CACP benchmark standards.")

    with tab_crops:
        st.markdown("#### 🌾 Regional Crop Specifications")
        for cname, cdata in CROPS.items():
            with st.expander(f"{cname} ({cdata.get('name_mr', cname)}) — {cdata.get('category', '')}"):
                st.write(f"**Duration:** {cdata.get('duration_days')} days | **Rooting Depth:** {cdata.get('rooting_depth_m')}m")
                st.write(f"**Benchmark Yield:** {cdata.get('benchmark_yield_q_ha')} q/ha | **Base Cost:** ₹{cdata.get('base_cost_per_ha'):,.0f}/ha")
                st.write(f"**Soil Impact:** {cdata.get('soil_nutrient_impact')} | **Description:** {cdata.get('description')}")
