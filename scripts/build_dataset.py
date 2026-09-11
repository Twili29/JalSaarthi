"""
JalSaarthi - Dataset Builder for Yield Prediction ML Model
Combines:
1. Historical daily NASA POWER weather data (Solapur & Pune, 2014-2023)
2. Soil moisture retention parameters (Vertisols / Loams)
3. Irrigation availability scenarios (Rainfed, Deficit, Fully Irrigated)
4. Agronomic yield response curves calibrated to Directorate of Economics & Statistics (DES) Maharashtra benchmarks.
Generates: data/processed/crop_yield_modeling_data.csv
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
from engine.crop_database import CROPS, SOIL_PROFILES
from engine.water_engine import simulate_crop_water_balance

# FAO-33 Yield response factor Ky: (1 - Ya/Ym) = Ky * (1 - ETa/ETc)
KY_FACTORS = {
    "Cotton": 0.85,
    "Maize": 1.25,     # Highly sensitive to water deficit
    "Soybean": 0.85,
    "Gram": 0.90,
    "Jowar": 0.70      # Tolerant to water deficit
}

def build_modeling_dataset():
    raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    processed_dir = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    locations = ["solapur", "pune"]
    records = []
    
    for loc in locations:
        weather_file = os.path.join(raw_dir, f"weather_daily_{loc}.csv")
        if not os.path.exists(weather_file):
            print(f"Weather file {weather_file} not found. Skipping {loc}.")
            continue
            
        df_weather = pd.read_csv(weather_file)
        years = sorted(df_weather["year"].unique())
        
        for yr in years:
            yr_weather = df_weather[df_weather["year"] == yr].copy().reset_index(drop=True)
            
            for crop_name, crop_info in CROPS.items():
                sowing_doy = 170 if crop_info["season"] == "Kharif" else 285 # ~June 19 or ~Oct 12
                
                for soil_name, soil_info in SOIL_PROFILES.items():
                    # Simulate seasonal water balance
                    wb = simulate_crop_water_balance(
                        crop_name=crop_name,
                        daily_weather_df=yr_weather,
                        sowing_day_of_year=sowing_doy,
                        latitude_deg=17.66 if loc == "solapur" else 18.52,
                        soil_type=soil_name
                    )
                    
                    # Extract seasonal climate features
                    duration = crop_info["duration_days"]
                    season_slice = yr_weather.iloc[:duration] # approx window
                    
                    rain_tot = wb["total_rainfall_mm"]
                    rain_eff = wb["total_effective_rainfall_mm"]
                    etc_tot = wb["total_etc_mm"]
                    gir_req_m3 = wb["gross_irrigation_volume_m3_ha"]
                    
                    # Dry spell calculation
                    rain_arr = season_slice["precipitation_mm"].values
                    dry_streak = 0
                    max_dry_spell = 0
                    for r in rain_arr:
                        if r < 2.5:
                            dry_streak += 1
                            max_dry_spell = max(max_dry_spell, dry_streak)
                        else:
                            dry_streak = 0
                            
                    heat_days = int(np.sum(season_slice["temp_max_c"].values > 38.0))
                    mean_temp = round(season_slice["temp_mean_c"].mean(), 2)
                    mean_solar = round(season_slice["solar_rad_mj_m2"].mean(), 2)
                    
                    # Growing Degree Days (Base temp 10 C)
                    gdd = round(np.sum(np.maximum(0, season_slice["temp_mean_c"].values - 10.0)), 1)
                    
                    # Generate 3 distinct irrigation scenarios for each year/crop/soil:
                    # 1. Rainfed (0% irrigation supplied)
                    # 2. Deficit irrigation (50% irrigation supplied)
                    # 3. Full irrigation (100% irrigation supplied)
                    for irrig_supply_ratio in [0.0, 0.50, 1.0]:
                        water_supplied = rain_eff + (wb["net_irrigation_requirement_mm"] * irrig_supply_ratio)
                        water_deficit_ratio = max(0.0, 1.0 - (water_supplied / max(1.0, etc_tot)))
                        
                        # Apply FAO-33 water-yield response
                        ky = KY_FACTORS.get(crop_name, 0.90)
                        yield_reduction_ratio = min(0.75, ky * water_deficit_ratio)
                        
                        # Add heat stress penalty if extreme heat days > 6
                        heat_penalty = 0.0
                        if heat_days > 6 and crop_name in ["Maize", "Cotton"]:
                            heat_penalty = min(0.20, (heat_days - 6) * 0.02)
                            
                        # Add soil benefit factor
                        soil_bonus = 0.05 if "Deep" in soil_name else (-0.05 if "Light" in soil_name else 0.0)
                        
                        # Max genetic potential yield for region (DES top percentile)
                        y_max_q = crop_info["yield_range_q_ha"][1]
                        
                        # Actual realized yield in quintals/ha
                        net_yield_ratio = max(0.25, 1.0 - yield_reduction_ratio - heat_penalty + soil_bonus)
                        noise = np.random.normal(0.0, 0.04) # Natural farm variability
                        actual_yield_q = round(y_max_q * np.clip(net_yield_ratio + noise, 0.20, 1.05), 2)
                        actual_yield_kg = round(actual_yield_q * 100.0, 1)
                        
                        records.append({
                            "year": yr,
                            "location": loc,
                            "crop": crop_name,
                            "season": crop_info["season"],
                            "soil_type": soil_name,
                            "soil_awc_mm": soil_info["available_water_capacity_mm_per_m"],
                            "duration_days": duration,
                            "rainfall_tot_mm": round(rain_tot, 1),
                            "effective_rain_mm": round(rain_eff, 1),
                            "etc_mm": round(etc_tot, 1),
                            "irrigation_supply_ratio": irrig_supply_ratio,
                            "water_deficit_ratio": round(water_deficit_ratio, 3),
                            "irrigation_applied_m3_ha": round(gir_req_m3 * irrig_supply_ratio, 1),
                            "max_dry_spell_days": max_dry_spell,
                            "extreme_heat_days": heat_days,
                            "mean_temp_c": mean_temp,
                            "mean_solar_rad_mj": mean_solar,
                            "gdd": gdd,
                            "yield_quintal_ha": actual_yield_q,
                            "yield_kg_ha": actual_yield_kg
                        })
                        
    df_out = pd.DataFrame(records)
    out_file = os.path.join(processed_dir, "crop_yield_modeling_data.csv")
    df_out.to_csv(out_file, index=False)
    print(f"Successfully generated modeling dataset with {len(df_out)} agronomic samples.")
    print(df_out.groupby("crop")[["yield_quintal_ha", "yield_kg_ha"]].mean())
    return df_out

if __name__ == "__main__":
    build_modeling_dataset()
