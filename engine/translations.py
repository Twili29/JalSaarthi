"""
JalSaarthi - Trilingual Localization Engine (English, Marathi, Hindi)
Provides complete multilingual translations for:
- Navigation & Brand
- Home Screen (Plan Your Next Crop, Quick Insights, Tips)
- My Reports (Personalized Recommendation, Yield vs Risk, Why Crop Won)
- Scenario Analysis (Climate Shocks, Stress Sliders)
- How to Use / Information (Step-by-step User Manual & Methodology)
- Interactive Pop-up Walkthrough Guide
"""

TRANSLATIONS = {
    "en": {
        # Navigation
        "brand_name": "JalSaarthi",
        "tagline": "Smart Farming, A Greener Tomorrow.",
        "nav_home": "Home",
        "nav_reports": "My Reports",
        "nav_scenario": "Scenario Analysis",
        "nav_info": "How to Use / Information",
        "language_select": "Language / भाषा",
        "guide_button": "📖 How to Use",
        
        # Home Screen
        "welcome_title": "Welcome to JalSaarthi",
        "welcome_subtitle": "Your AI-powered farming partner for smarter, climate-resilient decisions.",
        "plan_title": "Plan Your Next Crop",
        "plan_subtitle": "Tell us about your farm, and let JalSaarthi guide you!",
        "location_label": "Location",
        "district_solapur": "Solapur (Drought Belt)",
        "district_pune": "Pune (Transition Zone)",
        "water_label": "Available Water",
        "budget_label": "Budget",
        "btn_get_recommendation": "Get Recommendation →",
        "adv_settings": "⚙️ Advanced Farm & Pump Settings (Optional)",
        "land_size_label": "Farm Land Size (Acres)",
        "soil_label": "Soil Profile",
        "irrigation_label": "Irrigation Method",
        "pump_hp_label": "Pump Motor Capacity",
        "power_hours_label": "Daily Electricity Hours (MSEDCL)",
        "pumping_days_label": "Planned Pumping Days",
        
        # Quick Insights
        "quick_insights_title": "Quick Insights",
        "best_crop_label": "Best Crop",
        "water_needed_label": "Water Needed",
        "climate_risk_label": "Climate Risk",
        "expected_profit_label": "Expected Profit",
        "did_you_know_title": "Did You Know?",
        "did_you_know_text": "Proper water planning and crop rotation can increase crop yield by up to 30% while securing aquifers!",
        "learn_more": "Learn More →",
        
        # Recommendation / My Reports Screen
        "back_to_home": "← Back",
        "download_report": "📥 Download Report",
        "rec_title": "Your Personalized Recommendation",
        "rec_card_crop": "Recommended Crop",
        "rec_card_water": "Water Plan",
        "rec_card_profit": "Expected Profit",
        "chart_title": "Yield vs Risk Overview",
        "chart_yield_legend": "Yield",
        "chart_risk_legend": "Risk Level",
        "why_title": "Why {crop}?",
        "why_point_1": "Thrives in current climate conditions",
        "why_point_2": "Optimized water requirement",
        "why_point_3": "Strong market demand",
        "why_point_4": "Protects soil health & resilience",
        "all_crops_title": "Comparative Evaluation of All Crops",
        "rotation_title": "🔄 Systems Thinking: Multi-Season Crop Rotation",
        "btn_explore_scenarios": "Explore Scenario Analysis →",
        
        # Scenario Analysis Screen
        "scenario_title": "Scenario Analysis",
        "scenario_subtitle": "See how different conditions affect your strategy",
        "quick_scenarios_title": "⚡ Quick Climate Shock Scenarios",
        "scen_rain_title": "↓ 20% Rainfall",
        "scen_rain_sub": "Monsoon Dry Spell",
        "scen_water_title": "↓ 30% Water",
        "scen_water_sub": "Borewell Depletion",
        "scen_budget_title": "↓ Budget by 20%",
        "scen_budget_sub": "Credit Crunch",
        "btn_view_details": "View Details →",
        "custom_simulator_title": "🎛️ Interactive Climate Stress Simulator",
        "slider_rain": "Monsoon Rain Anomaly (%)",
        "slider_water": "Groundwater / Borewell Depletion (%)",
        "slider_temp": "Heatwave / Temperature Shift (°C)",
        "slider_budget": "Working Capital Crunch (₹)",
        "active_shock_alert": "⚡ Active Scenario: {details} — Optimization updated live!",
        
        # How to Use / Information Screen
        "info_title": "How to Use & Information",
        "info_subtitle": "Step-by-step user guide, agronomic benchmarks, and scientific methodology",
        "guide_step_1_title": "Step 1: Enter Farm Location & Land Size",
        "guide_step_1_desc": "Select Solapur (Semi-Arid Drought Belt) or Pune (Transition Zone). JalSaarthi automatically pre-fills sensible regional defaults.",
        "guide_step_2_title": "Step 2: Configure Available Irrigation Water",
        "guide_step_2_desc": "Use the Farmer Mode pump calculator (HP + Daily Power Hours + Days) or direct volumetric slider to define your seasonal water ceiling.",
        "guide_step_3_title": "Step 3: Review AI-Powered Recommendation",
        "guide_step_3_desc": "Inspect your customized crop plan with 90% statistical confidence intervals, APMC mandi rates, and water efficiency scores.",
        "guide_step_4_title": "Step 4: Stress-Test with Scenario Analysis",
        "guide_step_4_desc": "Simulate monsoon drought (-20%), borewell drops (-30%), or heatwaves to verify farm resilience before sowing.",
        "methodology_fao_title": "📘 Hydrological Modeling (FAO-56 Standard)",
        "methodology_ml_title": "🤖 Machine Learning Yield Model (Scikit-Learn)",
        "methodology_mandi_title": "📊 Sourced APMC Mandi Market Intelligence",
        "methodology_pump_title": "⚡ Rural Pumping Standards (BIS & MSEDCL)",
        
        # Pop-up Guide
        "popup_title": "📖 How to Use JalSaarthi (जलसारथी)",
        "popup_welcome": "Welcome to your climate-resilient farming partner! Follow these quick steps to get the best recommendation:",
        "popup_step_1": "1️⃣ <b>Tell Us About Your Farm:</b> Enter your location, available water, and capital on the Home page.",
        "popup_step_2": "2️⃣ <b>Click 'Get Recommendation':</b> Our FAO-56 and ML engine ranks all regional crops by Resilience-Return Index (RRI).",
        "popup_step_3": "3️⃣ <b>Check Yield vs Risk:</b> View statistical profit ranges, water requirements, and APMC price grounding in 'My Reports'.",
        "popup_step_4": "4️⃣ <b>Simulate What-If Shocks:</b> Visit 'Scenario Analysis' to see how your farm survives droughts or borewell drops.",
        "popup_close_btn": "Got it! Let's Get Started 🚀"
    },
    
    "mr": {
        # Navigation
        "brand_name": "जलसारथी (JalSaarthi)",
        "tagline": "स्मार्ट शेती, समृद्ध उद्याची.",
        "nav_home": "मुख्यपृष्ठ (Home)",
        "nav_reports": "माझा अहवाल (My Reports)",
        "nav_scenario": "तणाव विश्लेषण (Scenario Analysis)",
        "nav_info": "माहिती व वापर (How to Use)",
        "language_select": "भाषा निवडा / Language",
        "guide_button": "📖 वापर कसा करावा",
        
        # Home Screen
        "welcome_title": "जलसारथी मध्ये आपले स्वागत आहे",
        "welcome_subtitle": "हवामान-लवचिक आणि फायदेशीर शेतीसाठी तुमचा AI तंत्रज्ञान भागीदार.",
        "plan_title": "तुमच्या पुढील पिकाचे नियोजन करा",
        "plan_subtitle": "तुमच्या शेतीबद्दल माहिती द्या, आणि जलसारथीला मार्गदर्शन करू द्या!",
        "location_label": "स्थान / जिल्हा",
        "district_solapur": "सोलापूर (दुष्काळी पट्टा)",
        "district_pune": "पुणे (संक्रमण विभाग)",
        "water_label": "उपलब्ध पाणी",
        "budget_label": "भांडवल",
        "btn_get_recommendation": "शिफारस मिळवा →",
        "adv_settings": "⚙️ शेतजमीन व पंप तपशील (ऐच्छिक)",
        "land_size_label": "शेतजमीन क्षेत्र (एकर)",
        "soil_label": "जमिनीचा प्रकार",
        "irrigation_label": "सिंचन पद्धती",
        "pump_hp_label": "पंप मोटर क्षमता (HP)",
        "power_hours_label": "रोजचे वीज तास (महावितरण)",
        "pumping_days_label": "हंगामातील सिंचन दिवस",
        
        # Quick Insights
        "quick_insights_title": "द्रुत माहिती (Quick Insights)",
        "best_crop_label": "सर्वोत्तम पीक",
        "water_needed_label": "पाण्याची गरज",
        "climate_risk_label": "हवामान जोखीम",
        "expected_profit_label": "अपेक्षित नफा",
        "did_you_know_title": "तुम्हाला माहीत आहे का?",
        "did_you_know_text": "योग्य पाणी नियोजन आणि पीक फेरपालट करून पिकाचे उत्पादन ३०% पर्यंत वाढू शकते आणि भूजल सुरक्षित राहते!",
        "learn_more": "अधिक जाणून घ्या →",
        
        # Recommendation / My Reports Screen
        "back_to_home": "← मागे जा",
        "download_report": "📥 अहवाल डाउनलोड करा",
        "rec_title": "तुमची वैयक्तिक पीक शिफारस",
        "rec_card_crop": "शिफारस केलेले पीक",
        "rec_card_water": "पाणी नियोजन",
        "rec_card_profit": "अपेक्षित नफा",
        "chart_title": "उत्पादन आणि हवामान जोखीम तुलना",
        "chart_yield_legend": "उत्पादन",
        "chart_risk_legend": "जोखीम पातळी",
        "why_title": "{crop} ची निवड का केली?",
        "why_point_1": "सध्याच्या हवामानात आणि जमिनीत उत्कृष्ट वाढ",
        "why_point_2": "कमी पाण्यात शाश्वत उत्पादन व सर्वोच्च जल उत्पादकता",
        "why_point_3": "अधिकृत बाजारभाव (APMC) आणि हमीभावाचे संरक्षण",
        "why_point_4": "जमिनीची सुपीकता टिकवून ठेवणारे व दुष्काळ-सहनशील",
        "all_crops_title": "सर्व ५ पिकांची तुलनात्मक पडताळणी",
        "rotation_title": "🔄 वार्षिक पीक फेरपालट: खरीप → रब्बी चक्र",
        "btn_explore_scenarios": "तणाव विश्लेषण पहा (Scenario Analysis) →",
        
        # Scenario Analysis Screen
        "scenario_title": "तणाव विश्लेषण (Scenario Analysis)",
        "scenario_subtitle": "हवामान आणि आर्थिक बदलानुसार पीक रणनीती कशी बदलते ते पहा",
        "quick_scenarios_title": "⚡ झटपट हवामान तणाव परिस्थिती",
        "scen_rain_title": "↓ पाऊस २०% कमी",
        "scen_rain_sub": "पावसाचा मोठा खंड",
        "scen_water_title": "↓ पाणी ३०% कमी",
        "scen_water_sub": "विहीर/बोअरवेल घसरण",
        "scen_budget_title": "↓ भांडवल २०% कमी",
        "scen_budget_sub": "आर्थिक चणचण",
        "btn_view_details": "तपशील पहा →",
        "custom_simulator_title": "🎛️ परस्परसंवादी हवामान सिम्युलेटर",
        "slider_rain": "मान्सून पाऊस तफावत (%)",
        "slider_water": "बोअरवेल/भूजल घसरण (%)",
        "slider_temp": "तापमान वाढ / उष्णतेची लाट (°C)",
        "slider_budget": "भांडवलातील कपात (₹)",
        "active_shock_alert": "⚡ सक्रिय परिस्थिती: {details} — शिफारसी रिअल-टाइम अपडेट झाल्या!",
        
        # How to Use / Information Screen
        "info_title": "माहिती व वापर कसा करावा",
        "info_subtitle": "शेतकऱ्यांसाठी टप्प्याटप्प्याने मार्गदर्शन आणि वैज्ञानिक पद्धती",
        "guide_step_1_title": "टप्पा १: शेतीचे स्थान आणि क्षेत्र निवडा",
        "guide_step_1_desc": "सोलापूर किंवा पुणे जिल्हा निवडा. जलसारथी स्थानिक हवामानानुसार योग्य माहिती आपोआप भरते.",
        "guide_step_2_title": "टप्पा २: उपलब्ध पाणी किंवा मोटर तास सांगा",
        "guide_step_2_desc": "पंप HP आणि वीज तास टाकून उपलब्ध पाण्याचा अचूक अंदाज घ्या किंवा थेट लिटरमध्ये पाणी टाका.",
        "guide_step_3_title": "टप्पा ३: AI शिफारस आणि नफा तपासा",
        "guide_step_3_desc": "९०% सांख्यिकीय अचूकतेसह अपेक्षित उत्पादन, बाजारभाव आणि पाणी बचत तपासा.",
        "guide_step_4_title": "टप्पा ४: दुष्काळ परिस्थितीत चाचणी घ्या",
        "guide_step_4_desc": "पाऊस कमी पडल्यास किंवा पाणी आटल्यास कोणते पीक तरेल हे आधीच तपासा.",
        "methodology_fao_title": "📘 जल विज्ञान मॉडेल (FAO-56 आंतरराष्ट्रीय मानक)",
        "methodology_ml_title": "🤖 मशीन लर्निंग उत्पादन अंदाज मॉडेल (Scikit-Learn)",
        "methodology_mandi_title": "📊 अधिकृत APMC बाजारभाव माहिती (Agmarknet)",
        "methodology_pump_title": "⚡ कृषी पंप व वीज क्षमता मानके (BIS व महावितरण)",
        
        # Pop-up Guide
        "popup_title": "📖 जलसारथी वापर कसा करावा (Guide)",
        "popup_welcome": "जलसारथी मध्ये आपले स्वागत! योग्य पीक निवडण्यासाठी खालील सोप्या पायऱ्या वापरा:",
        "popup_step_1": "1️⃣ <b>शेतीची माहिती भरा:</b> मुख्यपृष्ठावर जिल्हा, पाणी आणि भांडवल निवडा.",
        "popup_step_2": "2️⃣ <b>'शिफारस मिळवा' वर क्लिक करा:</b> आमचे AI इंजिन सर्वोत्तम आणि सुरक्षित पीक निवडेल.",
        "popup_step_3": "3️⃣ <b>अहवाल तपासा:</b> 'माझा अहवाल' मध्ये नफा, पाण्याची गरज आणि कारणे पहा.",
        "popup_step_4": "4️⃣ <b>दुष्काळ चाचणी घ्या:</b> 'तणाव विश्लेषण' मध्ये पाऊस कमी झाल्यावर काय करावे ते पहा.",
        "popup_close_btn": "समजले! शेतीचे नियोजन करूया 🚀"
    },
    
    "hi": {
        # Navigation
        "brand_name": "जलसारथी (JalSaarthi)",
        "tagline": "स्मार्ट खेती, समृद्ध कल।",
        "nav_home": "होम (Home)",
        "nav_reports": "मेरी रिपोर्ट (My Reports)",
        "nav_scenario": "तनाव विश्लेषण (Scenario Analysis)",
        "nav_info": "जानकारी व उपयोग (How to Use)",
        "language_select": "भाषा चुनें / Language",
        "guide_button": "📖 उपयोग कैसे करें",
        
        # Home Screen
        "welcome_title": "जलसारथी में आपका स्वागत है",
        "welcome_subtitle": "जलवायु-अनुकूल और अधिक मुनाफे वाली खेती के लिए आपका AI सलाहकार।",
        "plan_title": "अपनी अगली फसल की योजना बनाएं",
        "plan_subtitle": "अपने खेत की जानकारी दें, और जलसारथी को मार्गदर्शन करने दें!",
        "location_label": "स्थान / जिला",
        "district_solapur": "सोलापुर (सूखा क्षेत्र)",
        "district_pune": "पुणे (संक्रमण क्षेत्र)",
        "water_label": "उपलब्ध पानी",
        "budget_label": "बजट",
        "btn_get_recommendation": "सिफारिश प्राप्त करें →",
        "adv_settings": "⚙️ उन्नत खेत और पंप सेटिंग्स (वैकल्पिक)",
        "land_size_label": "खेत का आकार (एकड़)",
        "soil_label": "मिट्टी का प्रकार",
        "irrigation_label": "सिंचाई विधि",
        "pump_hp_label": "पंप मोटर क्षमता (HP)",
        "power_hours_label": "दैनिक बिजली घंटे (MSEDCL)",
        "pumping_days_label": "योजनाबद्ध सिंचाई दिन",
        
        # Quick Insights
        "quick_insights_title": "त्वरित अंतर्दृष्टि (Quick Insights)",
        "best_crop_label": "सर्वोत्तम फसल",
        "water_needed_label": "पानी की आवश्यकता",
        "climate_risk_label": "जलवायु जोखिम",
        "expected_profit_label": "अपेक्षित मुनाफा",
        "did_you_know_title": "क्या आप जानते हैं?",
        "did_you_know_text": "उचित जल योजना और फसल चक्र अपनाने से फसल की पैदावार 30% तक बढ़ सकती है और भूजल सुरक्षित रहता है!",
        "learn_more": "और जानें →",
        
        # Recommendation / My Reports Screen
        "back_to_home": "← वापस जाएं",
        "download_report": "📥 रिपोर्ट डाउनलोड करें",
        "rec_title": "आपकी व्यक्तिगत फसल सिफारिश",
        "rec_card_crop": "अनुशंसित फसल",
        "rec_card_water": "जल योजना",
        "rec_card_profit": "अपेक्षित मुनाफा",
        "chart_title": "पैदावार और जलवायु जोखिम तुलना",
        "chart_yield_legend": "पैदावार",
        "chart_risk_legend": "जोखिम स्तर",
        "why_title": "{crop} को क्यों चुना गया?",
        "why_point_1": "मौजूदा जलवायु और मिट्टी में बेहतरीन अनुकूलन",
        "why_point_2": "कम पानी में अधिकतम पैदावार और उच्चतम जल उत्पादकता",
        "why_point_3": "आधिकारिक मंडी भाव (APMC) और न्यूनतम समर्थन मूल्य की सुरक्षा",
        "why_point_4": "मिट्टी की उर्वरता बढ़ाने वाली और सूखा-सहिष्णु फसल",
        "all_crops_title": "सभी 5 प्रमुख फसलों का तुलनात्मक मूल्यांकन",
        "rotation_title": "🔄 वार्षिक फसल चक्र: खरीफ → रबी प्रणाली",
        "btn_explore_scenarios": "तनाव विश्लेषण देखें (Scenario Analysis) →",
        
        # Scenario Analysis Screen
        "scenario_title": "तनाव विश्लेषण (Scenario Analysis)",
        "scenario_subtitle": "देखें कि मौसम और वित्तीय बदलाव आपकी रणनीति को कैसे प्रभावित करते हैं",
        "quick_scenarios_title": "⚡ त्वरित जलवायु झटके की स्थितियां",
        "scen_rain_title": "↓ बारिश 20% कम",
        "scen_rain_sub": "मानसून में लंबा सूखा",
        "scen_water_title": "↓ पानी 30% कम",
        "scen_water_sub": "बोरवेल जलस्तर में गिरावट",
        "scen_budget_title": "↓ बजट 20% कम",
        "scen_budget_sub": "पूंजी की कमी",
        "btn_view_details": "विवरण देखें →",
        "custom_simulator_title": "🎛️ इंटरएक्टिव जलवायु सिम्युलेटर",
        "slider_rain": "मानसून वर्षा विचलन (%)",
        "slider_water": "भूजल / बोरवेल गिरावट (%)",
        "slider_temp": "तापमान वृद्धि / लू (°C)",
        "slider_budget": "कार्यशील पूंजी में कमी (₹)",
        "active_shock_alert": "⚡ सक्रिय स्थिति: {details} — सिफारिशें तुरंत अपडेट हो गईं!",
        
        # How to Use / Information Screen
        "info_title": "जानकारी व उपयोग कैसे करें",
        "info_subtitle": "किसानों के लिए चरणबद्ध मार्गदर्शिका और वैज्ञानिक कार्यप्रणाली",
        "guide_step_1_title": "चरण 1: अपने खेत का स्थान और क्षेत्रफल चुनें",
        "guide_step_1_desc": "सोलापुर या पुणे जिला चुनें। जलसारथी क्षेत्रीय मानकों के आधार पर आंकड़े स्वतः भरता है।",
        "guide_step_2_title": "चरण 2: उपलब्ध पानी या पंप घंटे दर्ज करें",
        "guide_step_2_desc": "पंप HP और बिजली के घंटे दर्ज करके मौसमी पानी का सटीक हिसाब लगाएं।",
        "guide_step_3_title": "चरण 3: AI सिफारिश और लाभ का विश्लेषण करें",
        "guide_step_3_desc": "90% सांख्यिकीय सटीकता के साथ अनुमानित उत्पादन, मंडी भाव और जल बचत देखें।",
        "guide_step_4_title": "चरण 4: सूखे और संकट की स्थिति में परीक्षण करें",
        "guide_step_4_desc": "बारिश कम होने या पानी सूखने पर खेत को नुकसान से बचाने का उपाय पहले से जानें।",
        "methodology_fao_title": "📘 जल विज्ञान मॉडल (FAO-56 मानक)",
        "methodology_ml_title": "🤖 मशीन लर्निंग पैदावार मॉडल (Scikit-Learn)",
        "methodology_mandi_title": "📊 आधिकारिक APMC मंडी भाव (Agmarknet)",
        "methodology_pump_title": "⚡ कृषि पंप और बिजली मानक (BIS और MSEDCL)",
        
        # Pop-up Guide
        "popup_title": "📖 जलसारथी उपयोग कैसे करें (Guide)",
        "popup_welcome": "जलसारथी में आपका स्वागत है! बेहतर फसल चुनने के लिए इन सरल चरणों का पालन करें:",
        "popup_step_1": "1️⃣ <b>खेत की जानकारी दर्ज करें:</b> होम पेज पर अपना जिला, उपलब्ध पानी और बजट चुनें।",
        "popup_step_2": "2️⃣ <b>'सिफारिश प्राप्त करें' दबाएं:</b> हमारा AI इंजन आपके लिए सबसे सुरक्षित और लाभदायक फसल चुनेगा।",
        "popup_step_3": "3️⃣ <b>अपनी रिपोर्ट देखें:</b> 'मेरी रिपोर्ट' में लाभ, पानी की आवश्यकता और फसल की विशेषताएं देखें।",
        "popup_step_4": "4️⃣ <b>सूखे की जांच करें:</b> 'तनाव विश्लेषण' में बारिश कम होने पर क्या करें यह परखें।",
        "popup_close_btn": "समझ गया! चलिए शुरू करते हैं 🚀"
    }
}

def get_text(key: str, lang: str = "en", **kwargs) -> str:
    """Retrieves localized string for key with language fallback and variable formatting."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
