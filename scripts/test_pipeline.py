"""
JalSaarthi - End-to-End Pipeline Verification Test Suite
Runs automated sanity checks on:
1. Crop & Soil Database
2. FAO-56 Water Calculation Engine
3. IMD-aligned Climate Risk Engine
4. ML Yield Prediction Model
5. Multi-Objective Optimizer & Resilience-Return Index (RRI)
6. Sourced Mandi Price Integration & Confidence Ranges
7. Multi-Season Systems Crop Rotation Engine
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.crop_database import (
    CROPS, SOIL_PROFILES, IRRIGATION_COSTS, get_mandi_price, MANDI_DF,
    PUMP_SPECS, DISTRICT_REGIONAL_BASELINES, calculate_irrigation_volume
)
from engine.water_engine import (
    calculate_extraterrestrial_radiation,
    calculate_et0_hargreaves,
    get_crop_kc,
    simulate_crop_water_balance
)
from engine.climate_risk import analyze_climate_risk
from engine.yield_model import predict_yield, get_model
from engine.optimizer import optimize_farming_strategy, evaluate_annual_rotation, get_historical_weather
import pandas as pd
import numpy as np

class TestJalSaarthiPipeline(unittest.TestCase):
    
    def test_01_crop_database(self):
        """Verify all 5 anchor crops have required agronomic, financial, and bilingual parameters."""
        expected_crops = ["Cotton", "Soybean", "Maize", "Gram", "Jowar"]
        for c in expected_crops:
            self.assertIn(c, CROPS, f"Missing crop: {c}")
            crop_data = CROPS[c]
            self.assertIn("duration_days", crop_data)
            self.assertIn("kc", crop_data)
            self.assertIn("base_cost_per_ha", crop_data)
            self.assertIn("name_mr", crop_data)
            self.assertIn("name_hi", crop_data)
            self.assertIn("rotation_type", crop_data)
            self.assertGreater(crop_data["base_cost_per_ha"], 5000)
            
    def test_02_water_engine_et0_and_kc(self):
        """Verify FAO-56 radiation, ET0, and crop coefficient dynamics."""
        ra = calculate_extraterrestrial_radiation(17.66, 182)
        self.assertGreater(ra, 25.0, "Ra should be ~35-40 MJ/m2/day in tropical summer")
        
        et0 = calculate_et0_hargreaves(t_max=34.0, t_min=22.0, t_mean=28.0, latitude_deg=17.66, day_of_year=182)
        self.assertTrue(3.0 <= et0 <= 8.0, f"ET0 value {et0} is outside expected range")
        
        kc_ini = get_crop_kc("Cotton", 10)
        kc_mid = get_crop_kc("Cotton", 100)
        kc_end = get_crop_kc("Cotton", 160)
        self.assertAlmostEqual(kc_ini, 0.35, places=2)
        self.assertAlmostEqual(kc_mid, 1.15, places=2)
        self.assertAlmostEqual(kc_end, 0.65, delta=0.1)

    def test_03_climate_risk_engine(self):
        """Verify rainfall deficit and dry spell scoring."""
        weather_records = []
        for d in range(1, 121):
            rain = 0.0 if (30 <= d <= 52) else 8.0
            weather_records.append({
                "day_of_year": 170 + d,
                "precipitation_mm": rain,
                "temp_max_c": 33.0,
                "temp_min_c": 23.0
            })
        df_sim = pd.DataFrame(weather_records)
        
        risk = analyze_climate_risk("Maize", df_sim, location_key="solapur")
        self.assertEqual(risk["max_consecutive_dry_days"], 23)
        self.assertTrue(0.0 <= risk["composite_risk_score"] <= 100.0)

    def test_04_ml_yield_model_and_confidence_intervals(self):
        """Verify ML model inference and statistical confidence ranges."""
        pred = predict_yield(
            crop="Soybean",
            location="solapur",
            soil_type="Medium Black (Vertisol)",
            rainfall_tot_mm=620.0,
            effective_rain_mm=450.0,
            etc_mm=510.0,
            irrigation_supply_ratio=1.0,
            soil_awc_mm=180.0,
            max_dry_spell_days=8,
            extreme_heat_days=2,
            mean_temp_c=27.5,
            gdd=1850.0
        )
        self.assertGreater(pred["predicted_yield_kg_ha"], 1000.0)
        self.assertLess(pred["predicted_yield_kg_ha"], 3000.0)
        # Check lower <= predicted <= upper
        self.assertLessEqual(pred["yield_lower_kg_ha"], pred["predicted_yield_kg_ha"])
        self.assertGreaterEqual(pred["yield_upper_kg_ha"], pred["predicted_yield_kg_ha"])
        self.assertIn("range_display_kg_ha", pred)

    def test_05_optimizer_and_whatif_scenario(self):
        """Verify master optimizer and responsive scenario adaptation."""
        normal_plan = optimize_farming_strategy(
            farm_size_acres=2.5,
            available_budget_rs=50000,
            available_water_m3=4500,
            location="solapur"
        )
        self.assertEqual(len(normal_plan["all_ranked_options"]), 5)
        top_normal = normal_plan["top_recommendation"]
        self.assertIn("resilience_return_index", top_normal)
        self.assertIn("why_this_crop_won", normal_plan)
        
        # Severe Drought Scenario (-35% rainfall, -40% available water)
        drought_plan = optimize_farming_strategy(
            farm_size_acres=2.5,
            available_budget_rs=50000,
            available_water_m3=4500,
            location="solapur",
            rainfall_shift_pct=-35.0,
            water_shift_pct=-40.0
        )
        top_drought = drought_plan["top_recommendation"]
        self.assertTrue(
            top_drought["crop"] in ["Gram", "Jowar", "Soybean"],
            f"Under severe drought, top crop should be drought-hardy, got {top_drought['crop']}"
        )

    def test_06_mandi_prices_integration(self):
        """Verify Agmarknet APMC mandi prices lookup."""
        mandi_data = get_mandi_price("Cotton", district="solapur")
        self.assertGreater(mandi_data["modal_price"], 6000)
        self.assertIn("Solapur", mandi_data["mandi_name"])
        self.assertIn("Agmarknet", mandi_data["source"])

    def test_07_multi_season_rotation(self):
        """Verify systems-level annual crop rotation evaluation."""
        rot = evaluate_annual_rotation(
            farm_size_acres=2.5,
            available_budget_rs=60000,
            available_water_m3=5000,
            location="solapur"
        )
        self.assertIn("monoculture_cotton", rot)
        self.assertIn("rotation_soybean_gram", rot)
        self.assertIn("systems_verdict", rot)
        self.assertGreater(rot["rotation_soybean_gram"]["water_saved_pct"], 15.0)

    def test_08_crisis_level_infeasibility(self):
        """Verify crisis mode activates honestly when all crops fail constraints."""
        crisis_plan = optimize_farming_strategy(
            farm_size_acres=3.0,
            available_budget_rs=15000,
            available_water_m3=800,
            location="solapur",
            rainfall_shift_pct=-40.0,
            water_shift_pct=-50.0
        )
        self.assertTrue(crisis_plan["crisis_mode"])
        self.assertFalse(crisis_plan["any_viable"])
        self.assertIn("CRITICAL", crisis_plan["why_this_crop_won"])
        self.assertIn("emergency_mitigation", crisis_plan)
        emit = crisis_plan["emergency_mitigation"]
        self.assertTrue(emit["crisis_mode"])
        self.assertLess(emit["safe_cultivable_acres"], 3.0)
        self.assertGreater(emit["reduction_pct"], 0.0)

    def test_09_pump_capacity_and_regional_baselines(self):
        """Verify farmer pump horsepower calculations and district presets."""
        # 1. PUMP_SPECS verification
        self.assertIn(5.0, PUMP_SPECS)
        self.assertEqual(PUMP_SPECS[5.0]["flow_m3_h"], 25.0)
        self.assertIn(3.0, PUMP_SPECS)
        self.assertIn(7.5, PUMP_SPECS)
        self.assertIn(10.0, PUMP_SPECS)

        # 2. Solapur baseline calculation (5 HP, 5h/day, 32 days = 4000 m3 = 40.0 Lakh L)
        vol_solapur = calculate_irrigation_volume(pump_hp=5.0, daily_hours=5.0, pumping_days=32)
        self.assertEqual(vol_solapur["total_water_m3"], 4000.0)
        self.assertEqual(vol_solapur["lakh_liters"], 40.0)
        self.assertEqual(vol_solapur["total_pump_hours"], 160.0)

        # 3. Pune baseline calculation (5 HP, 6h/day, 45 days = 6750 m3 = 67.5 Lakh L)
        vol_pune = calculate_irrigation_volume(pump_hp=5.0, daily_hours=6.0, pumping_days=45)
        self.assertEqual(vol_pune["total_water_m3"], 6750.0)
        self.assertEqual(vol_pune["lakh_liters"], 67.5)
        self.assertEqual(vol_pune["total_pump_hours"], 270.0)

        # 4. District presets presence
        self.assertIn("solapur", DISTRICT_REGIONAL_BASELINES)
        self.assertIn("pune", DISTRICT_REGIONAL_BASELINES)
        s_preset = DISTRICT_REGIONAL_BASELINES["solapur"]
        self.assertEqual(s_preset["farm_size_acres"], 2.5)
        self.assertEqual(s_preset["budget_rs"], 50000)
        self.assertEqual(s_preset["default_water_m3"], 4000)

if __name__ == "__main__":
    unittest.main(verbosity=2)

