import streamlit as st
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="🇨🇦 Smart Farming Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #e8f5e9 0%, #e3f2fd 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: #1b5e20;
        font-weight: bold;
    }
    .main-header p {
        color: #2e7d32;
        font-size: 1.2rem;
        font-weight: 500;
    }
    .stat-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #1976d2;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0d47a1;
    }
    .stat-label {
        font-size: 1.1rem;
        color: #1565c0;
        font-weight: 600;
    }
    .recommendation-box {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2196f3;
        margin: 1rem 0;
        border: 2px solid #1976d2;
    }
    .recommendation-box h3 {
        color: #0d47a1;
        font-weight: bold;
    }
    .recommendation-box p {
        color: #1565c0;
        font-size: 1.05rem;
        font-weight: 500;
    }
    .info-card {
        background: #fff3e0;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #ff9800;
        margin: 1rem 0;
        border: 2px solid #f57c00;
    }
    .info-card li {
        color: #e65100;
        font-weight: 500;
        font-size: 1.05rem;
    }
    .success-message {
        background: #c8e6c9;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4caf50;
        margin: 1rem 0;
    }
    h1, h2, h3, h4 {
        color: #1b5e20 !important;
        font-weight: bold !important;
    }
    .stMarkdown h3 {
        color: #1b5e20 !important;
        font-weight: bold !important;
        font-size: 1.5rem !important;
    }
    .stMarkdown h4 {
        color: #2e7d32 !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'assessments' not in st.session_state:
    st.session_state.assessments = []
if 'current_assessment' not in st.session_state:
    st.session_state.current_assessment = {}
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'
if 'goals_completed' not in st.session_state:
    st.session_state.goals_completed = set()
if 'selected_crop' not in st.session_state:
    st.session_state.selected_crop = None

# Initialize OpenAI client
openai_client = None
try:
    import openai
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    openai_client = openai
except ImportError:
    st.error("⚠️ OpenAI library not installed. Please run: pip install openai")
    st.stop()
except KeyError:
    st.error("⚠️ OpenAI API key not found in secrets.toml. Please add it to continue.")
    st.stop()
except Exception as e:
    st.error(f"⚠️ Error initializing OpenAI: {str(e)}")
    st.stop()

# Goals definition
GOALS = [
    {'id': 'first_assessment', 'icon': '🎯', 'title': 'First Steps', 'description': 'Complete your first assessment', 'requirement': 1},
    {'id': 'five_assessments', 'icon': '📊', 'title': 'Getting Started', 'description': 'Complete 5 assessments', 'requirement': 5},
    {'id': 'ten_assessments', 'icon': '🌟', 'title': 'Committed Farmer', 'description': 'Complete 10 assessments', 'requirement': 10},
    {'id': 'all_crops', 'icon': '🌾', 'title': 'Crop Explorer', 'description': 'Try all 4 crop types', 'requirement': 4},
    {'id': 'all_seasons', 'icon': '🔄', 'title': 'Year-Round', 'description': 'Get advice for all 4 seasons', 'requirement': 4},
]

def generate_ai_recommendations(farmer_data):
    """Generate AI-powered farming recommendations using OpenAI"""
    if not openai_client:
        return generate_fallback_recommendations(farmer_data)
    
    try:
        prompt = f"""As an expert agricultural advisor for Canadian farming, provide specific recommendations for:

Farmer Profile:
- Name: {farmer_data['farmer_name']}
- Province: {farmer_data['province']}
- Season: {farmer_data['season']}
- Crop Stage: {farmer_data['crop_stage']}
- Selected Crop: {farmer_data['selected_crop']}

Please provide detailed recommendations in the following categories:
1. Weather-Based Advice (3-4 specific tips)
2. Pest & Disease Management (3-4 actionable items)
3. Soil & Fertilizer Guidance (3-4 recommendations)
4. Sustainable Farming Tips (3-4 practices)

Format your response as JSON with keys: weather_advice, pest_advice, soil_advice, sustainability_tips (each containing an array of strings). Only return the JSON, no other text."""

        response = openai_client.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert Canadian agricultural advisor. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
            content = content.strip()
        
        recommendations = json.loads(content)
        return recommendations
    
    except json.JSONDecodeError as e:
        st.warning("⚠️ AI response was not in correct format. Using fallback recommendations.")
        return generate_fallback_recommendations(farmer_data)
    except Exception as e:
        st.warning(f"⚠️ Error with AI: {str(e)}. Using fallback recommendations.")
        return generate_fallback_recommendations(farmer_data)

def generate_fallback_recommendations(farmer_data):
    """Fallback recommendations if AI fails"""
    crop = farmer_data['selected_crop']
    season = farmer_data['season']
    province = farmer_data['province']
    
    recommendations = {
        'weather_advice': [
            f"Monitor local weather forecasts daily for {season} conditions in {province}",
            "Watch for frost warnings and protect crops accordingly",
            "Track precipitation levels for optimal irrigation scheduling",
            "Plan fieldwork around weather windows to maximize efficiency"
        ],
        'pest_advice': [
            f"Scout fields regularly for common {crop} pests in your region",
            "Implement integrated pest management strategies to reduce chemical use",
            "Use crop rotation to naturally reduce pest pressure",
            "Monitor pest thresholds before applying treatments"
        ],
        'soil_advice': [
            "Conduct soil tests to determine nutrient levels and pH balance",
            f"Apply fertilizers based on {crop} requirements and soil test results",
            "Monitor soil moisture levels regularly for optimal crop growth",
            "Consider adding organic matter to improve soil structure"
        ],
        'sustainability_tips': [
            "Practice crop rotation to maintain soil health and reduce disease",
            "Reduce chemical inputs where possible through IPM strategies",
            "Implement water conservation techniques like drip irrigation",
            "Use cover crops during off-season to prevent erosion"
        ]
    }
    return recommendations

def check_goal_achievements():
    """Check and update goal achievements"""
    total = len(st.session_state.assessments)
    unique_crops = len(set(a.get('selected_crop', '') for a in st.session_state.assessments if a.get('selected_crop')))
    unique_seasons = len(set(a.get('season', '') for a in st.session_state.assessments if a.get('season')))
    
    if total >= 1:
        st.session_state.goals_completed.add('first_assessment')
    if total >= 5:
        st.session_state.goals_completed.add('five_assessments')
    if total >= 10:
        st.session_state.goals_completed.add('ten_assessments')
    if unique_crops >= 4:
        st.session_state.goals_completed.add('all_crops')
    if unique_seasons >= 4:
        st.session_state.goals_completed.add('all_seasons')

# Sidebar navigation
with st.sidebar:
    st.title("🇨🇦 Smart Farming")
    st.markdown("---")
    
    if st.button("🏠 Dashboard", use_container_width=True):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    if st.button("📝 New Assessment", use_container_width=True):
        st.session_state.page = 'profile'
        st.rerun()
    
    if st.button("🎯 Goals", use_container_width=True):
        st.session_state.page = 'goals'
        st.rerun()
    
    if st.button("🌤️ Weather", use_container_width=True):
        st.session_state.page = 'weather'
        st.rerun()
    
    if st.button("💰 Market Prices", use_container_width=True):
        st.session_state.page = 'market'
        st.rerun()
    
    if st.button("👥 Community", use_container_width=True):
        st.session_state.page = 'community'
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    st.metric("Total Assessments", len(st.session_state.assessments))
    st.metric("Goals Completed", f"{len(st.session_state.goals_completed)}/{len(GOALS)}")

# Main content area
if st.session_state.page == 'dashboard':
    st.markdown('<div class="main-header"><h1>🇨🇦 Smart Farming Assistant</h1><p>AI-Powered Agricultural Guidance for Canadian Farmers</p></div>', unsafe_allow_html=True)
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{len(st.session_state.assessments)}</div><div class="stat-label">Total Assessments</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{len(st.session_state.goals_completed)}</div><div class="stat-label">Goals Completed</div></div>', unsafe_allow_html=True)
    with col3:
        unique_crops = len(set(a.get('selected_crop', '') for a in st.session_state.assessments if a.get('selected_crop'))) if st.session_state.assessments else 0
        st.markdown(f'<div class="stat-box"><div class="stat-number">{unique_crops}</div><div class="stat-label">Crops Explored</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Get Started Button
    if st.button("🚀 Get Started - Create Assessment", use_container_width=True, type="primary"):
        st.session_state.page = 'profile'
        st.rerun()
    
    # Common Challenges
    st.markdown("### ⚠️ Common Farming Challenges in Canada")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("#### ❄️\n**Frost Risk**")
    with col2:
        st.markdown("#### ⏱️\n**Short Growing Season**")
    with col3:
        st.markdown("#### 🌧️\n**Unpredictable Weather**")
    with col4:
        st.markdown("#### 🐛\n**Pests & Disease**")

elif st.session_state.page == 'profile':
    st.markdown('<div class="main-header"><h1>📋 Your Farm Profile</h1><p>Tell us about your farming situation</p></div>', unsafe_allow_html=True)
    
    with st.form("profile_form"):
        farmer_name = st.text_input("👤 Farmer Name", placeholder="Enter your name")
        
        province = st.selectbox("📍 Province", [
            "", "Alberta", "British Columbia", "Manitoba", 
            "New Brunswick", "Newfoundland and Labrador", "Nova Scotia",
            "Ontario", "Prince Edward Island", "Quebec", "Saskatchewan"
        ])
        
        season = st.selectbox("🌤️ Current Season", [
            "", "Spring", "Summer", "Fall", "Winter"
        ])
        
        crop_stage = st.selectbox("🌱 Crop Stage", [
            "", "Pre-Planting", "Planting", "Growing", "Harvesting", "Post-Harvest"
        ])
        
        submitted = st.form_submit_button("Continue →", use_container_width=True, type="primary")
        
        if submitted:
            if farmer_name and province and season and crop_stage:
                st.session_state.current_assessment = {
                    'farmer_name': farmer_name,
                    'province': province,
                    'season': season,
                    'crop_stage': crop_stage,
                    'timestamp': datetime.now().isoformat()
                }
                st.session_state.page = 'crops'
                st.rerun()
            else:
                st.error("Please fill in all fields")
    
    if st.button("← Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()

elif st.session_state.page == 'crops':
    st.markdown('<div class="main-header"><h1>🌱 Crop Recommendations</h1><p>Select the crop you want guidance for</p></div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="recommendation-box">
        <h3>💡 Based on your profile:</h3>
        <p>Name: {st.session_state.current_assessment['farmer_name']} | 
        Province: {st.session_state.current_assessment['province']} | 
        Season: {st.session_state.current_assessment['season']} | 
        Stage: {st.session_state.current_assessment['crop_stage']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Recommended Crops for Your Region")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🌾\n\n**Wheat**", use_container_width=True, key="wheat"):
            st.session_state.selected_crop = "Wheat"
            st.rerun()
    
    with col2:
        if st.button("💛\n\n**Canola**", use_container_width=True, key="canola"):
            st.session_state.selected_crop = "Canola"
            st.rerun()
    
    with col3:
        if st.button("🌾\n\n**Barley**", use_container_width=True, key="barley"):
            st.session_state.selected_crop = "Barley"
            st.rerun()
    
    with col4:
        if st.button("🌾\n\n**Oats**", use_container_width=True, key="oats"):
            st.session_state.selected_crop = "Oats"
            st.rerun()
    
    # Show selected crop
    if st.session_state.selected_crop:
        st.success(f"✅ Selected: {st.session_state.selected_crop}")
        
        if st.button("Get AI Recommendations →", use_container_width=True, type="primary", key="get_recommendations"):
            st.session_state.current_assessment['selected_crop'] = st.session_state.selected_crop
            
            with st.spinner("🤖 Generating AI-powered recommendations..."):
                try:
                    recommendations = generate_ai_recommendations(st.session_state.current_assessment)
                    st.session_state.current_assessment['recommendations'] = recommendations
                    st.session_state.assessments.append(st.session_state.current_assessment.copy())
                    check_goal_achievements()
                    st.session_state.selected_crop = None  # Reset for next time
                    st.session_state.page = 'results'
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating recommendations: {str(e)}")
                    st.info("Please try again or contact support.")
    
    if st.button("← Back", key="back_to_profile"):
        st.session_state.selected_crop = None
        st.session_state.page = 'profile'
        st.rerun()

elif st.session_state.page == 'results':
    st.markdown('<div class="main-header"><h1>✅ Your Personalized Recommendations</h1><p>AI-generated guidance for your farm</p></div>', unsafe_allow_html=True)
    
    # Summary
    assessment = st.session_state.current_assessment
    st.markdown(f"""
    <div class="recommendation-box">
        <p><strong>👤 Farmer Name:</strong> {assessment.get('farmer_name', 'N/A')}</p>
        <p><strong>📍 Province:</strong> {assessment.get('province', 'N/A')}</p>
        <p><strong>🌤️ Season:</strong> {assessment.get('season', 'N/A')}</p>
        <p><strong>🌱 Crop Stage:</strong> {assessment.get('crop_stage', 'N/A')}</p>
        <p><strong>🌾 Selected Crop:</strong> {assessment.get('selected_crop', 'N/A')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Recommendations
    recommendations = assessment.get('recommendations', {})
    
    st.markdown("### 🌡️ Weather-Based Advice")
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    for tip in recommendations.get('weather_advice', []):
        st.markdown(f"- {tip}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### 🐛 Pest & Disease Management")
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    for tip in recommendations.get('pest_advice', []):
        st.markdown(f"- {tip}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### 💧 Soil & Fertilizer Guidance")
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    for tip in recommendations.get('soil_advice', []):
        st.markdown(f"- {tip}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### ♻️ Sustainable Farming Tips")
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    for tip in recommendations.get('sustainability_tips', []):
        st.markdown(f"- {tip}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.success("🎉 Recommendations generated successfully!")
    
    if st.button("Back to Dashboard", use_container_width=True, type="primary"):
        st.session_state.page = 'dashboard'
        st.rerun()

elif st.session_state.page == 'goals':
    st.markdown('<div class="main-header"><h1>🎯 Goals & Achievements</h1><p>Track your farming journey</p></div>', unsafe_allow_html=True)
    
    total = len(st.session_state.assessments)
    progress = (len(st.session_state.goals_completed) / len(GOALS)) * 100
    
    st.metric("Overall Progress", f"{int(progress)}%")
    st.progress(progress / 100)
    
    st.markdown("### Your Achievements")
    
    unique_crops = len(set(a.get('selected_crop', '') for a in st.session_state.assessments if a.get('selected_crop')))
    unique_seasons = len(set(a.get('season', '') for a in st.session_state.assessments if a.get('season')))
    
    for goal in GOALS:
        completed = goal['id'] in st.session_state.goals_completed
        
        if goal['id'] == 'first_assessment':
            current_progress = min(total, 1)
        elif goal['id'] == 'five_assessments':
            current_progress = min(total, 5)
        elif goal['id'] == 'ten_assessments':
            current_progress = min(total, 10)
        elif goal['id'] == 'all_crops':
            current_progress = unique_crops
        elif goal['id'] == 'all_seasons':
            current_progress = unique_seasons
        
        status = "✅" if completed else "⏳"
        st.markdown(f"### {goal['icon']} {goal['title']} {status}")
        st.markdown(f"*{goal['description']}*")
        st.progress(current_progress / goal['requirement'])
        st.markdown(f"Progress: {current_progress}/{goal['requirement']}")
        st.markdown("---")
    
    if st.button("← Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()

elif st.session_state.page == 'weather':
    st.markdown('<div class="main-header"><h1>🌤️ Weather Forecast</h1><p>7-day agricultural weather outlook</p></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="recommendation-box">
        <h3>📍 Canada - Agricultural Regions</h3>
        <p>General weather patterns and recommendations for Canadian farming regions</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ☀️ Today's Conditions")
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("""
    - Temperature: 18°C - 24°C
    - Conditions: Partly Cloudy
    - Wind: 15 km/h NW
    - Precipitation: 20% chance
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### 📅 Week Ahead")
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("""
    - Days 1-3: Warm and dry conditions ideal for fieldwork
    - Days 4-5: Scattered showers expected, delay spraying operations
    - Days 6-7: Clearing conditions, good for harvesting
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("← Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()

elif st.session_state.page == 'market':
    st.markdown('<div class="main-header"><h1>💰 Market Prices</h1><p>Current commodity prices in Canada</p></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="recommendation-box">
        <h3>📈 Market Trends</h3>
        <p>Commodity prices are updated weekly based on Canadian agricultural markets</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🌾 Wheat", "$320/tonne", "2.5%")
        st.metric("🌾 Barley", "$280/tonne", "-0.5%")
    with col2:
        st.metric("💛 Canola", "$650/tonne", "1.8%")
        st.metric("🌾 Oats", "$310/tonne", "3.2%")
    
    if st.button("← Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()

elif st.session_state.page == 'community':
    st.markdown('<div class="main-header"><h1>👥 Community Tips</h1><p>Shared wisdom from Canadian farmers</p></div>', unsafe_allow_html=True)
    
    st.markdown("### 🔥 Top Tips This Week")
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    st.markdown("""
    - "Early morning scouting is best for detecting pest issues before they spread" - Saskatchewan farmer
    - "Keep detailed records of applications and yields for better planning next year" - Ontario farmer
    - "Soil testing in fall gives you more time to plan amendments for spring" - Alberta farmer
    - "Consider companion planting to naturally reduce pest pressure" - BC farmer
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("← Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()
    