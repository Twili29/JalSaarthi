"""
JalSaarthi - Climate Risk Engine
Evaluates:
1. IMD-aligned Rainfall Deficit Index (deviation from long-term normal)
2. Dry Spell Hazard (consecutive days with rain < 2.5mm during critical growth phases)
3. Heat Stress Hazard (frequency of Tmax > 38°C)
4. Crop-specific vulnerability weighting
5. Composite Climate Risk Score [0 - 100] (Low, Moderate, High)
"""

import os
import sys
from typing import Dict, Any, List
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from engine.crop_database import CROPS
except ImportError:
    from crop_database import CROPS

# IMD Long-term normal seasonal rainfall benchmarks (mm) for Maharashtra Semi-Arid Zone
CLIMATE_NORMALS = {
    "solapur": {
        "kharif_normal_rain_mm": 520.0,
        "rabi_normal_rain_mm": 135.0,
        "mean_monsoon_tmax_c": 32.5
    },
    "pune": {
        "kharif_normal_rain_mm": 720.0,
        "rabi_normal_rain_mm": 110.0,
        "mean_monsoon_tmax_c": 29.5
    }
}

CROP_RISK_WEIGHTS = {
    "Cotton": {"drought": 0.45, "dry_spell": 0.35, "heat": 0.20},
    "Maize": {"drought": 0.40, "dry_spell": 0.40, "heat": 0.20},
    "Soybean": {"drought": 0.35, "dry_spell": 0.35, "heat": 0.30},
    "Gram": {"drought": 0.25, "dry_spell": 0.20, "heat": 0.55},     # Gram suffers mostly from heat at pod maturity
    "Jowar": {"drought": 0.20, "dry_spell": 0.15, "heat": 0.15}     # Highly resilient across all hazards
}

def analyze_climate_risk(
    crop_name: str,
    daily_weather_df: pd.DataFrame,
    location_key: str = "solapur",
    rainfall_multiplier: float = 1.0,
    temp_shift_c: float = 0.0
) -> Dict[str, Any]:
    """
    Computes rigorous climate risk metrics based on observed/forecast weather.
    Supports 'What-If' scenarios via rainfall_multiplier and temp_shift_c.
    """
    if crop_name not in CROPS:
        raise ValueError(f"Unknown crop: {crop_name}")
        
    normals = CLIMATE_NORMALS.get(location_key, CLIMATE_NORMALS["solapur"])
    weights = CROP_RISK_WEIGHTS.get(crop_name, {"drought": 0.34, "dry_spell": 0.33, "heat": 0.33})
    
    # Adjust weather series according to scenario
    sim_df = daily_weather_df.copy()
    sim_df["precipitation_mm"] = sim_df["precipitation_mm"] * max(0.0, rainfall_multiplier)
    sim_df["temp_max_c"] = sim_df["temp_max_c"] + temp_shift_c
    
    total_rain = float(sim_df["precipitation_mm"].sum())
    normal_rain = normals["kharif_normal_rain_mm"]
    
    # 1. IMD Rainfall Deviation Percentage
    rain_deviation_pct = ((total_rain - normal_rain) / normal_rain) * 100.0
    
    if rain_deviation_pct >= 20.0:
        imd_category = "Excess (+20% or more)"
        rain_risk_subscore = 15.0  # Excess can cause waterlogging
    elif rain_deviation_pct >= -19.0:
        imd_category = "Normal (-19% to +19%)"
        rain_risk_subscore = 25.0
    elif rain_deviation_pct >= -59.0:
        imd_category = "Deficient (-20% to -59%)"
        # Linear scaling from 40 to 80
        deficit_ratio = abs(rain_deviation_pct - (-19.0)) / 40.0
        rain_risk_subscore = 40.0 + deficit_ratio * 40.0
    else:
        imd_category = "Severe Deficit (-60% or worse)"
        rain_risk_subscore = 95.0
        
    # 2. Dry Spell Hazard (consecutive days with rain < 2.5 mm, standard IMD threshold)
    rain_series = sim_df["precipitation_mm"].values
    dry_days = (rain_series < 2.5).astype(int)
    
    max_consecutive_dry_days = 0
    current_dry_streak = 0
    for d in dry_days:
        if d == 1:
            current_dry_streak += 1
            max_consecutive_dry_days = max(max_consecutive_dry_days, current_dry_streak)
        else:
            current_dry_streak = 0
            
    if max_consecutive_dry_days <= 8:
        dry_spell_risk_subscore = 20.0
    elif max_consecutive_dry_days <= 15:
        dry_spell_risk_subscore = 45.0
    elif max_consecutive_dry_days <= 24:
        dry_spell_risk_subscore = 75.0
    else:
        dry_spell_risk_subscore = 95.0
        
    # 3. Extreme Heat Days (Tmax > 38 C)
    tmax_series = sim_df["temp_max_c"].values
    heat_days = int(np.sum(tmax_series > 38.0))
    
    if heat_days == 0:
        heat_risk_subscore = 10.0
    elif heat_days <= 5:
        heat_risk_subscore = 35.0
    elif heat_days <= 12:
        heat_risk_subscore = 65.0
    else:
        heat_risk_subscore = 90.0
        
    # 4. Composite Risk Score
    composite_raw = (
        rain_risk_subscore * weights["drought"] +
        dry_spell_risk_subscore * weights["dry_spell"] +
        heat_risk_subscore * weights["heat"]
    )
    
    # Specific crop resilience factor
    crop_info = CROPS[crop_name]
    if crop_name == "Jowar":
        composite_score = round(composite_raw * 0.65, 1)  # Naturally resilient
    elif crop_name == "Gram":
        composite_score = round(composite_raw * 0.75, 1)
    elif crop_name == "Soybean":
        composite_score = round(composite_raw * 0.90, 1)
    elif crop_name == "Cotton":
        composite_score = round(min(100.0, composite_raw * 1.15), 1)
    else:
        composite_score = round(min(100.0, composite_raw * 1.05), 1)
        
    # Categorization
    if composite_score <= 35.0:
        risk_level = "Low"
        color = "green"
    elif composite_score <= 65.0:
        risk_level = "Medium"
        color = "amber"
    else:
        risk_level = "High"
        color = "red"
        
    return {
        "crop_name": crop_name,
        "composite_risk_score": composite_score,
        "risk_level": risk_level,
        "color": color,
        "total_season_rainfall_mm": round(total_rain, 1),
        "normal_season_rainfall_mm": normal_rain,
        "rainfall_deviation_pct": round(rain_deviation_pct, 1),
        "imd_rainfall_category": imd_category,
        "max_consecutive_dry_days": max_consecutive_dry_days,
        "extreme_heat_days_gt_38c": heat_days,
        "subscores": {
            "rainfall_deficit_risk": round(rain_risk_subscore, 1),
            "dry_spell_risk": round(dry_spell_risk_subscore, 1),
            "heat_stress_risk": round(heat_risk_subscore, 1)
        }
    }

if __name__ == "__main__":
    # Test on Solapur data if available
    try:
        df = pd.read_csv("data/raw/weather_daily_solapur.csv")
        sample_season = df[df["month"].isin([6, 7, 8, 9, 10])].head(120)
        for crop in CROPS.keys():
            res = analyze_climate_risk(crop, sample_season)
            print(f"[{crop}] Risk Score: {res['composite_risk_score']}/100 ({res['risk_level']}) | Dev: {res['rainfall_deviation_pct']}% | Dry Streak: {res['max_consecutive_dry_days']}d")
    except Exception as e:
        print(f"Test run notice: {e}")
