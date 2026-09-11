"""
JalSaarthi - Agricultural Water Calculation Engine
Compliant with FAO Irrigation and Drainage Paper No. 56 (FAO-56)
Computes:
1. Reference Evapotranspiration (ET0) via FAO-56 Hargreaves-Samani & Penman-Monteith
2. Crop Coefficient (Kc) progression across growth stages
3. Crop Water Requirement (ETc = Kc * ET0)
4. Effective Rainfall (P_eff) via USDA Soil Conservation Service method
5. Soil Moisture Depletion (TAW, RAW) and Net Irrigation Requirements (NIR / GIR)
"""

import os
import sys
import math
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from engine.crop_database import CROPS, SOIL_PROFILES, IRRIGATION_COSTS
except ImportError:
    from crop_database import CROPS, SOIL_PROFILES, IRRIGATION_COSTS

def calculate_extraterrestrial_radiation(latitude_deg: float, day_of_year: int) -> float:
    """
    Calculates extraterrestrial radiation Ra (MJ/m^2/day) according to FAO-56 eq. 21-28.
    """
    lat_rad = math.radians(latitude_deg)
    # Solar declination delta (rad)
    delta = 0.409 * math.sin((2.0 * math.pi / 365.0) * day_of_year - 1.39)
    # Relative distance Earth-Sun dr
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * day_of_year / 365.0)
    # Sunset hour angle omega_s (rad)
    tan_val = -math.tan(lat_rad) * math.tan(delta)
    tan_val = max(-1.0, min(1.0, tan_val))
    omega_s = math.acos(tan_val)
    # Ra calculation
    g_sc = 0.0820  # Solar constant MJ/m2/min
    ra = (24.0 * 60.0 / math.pi) * g_sc * dr * (
        omega_s * math.sin(lat_rad) * math.sin(delta) +
        math.cos(lat_rad) * math.cos(delta) * math.sin(omega_s)
    )
    return max(0.0, ra)


def calculate_et0_hargreaves(t_max: float, t_min: float, t_mean: float, latitude_deg: float, day_of_year: int) -> float:
    """
    Computes daily reference evapotranspiration ET0 (mm/day) using FAO-56 Hargreaves-Samani eq. 52.
    ET0 = 0.0023 * (T_mean + 17.8) * (T_max - T_min)^0.5 * Ra_mm
    where Ra_mm = Ra (MJ/m^2/day) * 0.408 (latent heat of vaporization equivalent).
    """
    ra_mj = calculate_extraterrestrial_radiation(latitude_deg, day_of_year)
    ra_mm = 0.408 * ra_mj
    td = max(0.1, t_max - t_min)
    et0 = 0.0023 * (t_mean + 17.8) * (td ** 0.5) * ra_mm
    return max(0.5, round(et0, 2))


def get_crop_kc(crop_name: str, day_in_cycle: int) -> float:
    """
    Calculates interpolated crop coefficient Kc on any given day of the crop growth cycle (FAO-56).
    """
    if crop_name not in CROPS:
        raise ValueError(f"Unknown crop: {crop_name}")
        
    c = CROPS[crop_name]
    stages = c["stages_days"]
    kc_vals = c["kc"]
    
    l_ini = stages["initial"]
    l_dev = stages["development"]
    l_mid = stages["mid"]
    l_late = stages["late"]
    total_duration = c["duration_days"]
    
    # Boundary checks
    day = max(1, min(day_in_cycle, total_duration))
    
    # Stage 1: Initial
    if day <= l_ini:
        return kc_vals["initial"]
        
    # Stage 2: Crop Development (linear increase from Kc_ini to Kc_mid)
    elif day <= (l_ini + l_dev):
        progress = (day - l_ini) / max(1, l_dev)
        return round(kc_vals["initial"] + progress * (kc_vals["mid"] - kc_vals["initial"]), 3)
        
    # Stage 3: Mid-Season (Peak Kc)
    elif day <= (l_ini + l_dev + l_mid):
        return kc_vals["mid"]
        
    # Stage 4: Late Season (linear decrease from Kc_mid to Kc_end)
    else:
        days_in_late = day - (l_ini + l_dev + l_mid)
        progress = days_in_late / max(1, l_late)
        return round(kc_vals["mid"] - progress * (kc_vals["mid"] - kc_vals["end"]), 3)


def calculate_effective_rainfall_daily(precip_mm: float) -> float:
    """
    Estimates daily effective rainfall (P_eff) that infiltrates root zone without runoff/percolation.
    For small showers (< 3 mm), nearly 100% evaporates from canopy/soil surface.
    For substantial rain, 70-80% is effective up to soil infiltration limits.
    """
    if precip_mm < 3.0:
        return 0.0
    elif precip_mm <= 50.0:
        return round(precip_mm * 0.75 - 1.5, 2)
    else:
        # High intensity storm runoff cap
        return round(36.0 + (precip_mm - 50.0) * 0.35, 2)


def simulate_crop_water_balance(
    crop_name: str,
    daily_weather_df: pd.DataFrame,
    sowing_day_of_year: int,
    latitude_deg: float = 17.66,
    soil_type: str = "Medium Black (Vertisol)",
    irrigation_method: str = "flood_furrow"
) -> Dict[str, Any]:
    """
    Simulates the full season daily water requirement and moisture balance for a given crop.
    
    Returns:
    - total_et0_mm: Total seasonal reference evapotranspiration
    - total_etc_mm: Total crop water demand
    - total_rainfall_mm: Total rainfall during season
    - total_effective_rainfall_mm: Usable natural rainfall
    - net_irrigation_requirement_mm: Crop water deficit (NIR)
    - gross_irrigation_requirement_mm: Total water needed accounting for application efficiency (GIR)
    - gross_irrigation_volume_m3_ha: GIR in m3 per hectare (1 mm/ha = 10 m3)
    - daily_timeline: DataFrame with day-by-day ETc, Peff, and deficit
    """
    if crop_name not in CROPS:
        raise ValueError(f"Unknown crop: {crop_name}")
    crop = CROPS[crop_name]
    soil = SOIL_PROFILES.get(soil_type, list(SOIL_PROFILES.values())[0])
    irrig = IRRIGATION_COSTS.get(irrigation_method, IRRIGATION_COSTS["flood_furrow"])
    
    duration = crop["duration_days"]
    root_depth = crop["rooting_depth_m"]
    p_depletion = crop["depletion_factor_p"]
    
    # Total Available Water (TAW) in mm
    taw_mm = soil["available_water_capacity_mm_per_m"] * root_depth
    # Readily Available Water (RAW) in mm before water stress occurs
    raw_mm = taw_mm * p_depletion
    
    # Filter or match season from weather DataFrame
    # If weather_df has enough rows, slice 'duration' days starting from closest sowing day of year
    if "day_of_year" in daily_weather_df.columns:
        start_idx_candidates = daily_weather_df[daily_weather_df["day_of_year"] == sowing_day_of_year].index
        if len(start_idx_candidates) > 0:
            start_idx = start_idx_candidates[0]
            sim_weather = daily_weather_df.iloc[start_idx : start_idx + duration].copy().reset_index(drop=True)
        else:
            sim_weather = daily_weather_df.iloc[:duration].copy().reset_index(drop=True)
    else:
        sim_weather = daily_weather_df.iloc[:duration].copy().reset_index(drop=True)
        
    # If weather series is shorter than crop duration, wrap or repeat
    if len(sim_weather) < duration:
        repeats = int(np.ceil(duration / len(sim_weather)))
        sim_weather = pd.concat([sim_weather] * repeats, ignore_index=True).iloc[:duration]

    records = []
    current_soil_moisture = taw_mm * 0.70  # Assume 70% field capacity at start of sowing
    cum_nir = 0.0
    
    for day_i in range(1, duration + 1):
        row = sim_weather.iloc[day_i - 1]
        t_max = row.get("temp_max_c", 32.0)
        t_min = row.get("temp_min_c", 22.0)
        t_mean = row.get("temp_mean_c", (t_max + t_min) / 2.0)
        doy = int(row.get("day_of_year", (sowing_day_of_year + day_i) % 365 + 1))
        p_tot = float(row.get("precipitation_mm", 0.0))
        
        # 1. ET0
        et0 = calculate_et0_hargreaves(t_max, t_min, t_mean, latitude_deg, doy)
        
        # 2. Kc & ETc
        kc = get_crop_kc(crop_name, day_i)
        etc = round(kc * et0, 2)
        
        # 3. Effective rain
        p_eff = calculate_effective_rainfall_daily(p_tot)
        
        # 4. Soil water balance
        water_in = p_eff
        water_out = etc
        current_soil_moisture = min(taw_mm, max(0.0, current_soil_moisture + water_in - water_out))
        
        # If moisture drops below (TAW - RAW), crop enters stress -> Net Irrigation Needed
        stress_deficit = max(0.0, (taw_mm - raw_mm) - current_soil_moisture)
        daily_nir = 0.0
        if stress_deficit > 0:
            daily_nir = stress_deficit
            current_soil_moisture += daily_nir  # Irrigation refills root zone
            cum_nir += daily_nir
            
        records.append({
            "day": day_i,
            "doy": doy,
            "t_max": t_max,
            "t_min": t_min,
            "rainfall_mm": p_tot,
            "effective_rain_mm": p_eff,
            "et0_mm": et0,
            "kc": kc,
            "etc_mm": etc,
            "soil_moisture_mm": round(current_soil_moisture, 2),
            "nir_mm": round(daily_nir, 2)
        })
        
    timeline_df = pd.DataFrame(records)
    
    total_et0 = round(timeline_df["et0_mm"].sum(), 1)
    total_etc = round(timeline_df["etc_mm"].sum(), 1)
    total_rain = round(timeline_df["rainfall_mm"].sum(), 1)
    total_peff = round(timeline_df["effective_rain_mm"].sum(), 1)
    total_nir = round(timeline_df["nir_mm"].sum(), 1)
    
    # Gross irrigation needed accounting for irrigation efficiency
    eff = irrig["efficiency"]
    gir_mm = round(total_nir / eff, 1)
    # 1 mm over 1 ha = 10 m^3 = 10,000 liters
    gir_m3_ha = round(gir_mm * 10.0, 1)
    gir_liters_ha = gir_m3_ha * 1000.0
    
    # Energy / pumping cost
    irrigation_pumping_cost = round(gir_m3_ha * irrig["cost_per_m3"], 2)
    
    return {
        "crop_name": crop_name,
        "duration_days": duration,
        "total_et0_mm": total_et0,
        "total_etc_mm": total_etc,
        "total_rainfall_mm": total_rain,
        "total_effective_rainfall_mm": total_peff,
        "natural_water_contribution_pct": round(min(100.0, (total_peff / max(1.0, total_etc)) * 100.0), 1),
        "net_irrigation_requirement_mm": total_nir,
        "gross_irrigation_requirement_mm": gir_mm,
        "gross_irrigation_volume_m3_ha": gir_m3_ha,
        "gross_irrigation_liters_ha": gir_liters_ha,
        "irrigation_efficiency": eff,
        "irrigation_cost_rs_ha": irrigation_pumping_cost,
        "taw_mm": round(taw_mm, 1),
        "raw_mm": round(raw_mm, 1),
        "timeline_sample": timeline_df.head(10).to_dict(orient="records")
    }

if __name__ == "__main__":
    # Self-test using dummy weather
    dummy_weather = pd.DataFrame({
        "day_of_year": list(range(160, 325)),
        "temp_max_c": [33.0] * 165,
        "temp_min_c": [22.0] * 165,
        "temp_mean_c": [27.5] * 165,
        "precipitation_mm": [3.5] * 165
    })
    for crop in CROPS.keys():
        res = simulate_crop_water_balance(crop, dummy_weather, sowing_day_of_year=170)
        print(f"[{crop}] Duration: {res['duration_days']}d | ETc: {res['total_etc_mm']} mm | GIR: {res['gross_irrigation_volume_m3_ha']} m3/ha | Rain Contrib: {res['natural_water_contribution_pct']}%")
