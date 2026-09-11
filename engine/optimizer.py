"""
JalSaarthi - Multi-Objective Optimization Engine
Balances:
1. Economic Return (Net Profit & ROI) - Weight: 45%
2. Water Security (Gross Irrigation Demand vs Available Water) - Weight: 30%
3. Climate Resilience (IMD Deficit, Dry Spell, and Heat Stress) - Weight: 25%
Evaluates single crops and multi-season crop rotation strategies.
"""

import os
import sys

# Configure UTF-8 for Windows PowerShell output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from engine.crop_database import CROPS, SOIL_PROFILES, IRRIGATION_COSTS, get_mandi_price
    from engine.water_engine import simulate_crop_water_balance
    from engine.climate_risk import analyze_climate_risk
    from engine.yield_model import predict_yield
except ImportError:
    from crop_database import CROPS, SOIL_PROFILES, IRRIGATION_COSTS, get_mandi_price
    from water_engine import simulate_crop_water_balance
    from climate_risk import analyze_climate_risk
    from yield_model import predict_yield

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

def get_historical_weather(location: str = "solapur") -> pd.DataFrame:
    """Loads latest representative seasonal weather for location."""
    file_path = os.path.join(RAW_DATA_DIR, f"weather_daily_{location}.csv")
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        df_2023 = df[df["year"] == 2023].copy().reset_index(drop=True)
        if len(df_2023) > 100:
            return df_2023
        return df
    from scripts.fetch_nasa_power import generate_calibrated_weather_baseline
    return generate_calibrated_weather_baseline(17.66, 75.91, 2023, 2023)


def evaluate_crop_strategy(
    crop_name: str,
    farm_size_ha: float,
    available_budget_rs: float,
    available_water_m3: float,
    location: str = "solapur",
    soil_type: str = "Medium Black (Vertisol)",
    irrigation_method: str = "flood_furrow",
    weather_df: Optional[pd.DataFrame] = None,
    rainfall_shift_pct: float = 0.0,
    temp_shift_c: float = 0.0,
    market_price_shift_pct: float = 0.0
) -> Dict[str, Any]:
    """
    Evaluates a single crop strategy under given farm parameters and climate scenario.
    """
    if crop_name not in CROPS:
        raise ValueError(f"Unknown crop: {crop_name}")
    crop = CROPS[crop_name]
    soil = SOIL_PROFILES.get(soil_type, list(SOIL_PROFILES.values())[0])
    irrig = IRRIGATION_COSTS.get(irrigation_method, IRRIGATION_COSTS["flood_furrow"])
    
    if weather_df is None:
        weather_df = get_historical_weather(location)
        
    # Apply rainfall and temperature scenario adjustments
    sim_weather = weather_df.copy()
    rain_mult = max(0.05, 1.0 + (rainfall_shift_pct / 100.0))
    sim_weather["precipitation_mm"] = sim_weather["precipitation_mm"] * rain_mult
    sim_weather["temp_max_c"] = sim_weather["temp_max_c"] + temp_shift_c
    sim_weather["temp_min_c"] = sim_weather["temp_min_c"] + temp_shift_c
    sim_weather["temp_mean_c"] = sim_weather["temp_mean_c"] + temp_shift_c
    
    sowing_doy = 170 if crop["season"] == "Kharif" else 285
    lat = 17.66 if location == "solapur" else 18.52
    
    # 1. Hydrology & Water Balance
    wb = simulate_crop_water_balance(
        crop_name=crop_name,
        daily_weather_df=sim_weather,
        sowing_day_of_year=sowing_doy,
        latitude_deg=lat,
        soil_type=soil_type,
        irrigation_method=irrigation_method
    )
    
    gross_water_req_per_ha_m3 = wb["gross_irrigation_volume_m3_ha"]
    total_gross_water_needed_m3 = round(gross_water_req_per_ha_m3 * farm_size_ha, 1)
    
    if total_gross_water_needed_m3 > 0:
        water_supply_ratio = min(1.0, available_water_m3 / total_gross_water_needed_m3)
    else:
        water_supply_ratio = 1.0
        
    water_deficit_m3 = max(0.0, total_gross_water_needed_m3 - available_water_m3)
    water_feasible = water_deficit_m3 <= 1e-3
    
    # 2. Climate Risk Assessment
    risk_analysis = analyze_climate_risk(
        crop_name=crop_name,
        daily_weather_df=sim_weather,
        location_key=location
    )
    risk_score = risk_analysis["composite_risk_score"]
    
    # 3. Yield Prediction (via ML with Confidence Ranges)
    duration = crop["duration_days"]
    season_weather = sim_weather.iloc[:duration]
    gdd = round(float(np.sum(np.maximum(0, season_weather["temp_mean_c"].values - 10.0))), 1)
    mean_temp = round(float(season_weather["temp_mean_c"].mean()), 1)
    
    yield_pred = predict_yield(
        crop=crop_name,
        location=location,
        soil_type=soil_type,
        rainfall_tot_mm=wb["total_rainfall_mm"],
        effective_rain_mm=wb["total_effective_rainfall_mm"],
        etc_mm=wb["total_etc_mm"],
        irrigation_supply_ratio=water_supply_ratio,
        soil_awc_mm=soil["available_water_capacity_mm_per_m"],
        max_dry_spell_days=risk_analysis["max_consecutive_dry_days"],
        extreme_heat_days=risk_analysis["extreme_heat_days_gt_38c"],
        mean_temp_c=mean_temp,
        gdd=gdd
    )
    
    predicted_yield_kg_ha = yield_pred["predicted_yield_kg_ha"]
    predicted_yield_q_ha = yield_pred["predicted_yield_quintal_ha"]
    total_yield_kg = round(predicted_yield_kg_ha * farm_size_ha, 1)
    total_yield_quintals = round(predicted_yield_q_ha * farm_size_ha, 2)
    
    # Range estimates for total farm harvest
    yield_lower_farm_kg = round(yield_pred["yield_lower_kg_ha"] * farm_size_ha, 1)
    yield_upper_farm_kg = round(yield_pred["yield_upper_kg_ha"] * farm_size_ha, 1)
    yield_lower_farm_q = round(yield_lower_farm_kg / 100.0, 2)
    yield_upper_farm_q = round(yield_upper_farm_kg / 100.0, 2)
    
    # 4. Economics & Mandi Integration
    base_cultivation_cost = round(crop["base_cost_per_ha"] * farm_size_ha, 2)
    actual_water_used_m3 = min(available_water_m3, total_gross_water_needed_m3)
    irrigation_operational_cost = round(actual_water_used_m3 * irrig["cost_per_m3"], 2)
    total_cost_rs = round(base_cultivation_cost + irrigation_operational_cost, 2)
    
    budget_deficit_rs = max(0.0, total_cost_rs - available_budget_rs)
    budget_feasible = budget_deficit_rs <= 1.0
    
    total_crop_demand_m3 = round(wb["total_etc_mm"] * 10.0 * farm_size_ha, 1)
    is_rainfed = (total_gross_water_needed_m3 <= 0.0)
    
    # Sourced Mandi Price (Agmarknet APMC snapshot)
    mandi_info = get_mandi_price(crop_name, district=location)
    base_market_price = mandi_info["modal_price"]
    effective_market_price = round(base_market_price * (1.0 + (market_price_shift_pct / 100.0)), 2)
    
    expected_revenue_rs = round(total_yield_quintals * effective_market_price, 2)
    expected_profit_rs = round(expected_revenue_rs - total_cost_rs, 2)
    
    # Profit confidence range
    revenue_lower_rs = round(yield_lower_farm_q * effective_market_price, 2)
    revenue_upper_rs = round(yield_upper_farm_q * effective_market_price, 2)
    profit_lower_rs = round(revenue_lower_rs - total_cost_rs, 2)
    profit_upper_rs = round(revenue_upper_rs - total_cost_rs, 2)
    
    roi_pct = round((expected_profit_rs / max(1.0, total_cost_rs)) * 100.0, 1)
    water_productivity_rs_m3 = round(expected_profit_rs / max(1.0, actual_water_used_m3), 2)
    
    return {
        "crop": crop_name,
        "name_mr": crop.get("name_mr", crop_name),
        "name_hi": crop.get("name_hi", crop_name),
        "category": crop["category"],
        "rotation_type": crop.get("rotation_type", "Standard"),
        "soil_nutrient_impact": crop.get("soil_nutrient_impact", "Neutral"),
        "nitrogen_fixation_kg_ha": crop.get("nitrogen_fixation_kg_ha", 0.0),
        "farm_size_ha": farm_size_ha,
        "farm_size_acres": round(farm_size_ha * 2.47105, 2),
        "water_metrics": {
            "etc_mm": wb["total_etc_mm"],
            "natural_rain_mm": wb["total_rainfall_mm"],
            "effective_rain_mm": wb["total_effective_rainfall_mm"],
            "natural_contribution_pct": wb["natural_water_contribution_pct"],
            "crop_demand_m3": total_crop_demand_m3,
            "is_rainfed": is_rainfed,
            "water_status_display": "0 m³ (100% Rainfed)" if is_rainfed else f"{total_gross_water_needed_m3:,.0f} m³",
            "water_required_m3": total_gross_water_needed_m3,
            "water_used_m3": round(actual_water_used_m3, 1),
            "water_deficit_m3": round(water_deficit_m3, 1),
            "water_feasible": water_feasible,
            "water_supply_ratio": round(water_supply_ratio, 2)
        },
        "climate_metrics": {
            "risk_score": risk_score,
            "risk_level": risk_analysis["risk_level"],
            "max_dry_spell_days": risk_analysis["max_consecutive_dry_days"],
            "max_consecutive_dry_days": risk_analysis["max_consecutive_dry_days"],
            "extreme_heat_days": risk_analysis["extreme_heat_days_gt_38c"],
            "imd_category": risk_analysis["imd_rainfall_category"]
        },
        "yield_metrics": {
            "yield_kg_ha": predicted_yield_kg_ha,
            "yield_q_ha": predicted_yield_q_ha,
            "total_yield_kg": total_yield_kg,
            "total_yield_quintals": total_yield_quintals,
            "yield_lower_farm_kg": yield_lower_farm_kg,
            "yield_upper_farm_kg": yield_upper_farm_kg,
            "yield_lower_farm_q": yield_lower_farm_q,
            "yield_upper_farm_q": yield_upper_farm_q,
            "range_display_kg": f"{yield_lower_farm_kg:,.0f} – {yield_upper_farm_kg:,.0f} kg",
            "range_display_q": f"{yield_lower_farm_q:.1f} – {yield_upper_farm_q:.1f} q"
        },
        "financial_metrics": {
            "base_cost_rs": base_cultivation_cost,
            "irrigation_cost_rs": irrigation_operational_cost,
            "total_investment_rs": total_cost_rs,
            "available_budget_rs": available_budget_rs,
            "budget_deficit_rs": round(budget_deficit_rs, 2),
            "budget_feasible": budget_feasible,
            "market_price_per_q": effective_market_price,
            "mandi_modal_price_q": mandi_info["modal_price"],
            "mandi_name": mandi_info["mandi_name"],
            "mandi_as_of_date": mandi_info["as_of_date"],
            "mandi_source": mandi_info["source"],
            "expected_revenue_rs": expected_revenue_rs,
            "expected_profit_rs": expected_profit_rs,
            "profit_lower_rs": profit_lower_rs,
            "profit_upper_rs": profit_upper_rs,
            "range_display_profit_rs": f"₹{profit_lower_rs:,.0f} – ₹{profit_upper_rs:,.0f}",
            "roi_pct": roi_pct,
            "water_productivity_rs_m3": water_productivity_rs_m3
        }
    }


def optimize_farming_strategy(
    farm_size_acres: float = 2.5,
    available_budget_rs: float = 50000.0,
    available_water_m3: float = 3500.0,
    location: str = "solapur",
    soil_type: str = "Medium Black (Vertisol)",
    irrigation_method: str = "flood_furrow",
    rainfall_shift_pct: float = 0.0,
    temp_shift_c: float = 0.0,
    market_price_shift_pct: float = 0.0,
    water_shift_pct: float = 0.0,
    budget_shift_rs: float = 0.0
) -> Dict[str, Any]:
    """
    Master optimization function:
    Compares all crops under active constraints and scenario variations,
    calculates JalSaarthi Resilience-Return Index (RRI), and ranks the optimal plan.
    """
    farm_size_ha = farm_size_acres / 2.47105
    adj_budget_rs = max(5000.0, available_budget_rs + budget_shift_rs)
    adj_water_m3 = max(100.0, available_water_m3 * (1.0 + (water_shift_pct / 100.0)))
    
    weather_df = get_historical_weather(location)
    
    evaluations = []
    for crop_name in CROPS.keys():
        eval_res = evaluate_crop_strategy(
            crop_name=crop_name,
            farm_size_ha=farm_size_ha,
            available_budget_rs=adj_budget_rs,
            available_water_m3=adj_water_m3,
            location=location,
            soil_type=soil_type,
            irrigation_method=irrigation_method,
            weather_df=weather_df,
            rainfall_shift_pct=rainfall_shift_pct,
            temp_shift_c=temp_shift_c,
            market_price_shift_pct=market_price_shift_pct
        )
        evaluations.append(eval_res)
        
    # Multi-Objective Scoring: 45% Profit, 30% Water Security, 25% Climate Resilience
    profits = [e["financial_metrics"]["expected_profit_rs"] for e in evaluations]
    max_profit = max(profits) if max(profits) > 0 else 1.0
    min_profit = min(profits)
    
    scored_plans = []
    for e in evaluations:
        fin = e["financial_metrics"]
        wat = e["water_metrics"]
        clim = e["climate_metrics"]
        
        # 1. Normalized Profit [0, 1]
        profit_norm = (fin["expected_profit_rs"] - min_profit) / max(1.0, (max_profit - min_profit))
        profit_score_pts = 0.45 * profit_norm * 100.0
        
        # 2. Water Conservation [0, 1]
        if wat["water_required_m3"] > 0:
            water_conserved_ratio = max(0.0, (adj_water_m3 - wat["water_used_m3"]) / adj_water_m3)
        else:
            water_conserved_ratio = 1.0
        water_score_pts = 0.30 * water_conserved_ratio * 100.0
            
        # 3. Climate Safety [0, 1]
        climate_safety = max(0.0, (100.0 - clim["risk_score"]) / 100.0)
        climate_score_pts = 0.25 * climate_safety * 100.0
        
        # Base RRI Score
        base_rri = profit_score_pts + water_score_pts + climate_score_pts
        
        # Infeasibility Penalties
        penalty = 0.0
        reasons = []
        if not fin["budget_feasible"]:
            deficit = fin["total_investment_rs"] - adj_budget_rs
            penalty += 35.0
            reasons.append(f"Budget deficit of ₹{deficit:,.0f}")
        if not wat["water_feasible"]:
            deficit_m3 = wat["water_deficit_m3"]
            penalty += 40.0
            reasons.append(f"Water shortage of {deficit_m3:,.0f} m³ ({round(deficit_m3*1000):,.0f} L)")
            
        final_score = max(5.0, round(base_rri - penalty, 1))
        is_viable = fin["budget_feasible"] and wat["water_feasible"]
        
        scored_plans.append({
            **e,
            "resilience_return_index": final_score,
            "jalsaarthi_score": final_score,  # Backwards compatibility alias
            "score_breakdown": {
                "profit_points": round(profit_score_pts, 1),
                "water_points": round(water_score_pts, 1),
                "climate_points": round(climate_score_pts, 1),
                "penalty_points": round(penalty, 1),
                "weights_display": "45% Net Profit + 30% Water Conservation + 25% Climate Resilience"
            },
            "is_viable": is_viable,
            "feasibility_warnings": reasons,
            "water_conserved_pct": round(water_conserved_ratio * 100.0, 1)
        })
        
    scored_plans.sort(key=lambda x: x["resilience_return_index"], reverse=True)
    top_recommendation = scored_plans[0]
    
    # Check overall feasibility across all options
    any_viable = any(p["is_viable"] for p in scored_plans)
    crisis_mode = not any_viable
    
    top_crop = top_recommendation["crop"]
    runner_up = scored_plans[1] if len(scored_plans) > 1 else None
    
    # Calculate emergency mitigation metrics if in crisis mode
    if crisis_mode:
        top_wat = top_recommendation["water_metrics"]
        top_fin = top_recommendation["financial_metrics"]
        
        water_ratio = adj_water_m3 / max(1.0, top_wat["water_required_m3"])
        budget_ratio = adj_budget_rs / max(1.0, top_fin["total_investment_rs"])
        limiting_ratio = min(water_ratio, budget_ratio)
        
        safe_acreage = max(0.2, round(farm_size_acres * limiting_ratio, 1))
        safe_acreage = min(safe_acreage, farm_size_acres)
        area_reduction_pct = round((1.0 - safe_acreage / farm_size_acres) * 100.0, 1)
        
        # Drip micro-irrigation saving (~33% reduction compared to flood/furrow)
        drip_saving_m3 = round(top_wat["water_required_m3"] * 0.33, 1) if irrigation_method != "drip" else 0.0
        
        deficit_items = top_recommendation["feasibility_warnings"]
        deficit_summary = "; ".join(deficit_items) if deficit_items else "Resource limits exceeded"
        
        why_won = (
            f"🚨 CRITICAL RESOURCE DEFICIT: Under current extreme stress conditions, NO crop can be safely cultivated across your full {farm_size_acres} acres. "
            f"{top_crop} is identified strictly as the LEAST-DAMAGE CONTINGENCY (RRI {top_recommendation['resilience_return_index']}/100) because it minimizes catastrophic loss ({deficit_summary}). "
            f"DO NOT plant your full land: downscale sowing to {safe_acreage} Acres or convert to micro-irrigation to avert severe crop desiccation."
        )
        
        emergency_mitigation = {
            "crisis_mode": True,
            "limiting_factor": "Water" if water_ratio < budget_ratio else "Budget",
            "safe_cultivable_acres": safe_acreage,
            "reduction_pct": area_reduction_pct,
            "unviable_acres": round(farm_size_acres - safe_acreage, 1),
            "drip_water_saved_m3": drip_saving_m3,
            "recommended_action": f"Downscale {top_crop} to {safe_acreage} Acres to match available {adj_water_m3:,.0f} m³ water."
        }
    else:
        emergency_mitigation = {
            "crisis_mode": False,
            "limiting_factor": "None",
            "safe_cultivable_acres": farm_size_acres,
            "reduction_pct": 0.0,
            "unviable_acres": 0.0,
            "drip_water_saved_m3": 0.0,
            "recommended_action": f"Full {farm_size_acres} acres viable for {top_crop}."
        }
        
        # Standard "Why this crop won" explanation
        cotton_eval = next((p for p in scored_plans if p["crop"] == "Cotton"), None)
        if cotton_eval and not cotton_eval["is_viable"] and top_crop != "Cotton":
            why_won = (
                f"{top_crop} won because it delivers optimal financial return ({top_recommendation['financial_metrics']['range_display_profit_rs']}) "
                f"within your exact water ceiling. While Cotton appears lucrative in raw price, it suffers a severe {cotton_eval['water_metrics']['water_deficit_m3']:,.0f} m³ "
                f"water deficit and high climate risk under your current constraints."
            )
        elif runner_up:
            diff_water = runner_up["water_metrics"]["water_required_m3"] - top_recommendation["water_metrics"]["water_required_m3"]
            water_saved_str = f"saves {diff_water:,.0f} m³ water compared to {runner_up['crop']}" if diff_water > 0 else f"maximizes net profit while remaining 100% water-viable"
            why_won = (
                f"{top_crop} achieved the highest Resilience-Return Index ({top_recommendation['resilience_return_index']}/100) because it "
                f"{water_saved_str} with {top_recommendation['climate_metrics']['risk_level'].lower()} climate vulnerability."
            )
        else:
            why_won = f"{top_crop} provides the best trade-off between net profit and water conservation."

    return {
        "context": {
            "farm_size_acres": farm_size_acres,
            "farm_size_ha": round(farm_size_ha, 2),
            "effective_budget_rs": adj_budget_rs,
            "effective_water_m3": round(adj_water_m3, 1),
            "location": location,
            "soil_type": soil_type,
            "irrigation_method": irrigation_method,
            "scenario": {
                "rainfall_shift_pct": rainfall_shift_pct,
                "water_shift_pct": water_shift_pct,
                "budget_shift_rs": budget_shift_rs,
                "temp_shift_c": temp_shift_c,
                "market_price_shift_pct": market_price_shift_pct
            }
        },
        "top_recommendation": top_recommendation,
        "why_this_crop_won": why_won,
        "all_ranked_options": scored_plans,
        "crisis_mode": crisis_mode,
        "any_viable": any_viable,
        "emergency_mitigation": emergency_mitigation
    }


def evaluate_annual_rotation(
    farm_size_acres: float = 2.5,
    available_budget_rs: float = 60000.0,
    available_water_m3: float = 5000.0,
    location: str = "solapur",
    soil_type: str = "Medium Black (Vertisol)",
    irrigation_method: str = "flood_furrow",
    rainfall_shift_pct: float = 0.0,
    temp_shift_c: float = 0.0,
    water_shift_pct: float = 0.0,
    budget_shift_rs: float = 0.0
) -> Dict[str, Any]:
    """
    Systems-level multi-season analysis:
    Compares:
    Option A: Monoculture Long-Season Cotton (165 days) -> Fallow (Single decision)
    Option B: Climate-Smart Crop Rotation: Kharif Soybean (105 days) + Rabi Gram (100 days)
    """
    farm_size_ha = farm_size_acres / 2.47105
    adj_budget_rs = max(5000.0, available_budget_rs + budget_shift_rs)
    adj_water_m3 = max(100.0, available_water_m3 * (1.0 + (water_shift_pct / 100.0)))
    
    # 1. Evaluate Cotton (Monoculture)
    cotton_eval = evaluate_crop_strategy(
        crop_name="Cotton",
        farm_size_ha=farm_size_ha,
        available_budget_rs=adj_budget_rs,
        available_water_m3=adj_water_m3,
        location=location,
        soil_type=soil_type,
        irrigation_method=irrigation_method,
        rainfall_shift_pct=rainfall_shift_pct,
        temp_shift_c=temp_shift_c
    )
    
    # 2. Evaluate Kharif Soybean
    soybean_eval = evaluate_crop_strategy(
        crop_name="Soybean",
        farm_size_ha=farm_size_ha,
        available_budget_rs=adj_budget_rs * 0.55,
        available_water_m3=adj_water_m3 * 0.55,
        location=location,
        soil_type=soil_type,
        irrigation_method=irrigation_method,
        rainfall_shift_pct=rainfall_shift_pct,
        temp_shift_c=temp_shift_c
    )
    
    # 3. Evaluate Rabi Gram
    gram_eval = evaluate_crop_strategy(
        crop_name="Gram",
        farm_size_ha=farm_size_ha,
        available_budget_rs=adj_budget_rs * 0.45,
        available_water_m3=adj_water_m3 * 0.45,
        location=location,
        soil_type=soil_type,
        irrigation_method=irrigation_method,
        rainfall_shift_pct=rainfall_shift_pct,
        temp_shift_c=temp_shift_c
    )
    
    # Combined Multi-Season Stats (Balanced 50-50 seasonal staggered allocation across the year)
    # Staggers water demand between monsoon (Kharif) and winter (Rabi)
    rot_water_total = round((soybean_eval["water_metrics"]["water_required_m3"] + gram_eval["water_metrics"]["water_required_m3"]) * 0.5, 1)
    rot_cost_total = round((soybean_eval["financial_metrics"]["total_investment_rs"] + gram_eval["financial_metrics"]["total_investment_rs"]) * 0.5, 2)
    rot_profit_total = round((soybean_eval["financial_metrics"]["expected_profit_rs"] + gram_eval["financial_metrics"]["expected_profit_rs"]) * 0.5, 2)
    
    rot_profit_lower = round((soybean_eval["financial_metrics"]["profit_lower_rs"] + gram_eval["financial_metrics"]["profit_lower_rs"]) * 0.5, 2)
    rot_profit_upper = round((soybean_eval["financial_metrics"]["profit_upper_rs"] + gram_eval["financial_metrics"]["profit_upper_rs"]) * 0.5, 2)
    
    cotton_water = cotton_eval["water_metrics"]["water_required_m3"]
    cotton_cost = cotton_eval["financial_metrics"]["total_investment_rs"]
    cotton_profit = cotton_eval["financial_metrics"]["expected_profit_rs"]
    
    water_diff_m3 = round(cotton_water - rot_water_total, 1)
    water_diff_pct = round((water_diff_m3 / max(1.0, cotton_water)) * 100.0, 1)
    
    # Biological Nitrogen Fixation (Soybean ~45kg/ha + Gram ~50kg/ha = ~95 kg N/ha on rotation cycle)
    n_fixed_total = round(48.0 * farm_size_ha, 1)
    
    if water_diff_m3 >= 0:
        water_badge = f"{water_diff_pct}% Water Saved!"
        water_narrative = f"saving {water_diff_pct}% supplemental water ({water_diff_m3:,.0f} m³) compared to full-season Cotton"
    else:
        extra_m3 = abs(water_diff_m3)
        extra_pct = abs(water_diff_pct)
        water_badge = f"+{extra_pct}% Water for 2 Cycles"
        water_narrative = (
            f"producing 2 full harvest cycles (Kharif + Rabi) yielding ₹{rot_profit_total:,.0f} net income. "
            f"While two complete crops require +{extra_pct}% supplemental irrigation (+{extra_m3:,.0f} m³) compared to single-cycle Cotton under high Kharif rain, "
            f"the rotation diversifies income across two selling windows and dramatically cuts crop failure risk"
        )
    
    cotton_water_def = max(0.0, round(cotton_water - adj_water_m3, 1))
    cotton_budget_def = max(0.0, round(cotton_cost - adj_budget_rs, 2))
    
    rot_water_def = max(0.0, round(rot_water_total - adj_water_m3, 1))
    rot_budget_def = max(0.0, round(rot_cost_total - adj_budget_rs, 2))
    rot_viable = (rot_water_def <= 1e-3) and (rot_budget_def <= 1.0)
    
    scale_note = ""
    if not rot_viable:
        safe_scale_acres = max(0.5, round(farm_size_acres * min(adj_water_m3 / max(1.0, rot_water_total), adj_budget_rs / max(1.0, rot_cost_total)), 1))
        scale_note = f" ⚠️ **Scale Advisory**: Across {farm_size_acres} acres, rotation demand exceeds your ceilings ({rot_water_def:,.0f} m³ water gap). Downscale to ~{safe_scale_acres} acres or install drip micro-irrigation to achieve 100% feasibility."

    return {
        "monoculture_cotton": {
            "title": "Option A: Monoculture Cotton (कपास एकपीक पद्धती)",
            "season": "Long Kharif (165 days)",
            "total_water_m3": cotton_water,
            "total_cost_rs": cotton_cost,
            "water_deficit_m3": cotton_water_def,
            "budget_deficit_rs": cotton_budget_def,
            "expected_profit_rs": cotton_profit,
            "profit_range": f"₹{cotton_eval['financial_metrics']['profit_lower_rs']:,.0f} – ₹{cotton_eval['financial_metrics']['profit_upper_rs']:,.0f}",
            "climate_risk": cotton_eval["climate_metrics"]["risk_level"],
            "soil_impact": "Heavy NPK Extraction & Soil Exhaustion",
            "is_viable": cotton_eval["financial_metrics"]["budget_feasible"] and cotton_eval["water_metrics"]["water_feasible"]
        },
        "rotation_soybean_gram": {
            "title": "Option B: Climate-Smart Soybean + Gram Rotation (सोयाबीन + हरभरा फेरपालट)",
            "season": "Kharif (105d) + Rabi (100d)",
            "total_water_m3": rot_water_total,
            "total_cost_rs": rot_cost_total,
            "water_deficit_m3": rot_water_def,
            "budget_deficit_rs": rot_budget_def,
            "expected_profit_rs": rot_profit_total,
            "profit_range": f"₹{rot_profit_lower:,.0f} – ₹{rot_profit_upper:,.0f}",
            "climate_risk": "Low to Moderate (Risk Diversified across 2 cycles)",
            "soil_impact": f"+{n_fixed_total} kg Biological Nitrogen Fixed (Restorative Legume Rotation)",
            "water_saved_m3": max(0.0, water_diff_m3),
            "water_saved_pct": max(0.0, water_diff_pct),
            "water_diff_m3": water_diff_m3,
            "water_diff_pct": water_diff_pct,
            "water_badge": water_badge,
            "is_viable": rot_viable
        },
        "systems_verdict": (
            f"The Soybean $\\rightarrow$ Gram rotation generates ₹{rot_profit_total:,.0f} annual net profit while "
            f"{water_narrative}. Moreover, its dual-legume root systems "
            f"enrich your soil with {n_fixed_total} kg of natural atmospheric nitrogen, cutting chemical fertilizer bills.{scale_note}"
        )
    }

if __name__ == "__main__":
    res = optimize_farming_strategy(farm_size_acres=2.5, available_budget_rs=50000, available_water_m3=3500)
    print("--- TOP RECOMMENDATION ---")
    top = res["top_recommendation"]
    print(f"Crop: {top['crop']} | RRI Score: {top['resilience_return_index']}/100")
    print(f"Why this won: {res['why_this_crop_won']}")
    print(f"Profit Range: {top['financial_metrics']['range_display_profit_rs']}")
    
    print("\n--- MULTI-SEASON ROTATION ---")
    rot = evaluate_annual_rotation(farm_size_acres=2.5, available_budget_rs=60000, available_water_m3=5000)
    print(rot["systems_verdict"])
