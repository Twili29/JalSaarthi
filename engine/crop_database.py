"""
JalSaarthi - Crop Agronomic, Economic & Multi-Season Reference Database
Anchored for Maharashtra Semi-Arid Region (Solapur / Pune / Ahmednagar)
Data Sources:
- FAO-56 Irrigation and Drainage Paper (Crop coefficients Kc, growth stages)
- Directorate of Economics & Statistics (DES) / CACP Cost of Cultivation reports
- Minimum Support Price (MSP) & Agmarknet APMC mandi price snapshots
"""

import os
import pandas as pd

# Load Agmarknet APMC Mandi Price Snapshot if available
MANDI_CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "mandi_prices_maharashtra.csv")

def load_mandi_prices():
    if os.path.exists(MANDI_CSV_PATH):
        try:
            return pd.read_csv(MANDI_CSV_PATH)
        except Exception:
            return None
    return None

MANDI_DF = load_mandi_prices()

def get_mandi_price(crop_name: str, district: str = "solapur") -> dict:
    """Fetches realistic APMC mandi modal price for crop in district with MSP fallback."""
    if MANDI_DF is not None and not MANDI_DF.empty:
        match = MANDI_DF[(MANDI_DF["crop"].str.lower() == crop_name.lower()) & 
                         (MANDI_DF["district"].str.lower() == district.lower())]
        if not match.empty:
            row = match.iloc[0]
            return {
                "modal_price": float(row["modal_price_rs_q"]),
                "min_price": float(row["min_price_rs_q"]),
                "max_price": float(row["max_price_rs_q"]),
                "msp": float(row["msp_rs_q"]),
                "mandi_name": str(row["mandi_name"]),
                "as_of_date": str(row["as_of_date"]),
                "source": str(row["source"])
            }
    # Fallback to default MSP
    base_msp = CROPS.get(crop_name, {}).get("market_price_per_quintal", 5000.0)
    return {
        "modal_price": base_msp,
        "min_price": base_msp * 0.92,
        "max_price": base_msp * 1.08,
        "msp": base_msp,
        "mandi_name": f"{district.title()} APMC Benchmark",
        "as_of_date": "2026-09-08",
        "source": "CACP / MSP 2025-26"
    }

CROPS = {
    "Cotton": {
        "name_mr": "कापूस (Cotton)",
        "name_hi": "कपास (Cotton)",
        "scientific_name": "Gossypium hirsutum",
        "category": "Cash Crop / Fiber",
        "season": "Kharif",
        "duration_days": 165,
        "stages_days": {
            "initial": 30,
            "development": 50,
            "mid": 55,
            "late": 30
        },
        "kc": {
            "initial": 0.35,
            "mid": 1.15,
            "end": 0.65
        },
        "critical_growth_stages": ["Square formation", "Flowering", "Boll development"],
        "depletion_factor_p": 0.65,  # Soil moisture depletion factor before stress
        "rooting_depth_m": 1.2,
        "base_cost_per_ha": 38000.0,  # ₹/ha (Seed, BT technology, fertilizer, labor, tilling)
        "market_price_per_quintal": 7020.0,  # ₹/q (2023-24 MSP Long Staple)
        "benchmark_yield_q_ha": 20.0,  # 20 q/ha = 2000 kg/ha average
        "yield_range_q_ha": (12.0, 28.0),
        "climate_sensitivity": "High",
        "drought_tolerance": "Moderate-Low",
        "rotation_type": "Long-Cycle Cash Monoculture",
        "nitrogen_fixation_kg_ha": 0.0,
        "soil_nutrient_impact": "High Depletion (Heavy consumer of N-P-K)",
        "description": "High revenue potential but water-intensive and sensitive to dry spells during boll development."
    },
    "Soybean": {
        "name_mr": "सोयाबीन (Soybean)",
        "name_hi": "सोयाबीन (Soybean)",
        "scientific_name": "Glycine max",
        "category": "Oilseed / Legume",
        "season": "Kharif",
        "duration_days": 105,
        "stages_days": {
            "initial": 20,
            "development": 30,
            "mid": 40,
            "late": 15
        },
        "kc": {
            "initial": 0.40,
            "mid": 1.15,
            "end": 0.50
        },
        "critical_growth_stages": ["Flowering", "Pod initiation", "Pod filling"],
        "depletion_factor_p": 0.50,
        "rooting_depth_m": 0.9,
        "base_cost_per_ha": 22000.0,
        "market_price_per_quintal": 4600.0,  # ₹/q MSP benchmark
        "benchmark_yield_q_ha": 18.0,  # 1800 kg/ha
        "yield_range_q_ha": (12.0, 24.0),
        "climate_sensitivity": "Moderate",
        "drought_tolerance": "Moderate",
        "rotation_type": "Short-Cycle Kharif Legume",
        "nitrogen_fixation_kg_ha": 45.0,  # Fixes ~40-50 kg atmospheric N per ha
        "soil_nutrient_impact": "Restorative (Adds organic matter & biological N)",
        "description": "Short duration, reliable Kharif oilseed with nitrogen-fixing properties and liquid market demand."
    },
    "Maize": {
        "name_mr": "मका (Maize)",
        "name_hi": "मक्का (Maize)",
        "scientific_name": "Zea mays",
        "category": "Cereal / Feed",
        "season": "Kharif",
        "duration_days": 110,
        "stages_days": {
            "initial": 20,
            "development": 35,
            "mid": 40,
            "late": 15
        },
        "kc": {
            "initial": 0.30,
            "mid": 1.20,
            "end": 0.45
        },
        "critical_growth_stages": ["Tasseling", "Silking", "Grain filling"],
        "depletion_factor_p": 0.55,
        "rooting_depth_m": 1.0,
        "base_cost_per_ha": 24000.0,
        "market_price_per_quintal": 2090.0,  # ₹/q MSP
        "benchmark_yield_q_ha": 40.0,  # 4000 kg/ha
        "yield_range_q_ha": (25.0, 55.0),
        "climate_sensitivity": "Moderate-High",
        "drought_tolerance": "Moderate",
        "rotation_type": "Kharif Cereal Workhorse",
        "nitrogen_fixation_kg_ha": 0.0,
        "soil_nutrient_impact": "Moderate Depletion",
        "description": "High biomass and harvest yield; highly sensitive to water stress at the critical silking stage."
    },
    "Gram": {
        "name_mr": "हरभरा / चना (Gram / Chickpea)",
        "name_hi": "चना (Gram / Chickpea)",
        "scientific_name": "Cicer arietinum (Chickpea / Chana)",
        "category": "Pulse / Legume",
        "season": "Rabi / Late Kharif",
        "duration_days": 100,
        "stages_days": {
            "initial": 20,
            "development": 25,
            "mid": 35,
            "late": 20
        },
        "kc": {
            "initial": 0.40,
            "mid": 1.00,
            "end": 0.35
        },
        "critical_growth_stages": ["Pre-flowering", "Pod development"],
        "depletion_factor_p": 0.60,
        "rooting_depth_m": 1.0,
        "base_cost_per_ha": 16000.0,
        "market_price_per_quintal": 5440.0,  # ₹/q MSP
        "benchmark_yield_q_ha": 15.0,  # 1500 kg/ha
        "yield_range_q_ha": (10.0, 22.0),
        "climate_sensitivity": "Low",
        "drought_tolerance": "High",
        "rotation_type": "Rabi Drought-Resilient Pulse",
        "nitrogen_fixation_kg_ha": 50.0,  # Fixes ~45-60 kg N per ha
        "soil_nutrient_impact": "Restorative (Deep taproot breaks soil pans, enriches N)",
        "description": "Deep taproot system, low water consumption, drought hardy with premium market price."
    },
    "Jowar": {
        "name_mr": "ज्वारी (Jowar / Sorghum)",
        "name_hi": "ज्वार (Jowar / Sorghum)",
        "scientific_name": "Sorghum bicolor",
        "category": "Millet / Coarse Cereal",
        "season": "Kharif / Rabi",
        "duration_days": 105,
        "stages_days": {
            "initial": 20,
            "development": 30,
            "mid": 40,
            "late": 15
        },
        "kc": {
            "initial": 0.30,
            "mid": 1.05,
            "end": 0.55
        },
        "critical_growth_stages": ["Booting", "Flowering"],
        "depletion_factor_p": 0.60,
        "rooting_depth_m": 1.2,
        "base_cost_per_ha": 13000.0,
        "market_price_per_quintal": 3180.0,  # ₹/q MSP
        "benchmark_yield_q_ha": 17.0,  # 1700 kg/ha
        "yield_range_q_ha": (10.0, 26.0),
        "climate_sensitivity": "Very Low",
        "drought_tolerance": "Extremely High",
        "rotation_type": "Climate-Shield Coarse Grain",
        "nitrogen_fixation_kg_ha": 0.0,
        "soil_nutrient_impact": "Low Depletion (High biomass residue)",
        "description": "Excellent C4 photosynthetic efficiency, dormant during dry spells, ultimate climate shield crop."
    }
}

SOIL_PROFILES = {
    "Medium Black (Vertisol)": {
        "name_mr": "मध्यम काळी जमीन (Medium Black)",
        "name_hi": "मध्यम काली मिट्टी (Medium Black)",
        "field_capacity": 0.36,     # m3/m3
        "wilting_point": 0.18,      # m3/m3
        "available_water_capacity_mm_per_m": 180.0,
        "drainage_rate": "Moderate-Low",
        "description": "Common in Western Maharashtra/Solapur; high water-holding capacity, prone to cracking when dry."
    },
    "Deep Black (Heavy Vertisol)": {
        "name_mr": "भारी काळी जमीन (Deep Black)",
        "name_hi": "गहरी काली मिट्टी (Deep Black)",
        "field_capacity": 0.42,
        "wilting_point": 0.22,
        "available_water_capacity_mm_per_m": 200.0,
        "drainage_rate": "Slow",
        "description": "Deep fertile soil with maximum water retention, ideal for moisture conservation."
    },
    "Light Loam (Sandy Loam)": {
        "name_mr": "हलकी ते मध्यम जमीन (Light Loam)",
        "name_hi": "हल्की दोमट मिट्टी (Light Loam)",
        "field_capacity": 0.24,
        "wilting_point": 0.10,
        "available_water_capacity_mm_per_m": 140.0,
        "drainage_rate": "High",
        "description": "Requires frequent light irrigations due to lower water retention."
    }
}

IRRIGATION_COSTS = {
    "flood_furrow": {
        "name_mr": "पाट पाणी / प्रवाही सिंचन (Flood / Furrow)",
        "name_hi": "पारंपरिक बाढ़ सिंचाई (Flood / Furrow)",
        "efficiency": 0.60,       # 60% irrigation efficiency
        "cost_per_m3": 1.20,      # Pumping electricity & labor cost in ₹ per m3
        "capital_cost_per_ha": 0.0
    },
    "drip": {
        "name_mr": "ठिबक सिंचन (Drip Irrigation)",
        "name_hi": "टपक सिंचाई (Drip Irrigation)",
        "efficiency": 0.90,       # 90% irrigation efficiency
        "cost_per_m3": 0.80,      # Less water pumped = lower energy
        "capital_cost_per_ha": 35000.0  # Subsidy-adjusted initial setup cost
    },
    "sprinkler": {
        "name_mr": "तुषार सिंचन (Sprinkler)",
        "name_hi": "फव्वारा सिंचाई (Sprinkler)",
        "efficiency": 0.75,       # 75% irrigation efficiency
        "cost_per_m3": 1.00,
        "capital_cost_per_ha": 18000.0
    }
}

# Agricultural Pumping Standards for Maharashtra Semi-Arid Zone (BIS / MSEDCL / KVK)
PUMP_SPECS = {
    3.0: {
        "hp": 3.0,
        "flow_m3_h": 16.0,
        "label": "3 HP (~16,000 L/h - Small Borewell / Open Well)",
        "lps": 4.4
    },
    5.0: {
        "hp": 5.0,
        "flow_m3_h": 25.0,
        "label": "5 HP (~25,000 L/h - Standard Regional Submersible)",
        "lps": 6.9
    },
    7.5: {
        "hp": 7.5,
        "flow_m3_h": 38.0,
        "label": "7.5 HP (~38,000 L/h - High-Yield Well / Lift Scheme)",
        "lps": 10.5
    },
    10.0: {
        "hp": 10.0,
        "flow_m3_h": 50.0,
        "label": "10 HP (~50,000 L/h - River Lift / Community Scheme)",
        "lps": 13.9
    }
}

# Regional Agro-Climatic Benchmarks & Default Farmer Profiles
DISTRICT_REGIONAL_BASELINES = {
    "solapur": {
        "district": "solapur",
        "label": "Solapur (Semi-Arid Drought Belt)",
        "summary": "Deep Vertisols, 520 mm normal Kharif rain, deep borewell pumping constrained by MSEDCL 5h power shifts.",
        "farm_size_acres": 2.5,
        "budget_rs": 50000,
        "soil_type": "Medium Black (Vertisol)",
        "irrigation_method": "flood_furrow",
        "pump_hp": 5.0,
        "daily_pumping_hours": 5,
        "pumping_days_season": 32,
        "default_water_m3": 4000
    },
    "pune": {
        "district": "pune",
        "label": "Pune (Transition Zone)",
        "summary": "Clay Loam, 720 mm normal Kharif rain, canal/well water support with longer 6h pumping windows.",
        "farm_size_acres": 3.0,
        "budget_rs": 65000,
        "soil_type": "Clay Loam",
        "irrigation_method": "flood_furrow",
        "pump_hp": 5.0,
        "daily_pumping_hours": 6,
        "pumping_days_season": 45,
        "default_water_m3": 6750
    }
}

def calculate_irrigation_volume(pump_hp: float, daily_hours: float, pumping_days: int) -> dict:
    """Calculates seasonal available irrigation water volume from pump capacity and electricity hours."""
    spec = PUMP_SPECS.get(pump_hp, PUMP_SPECS[5.0])
    flow_m3_h = spec["flow_m3_h"]
    total_hours = round(daily_hours * pumping_days, 1)
    total_m3 = round(flow_m3_h * total_hours, 1)
    total_liters = total_m3 * 1000.0
    lakh_liters = round(total_liters / 100000.0, 2)
    return {
        "pump_hp": pump_hp,
        "flow_rate_m3_h": flow_m3_h,
        "daily_hours": daily_hours,
        "pumping_days": pumping_days,
        "total_pump_hours": total_hours,
        "total_water_m3": total_m3,
        "total_water_liters": total_liters,
        "lakh_liters": lakh_liters
    }

