import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import random
import time
from groq import Groq
import io
from datetime import datetime
import traceback # Added for detailed error logging

# --- App Configuration ---
st.set_page_config(
    page_title="🌐 PoliBot : Crisis Simulation",
    layout="wide",
    page_icon="🌍",
    initial_sidebar_state="expanded"
)

# --- Custom CSS Styling ---
# Removed .report-style as it's no longer needed
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f6;
    }
    .stButton>button {
        color: white;
        background-color: #007bff;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    /* Removed .report-style CSS */
    .log-entry {
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border-radius: 8px;
        background-color: #f8f9fa;
        border-left: 4px solid #4dabf7;
        font-size: 0.95em;
    }
    /* Removed treaty-card CSS as we are using st.info now */
    /* Keep h3 and h4 styles if used elsewhere, otherwise can remove */
    h3 {
       color: #0056b3;
       border-bottom: 2px solid #007bff;
       padding-bottom: 0.3rem;
       margin-bottom: 1rem;
    }
    h4 { /* Style for treaty heading */
        color: #333;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- Groq API Setup ---
try:
    # IMPORTANT: Replace with your actual Groq API key or use Streamlit secrets
    # Example using secrets (recommended):
    groq_api_key = st.secrets["GROQ_API_KEY"]
    groq_client = Groq(api_key=groq_api_key)

    # Using placeholder key for demonstration (REPLACE THIS)
    # groq_client = Groq(api_key=") # Replace with your key

    # Simple check (optional, consumes minimal quota)
    groq_client.models.list()
except Exception as e:
    st.error(f"Failed to initialize Groq client: {e}. Check API Key and network connection.", icon="🚨")
    st.stop()

MODEL = "llama3-70b-8192" # Or choose another appropriate model like llama3-8b-8192

# --- Country Database ---
COUNTRY_PROFILES = {
    "USA": {
        "strengths": ["Military", "Economy", "Technology", "Diplomatic Influence"],
        "weaknesses": ["Political Polarization", "National Debt", "Infrastructure Gaps"],
        "interests": ["Global Stability", "Free Trade", "Democracy Promotion", "Counter-terrorism"],
        "color": "#0033A0"
    },
    "China": {
        "strengths": ["Manufacturing", "Infrastructure", "Population", "Economic Growth Rate"],
        "weaknesses": ["Aging Population", "Environmental Issues", "Regional Tensions"],
        "interests": ["Regional Dominance", "Technological Supremacy", "Economic Partnerships", "One China Policy"],
        "color": "#DE2910"
    },
    "India": {
        "strengths": ["Large Workforce", "IT Sector", "Strategic Location", "Democratic System"],
        "weaknesses": ["Infrastructure Deficits", "Poverty & Inequality", "Bureaucracy"],
        "interests": ["Economic Development", "Regional Security", "Climate Action", "Non-alignment"],
        "color": "#FF9933"
    },
    "Russia": {
        "strengths": ["Vast Natural Resources", "Military Power", "Cyber Capabilities", "UN Security Council Veto"],
        "weaknesses": ["Economic Sanctions", "Demographic Decline", "Technological Lag (non-military)"],
        "interests": ["Regional Sphere of Influence", "Energy Markets", "National Security", "Multipolar World Order"],
        "color": "#0039A6"
    },
    "Germany": {
        "strengths": ["Strong Industry", "Engineering Excellence", "EU Leadership", "Export Economy"],
        "weaknesses": ["Energy Dependence", "Aging Population", "Military Underfunding (historical)"],
        "interests": ["EU Stability & Integration", "Climate Policy Leadership", "International Trade", "Human Rights"],
        "color": "#FFCC00"
    },
    "Brazil": {
        "strengths": ["Agriculture Powerhouse", "Natural Resources", "Regional Influence (LatAm)", "Biodiversity"],
        "weaknesses": ["Political Instability", "Infrastructure Bottlenecks", "Deforestation"],
        "interests": ["Economic Growth", "South American Integration", "Environmental Sustainability", "Social Equality"],
        "color": "#009B3A"
    },
     "South Africa": {
        "strengths": ["Mineral Wealth", "Developed Infrastructure (regional context)", "Constitutional Democracy", "Regional Hub"],
        "weaknesses": ["High Unemployment", "Inequality", "Energy Crisis (Eskom)", "Corruption"],
        "interests": ["African Development", "Regional Stability", "Trade Partnerships (BRICS, etc.)", "Addressing Inequality"],
        "color": "#007A4D"
    },
}

# --- Scenario Database ---
SCENARIO_DETAILS = {
    "🌪️ Climate Collapse": {
        "description": "Rapid sea-level rise, extreme weather events (heatwaves, floods, storms), and failing agricultural yields threaten global stability and resource access.",
        "key_issues": ["Coastal city inundation", "Food security crisis", "Mass climate migration", "Water resource conflicts", "Carbon reduction targets"],
        "historical": "Amplified effects seen in events like the 1930s Dust Bowl, Hurricane Katrina, or recent global heatwaves, but occurring simultaneously and globally."
    },
    "🦠 Global Pandemic MkII": {
        "description": "A novel airborne pathogen emerges with high transmissibility, significant morbidity/mortality across age groups, and resistance to initial treatments.",
        "key_issues": ["Healthcare system collapse", "Global supply chain disruption", "Vaccine development & equitable distribution", "Border closures & travel restrictions", "Economic recession"],
        "historical": "Combines lessons from COVID-19 (global spread, economic impact) and historical plagues (higher mortality potential), plus potential for faster mutation."
    },
    "⚡ Gridlock Energy Crisis": {
        "description": "Simultaneous disruption of major fossil fuel supplies (geopolitics, infrastructure failure) and slow renewable rollout leads to critical global energy shortages.",
        "key_issues": ["Skyrocketing fuel prices", "Industrial production halts", "Energy rationing", "Renewable transition acceleration pressures", "Geopolitical tensions over remaining resources"],
        "historical": "Severity exceeding the 1970s oil crises due to higher global energy dependence and interconnectedness, coupled with transition challenges."
    },
    "🚰 Multi-Regional Water Wars": {
        "description": "Severe droughts exacerbated by climate change and poor management lead to critical freshwater shortages in multiple densely populated/agricultural regions simultaneously.",
        "key_issues": ["Agricultural collapse & famine risk", "Cross-border water disputes escalating to conflict", "Urban water supply failure", "Investment in desalination/water tech", "Hydro-diplomacy needs"],
        "historical": "Scaling up regional crises like those seen around the Nile, Jordan River, or Indus basins, or Cape Town's 'Day Zero' threat, to multiple global hotspots at once."
    },
    "🛂 Cascading Refugee Crisis": {
        "description": "A confluence of conflict, economic collapse, and climate disasters triggers unprecedented mass displacement across several continents.",
        "key_issues": ["Overwhelmed border security", "Humanitarian aid funding gaps", "Host country integration challenges", "Political destabilization in receiving nations", "Addressing root causes of displacement"],
        "historical": "Magnitude significantly larger than the 2015 European migrant crisis or Syrian refugee crisis, involving more diverse origins and destinations."
    },
    "🤖 AI Cold War": {
        "description": "Rapid, unregulated advances in Artificial General Intelligence (AGI) research by competing blocs triggers intense geopolitical rivalry, mistrust, and fears of autonomous weapons or societal control.",
        "key_issues": ["AI arms race (autonomous weapons)", "Economic disruption (job displacement)", "AI safety and ethics agreements", "Control over critical AI infrastructure/data", "Risk of accidental escalation"],
        "historical": "Analogous to the Nuclear Cold War, but focused on AI dominance, with faster development cycles and potentially more unpredictable outcomes."
     }
}

# --- Helper Functions ---
def generate_negotiation_message(speaker, receiver, scenario, negotiation_style, turn, context_log):
    scenario_details = SCENARIO_DETAILS[scenario]
    recent_interactions = "\n".join(context_log[-3:]) # Use last 3 interactions

    system_prompt = f"""
    You are an expert simulator of a diplomat representing {speaker}, negotiating with {receiver}.
    The global crisis is: {scenario} - {scenario_details['description']}
    Key crisis issues: {', '.join(scenario_details['key_issues'])}
    Historical context: {scenario_details['historical']}

    Your country ({speaker}) profile: {COUNTRY_PROFILES.get(speaker, {'interests': ['National Survival']})}
    Their country ({receiver}) profile: {COUNTRY_PROFILES.get(receiver, {'interests': ['National Survival']})}

    Negotiation style to adopt: {negotiation_style}.
    Current negotiation round: {turn}.

    Recent context (last few interactions in the simulation):
    {recent_interactions if recent_interactions else "No recent interactions logged yet."}

    **Task:** Generate a realistic, concise (2-4 sentences) diplomatic message from {speaker} to {receiver}.
    * **Reflect:** Your message must reflect {speaker}'s interests, strengths, and weaknesses.
    * **Acknowledge:** Consider {receiver}'s likely interests and position.
    * **Address:** Relate directly to the {scenario} crisis and its key issues.
    * **Style:** Adhere strictly to the assigned {negotiation_style} (Cooperative: seek win-win, build trust; Competitive: assert demands, use leverage; Mixed: blend approaches, perhaps conditional offers).
    * **Progress:** Your message should logically follow the negotiation turn and recent context (if any). Avoid generic statements. Be specific if possible (e.g., propose a specific action, request specific information, state a clear position).
    * **Format:** Output only the diplomatic message text, without any preamble or explanation.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Draft the diplomatic message from {speaker} to {receiver} for turn {turn}."}
    ]

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model=MODEL,
            temperature=0.75, # Adjust for creativity vs. predictability
            max_tokens=200,
            stop=None # Allow model to complete naturally
        )
        reply = chat_completion.choices[0].message.content
        # Clean up potential markdown or quotes if model adds them
        reply = reply.strip().replace('"', '').replace("```", "").strip()
        return reply if reply else f"(Error: Empty response from model for {speaker} to {receiver})"
    except Exception as e:
        st.error(f"Groq API Error during message generation: {e}", icon="⚡")
        print(f"Groq Error Details: {e}") # Log details for debugging
        return f"(Error: Could not generate message for {speaker} to {receiver})"

def determine_outcome(speaker, receiver, proposal, negotiation_style, metrics):
    # Base probability influenced by peace index
    base_prob = 0.2 + (metrics["Peace Index"] * 0.4)

    # Adjust based on negotiation style
    if negotiation_style == "Cooperative":
        base_prob += 0.15
    elif negotiation_style == "Competitive":
        base_prob -= 0.10
    # Mixed style has no direct base adjustment

    # Check alignment with receiver's interests (simple keyword check)
    receiver_interests = COUNTRY_PROFILES.get(receiver, {}).get("interests", [])
    interest_match_score = 0
    proposal_lower = proposal.lower() if proposal else "" # Handle potential None proposal
    if proposal_lower:
        for interest in receiver_interests:
            # Basic check, could be enhanced with NLP
            if interest.lower().split(' ')[0] in proposal_lower: # Check first word of interest
                 interest_match_score += 0.05
    base_prob += min(interest_match_score, 0.15) # Cap bonus from interest match

    # Add randomness
    base_prob += random.uniform(-0.1, 0.1)

    # Clamp probability between 5% and 95%
    acceptance_prob = max(0.05, min(0.95, base_prob))

    # Determine outcome
    if random.random() < acceptance_prob:
        return "Accepted ✅", "The proposal aligns sufficiently with mutual or national interests at this time."
    else:
        # Provide more context-specific rejection reasons
        reasons = [
            f"Insufficient alignment with {receiver}'s core interests.",
            "Proposal viewed as unbalanced or lacking reciprocity.",
            f"Domestic political constraints in {receiver} prevent acceptance.",
            "Requires further clarification or concessions.",
            f"Trust levels between {speaker} and {receiver} remain too low.",
            "Waiting for a more opportune moment or a better offer."
        ]
        if negotiation_style == "Competitive":
            reasons.append(f"{receiver} perceives the proposal as an attempt to gain unilateral advantage.")
        if metrics["Peace Index"] < 0.4:
             reasons.append("High global tension makes new commitments risky.")
        # Add a reason if the proposal was empty/error
        if not proposal_lower:
            reasons.append("Proposal was unclear or missing.")

        return "Rejected ❌", random.choice(reasons)

def update_metrics(metrics, outcome, scenario):
    # Get current state safely
    severity_factor = st.session_state.get('crisis_severity', 5) / 10.0
    peace_index = metrics.get("Peace Index", 0.5) # Default if missing

    # Update Peace Index
    peace_change = 0
    if outcome == "Accepted ✅":
        # Increase peace more if already low, less if high; reduced by severity
        peace_change = random.uniform(0.01, 0.04) * (1.2 - peace_index) * (1.1 - severity_factor)
    else: # Rejected
        # Decrease peace more if already high, less if low; amplified by severity
        peace_change = -random.uniform(0.01, 0.03) * (0.8 + peace_index) * (1 + severity_factor)
    metrics["Peace Index"] = max(0.05, min(0.95, peace_index + peace_change))

    # Scenario-specific updates (using .get for safety)
    if "Climate" in scenario and "Carbon Emissions (Gt)" in metrics:
        # Emissions tend to rise with low peace, decrease slightly with agreements
        emission_change = random.uniform(-0.1, 0.5) + (0.6 - peace_index) * 0.4 - (0.1 if outcome == "Accepted ✅" else -0.05)
        metrics["Carbon Emissions (Gt)"] = max(10, metrics.get("Carbon Emissions (Gt)", 35) + emission_change)

    elif "Energy" in scenario and "Energy Stability Index" in metrics:
        # Stability improves with peace/agreements, degrades otherwise
        stability_change = (peace_index - 0.5) * 0.05 + random.uniform(-0.03, 0.03) + (0.03 if outcome == "Accepted ✅" else -0.04)
        metrics["Energy Stability Index"] = max(0.1, min(0.9, metrics.get("Energy Stability Index", 0.6) + stability_change))

    elif "Refugee" in scenario and "Refugee Migration (M)" in metrics:
        # Refugees decrease with agreements (more if peace is high), increase otherwise
         if outcome == "Accepted ✅":
             decrease = random.randint(1, 3) * (1 + int(peace_index > 0.6))
             metrics["Refugee Migration (M)"] = max(0, metrics.get("Refugee Migration (M)", 20) - decrease)
         else:
             # Slight random increase on rejection
             metrics["Refugee Migration (M)"] = max(0, metrics.get("Refugee Migration (M)", 20) + random.randint(0, 1))

    # Economic Growth Update
    if "Economic Growth (%)" in metrics:
        # Growth hurt by low peace & severity, helped slightly by agreements
        base_growth_factor = (peace_index - 0.55) * 0.3 - severity_factor * 0.15
        outcome_impact = 0.06 if outcome == "Accepted ✅" else -0.04
        random_fluct = random.uniform(-0.1, 0.1)
        current_growth = metrics.get("Economic Growth (%)", 2.5)
        metrics["Economic Growth (%)"] = round(max(-15.0, current_growth + base_growth_factor + outcome_impact + random_fluct), 1)

    # Ensure default values if keys were somehow missing (less likely now)
    metrics.setdefault("Carbon Emissions (Gt)", 35.0) # Ensure float
    metrics.setdefault("Refugee Migration (M)", 20)
    metrics.setdefault("Energy Stability Index", 0.6) # Ensure float
    metrics.setdefault("Economic Growth (%)", 2.5) # Ensure float

    return metrics

def generate_country_card(country):
    profile = COUNTRY_PROFILES.get(country)
    if not profile:
        return "<p><em>Profile not available.</em></p>"

    # Simple HTML card for country profile (keeping this as it's simple)
    card = f"""
    <div style='padding: 1rem; margin-bottom: 1rem; border-radius: 8px;
                background-color: #ffffff; border-left: 5px solid {profile.get("color", "#cccccc")};
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
        <h4 style='margin-bottom: 0.5rem; color: {profile.get("color", "#333333")};'>{country}</h4>
        <p style='font-size: 0.9em; margin-bottom: 0.3rem;'><strong>Strengths:</strong> {', '.join(profile.get('strengths', ['N/A']))}</p>
        <p style='font-size: 0.9em; margin-bottom: 0.3rem;'><strong>Weaknesses:</strong> {', '.join(profile.get('weaknesses', ['N/A']))}</p>
        <p style='font-size: 0.9em; margin-bottom: 0.1rem;'><strong>Interests:</strong> {', '.join(profile.get('interests', ['N/A']))}</p>
    </div>
    """
    return card

# --- UI Layout ---
st.title("🌐 PoliBot Pro: Advanced Crisis Negotiation Simulator")

col_main, col_sidebar = st.columns([3, 1]) # Main content area wider

with col_sidebar:
    st.header("🛠️ Simulation Configuration")

    # --- Scenario Selection ---
    if 'selected_scenario' not in st.session_state:
        st.session_state.selected_scenario = list(SCENARIO_DETAILS.keys())[0]
    # Use the current state value in selectbox, update state on change
    st.session_state.selected_scenario = st.selectbox(
        "🌍 Crisis Scenario",
        options=list(SCENARIO_DETAILS.keys()),
        index=list(SCENARIO_DETAILS.keys()).index(st.session_state.selected_scenario),
        key="scenario_select" # Key helps maintain state across reruns
    )
    scenario = st.session_state.selected_scenario # Get current value

    # Display scenario details in an expander
    with st.expander("Scenario Details", expanded=False):
        details = SCENARIO_DETAILS[scenario]
        st.write(f"**Description:** {details['description']}")
        st.write(f"**Key Issues:** {', '.join(details['key_issues'])}")
        st.write(f"**Historical Context:** {details['historical']}")

    # --- Nation Selection ---
    if 'selected_nations' not in st.session_state:
        # Default selection
        st.session_state.selected_nations = ["USA", "China", "India", "Germany"]
    # Use current state value in multiselect, update state on change
    st.session_state.selected_nations = st.multiselect(
        "🌎 Participating Nations",
        options=list(COUNTRY_PROFILES.keys()),
        default=st.session_state.selected_nations,
        key="nation_select" # Key for state persistence
    )
    nations = st.session_state.selected_nations # Get current value

    # --- Simulation Speed Slider ---
    if 'sim_speed' not in st.session_state:
        st.session_state.sim_speed = 1.0 # Default speed
    # Ensure sim_speed is float before passing to slider
    current_speed = st.session_state.get('sim_speed', 1.0)
    if not isinstance(current_speed, (int, float)):
        st.warning("Resetting simulation speed due to invalid type.", icon="⚠️")
        current_speed = 1.0
        st.session_state.sim_speed = current_speed
    # Update state based on slider interaction
    st.session_state.sim_speed = st.slider(
        "⏱️ Simulation Speed (s/turn)",
        min_value=0.0, max_value=5.0,
        value=float(current_speed), # Pass current valid float value
        step=0.1,
        key="speed_slider" # Key for state
    )
    speed = st.session_state.sim_speed # Get current value

    # --- Number of Turns ---
    if 'num_turns' not in st.session_state:
        st.session_state.num_turns = 15 # Default turns
    # Update state based on number input
    st.session_state.num_turns = st.number_input(
        "🔄 Number of Turns",
        min_value=5, max_value=50,
        value=st.session_state.num_turns,
        step=1,
        key="turns_input" # Key for state
    )
    num_turns = st.session_state.num_turns # Get current value

    # --- Negotiation Style ---
    style_options = ["Cooperative", "Competitive", "Mixed"]
    if 'negotiation_style' not in st.session_state or st.session_state.negotiation_style not in style_options:
        st.session_state.negotiation_style = "Mixed" # Default/fallback
    # Update state based on radio button selection
    st.session_state.negotiation_style = st.radio(
        "🗣️ Overall Negotiation Style",
        options=style_options,
        index=style_options.index(st.session_state.negotiation_style),
        key="style_radio" # Key for state
    )
    negotiation_style = st.session_state.negotiation_style # Get current value

    # --- Advanced Options ---
    # Initialize state variables if they don't exist
    if 'advanced_options_checked' not in st.session_state:
        st.session_state.advanced_options_checked = False
    if 'crisis_severity' not in st.session_state:
        st.session_state.crisis_severity = 5
    if 'initial_peace' not in st.session_state:
        st.session_state.initial_peace = 0.5

    # Checkbox to show/hide advanced options
    st.session_state.advanced_options_checked = st.checkbox(
        "Show Advanced Options",
        value=st.session_state.advanced_options_checked,
        key="advanced_checkbox" # Key for state
        )
    # Display sliders if checkbox is checked
    if st.session_state.advanced_options_checked:
        st.session_state.crisis_severity = st.slider(
            "🔥 Crisis Severity", 1, 10, st.session_state.crisis_severity,
            key="severity_slider" # Key for state
            )
        st.session_state.initial_peace = st.slider(
            "🕊️ Initial Peace Index", 0.1, 0.9, st.session_state.initial_peace, 0.05,
            key="peace_slider" # Key for state
            )

    # --- Start Button ---
    start_simulation = st.button("🚀 Start Simulation", type="primary", use_container_width=True, key="start_button")

    # --- Country Profiles Display ---
    st.markdown("---")
    st.markdown("### Selected Country Profiles")
    if nations:
        for country in nations:
            # Display profile card for each selected nation
            st.markdown(generate_country_card(country), unsafe_allow_html=True)
    else:
        st.warning("Please select at least two nations.")


with col_main:
    st.markdown("---")
    st.subheader("📊 Global Metrics Dashboard")

    # --- Initialize Metrics State ---
    # Reset metrics only if the start button is pressed OR if they don't exist yet
    if 'metrics' not in st.session_state or start_simulation:
        # Use advanced options if checked, otherwise defaults
        init_peace = st.session_state.initial_peace if st.session_state.advanced_options_checked else 0.5
        # Store the initial state separately for comparison
        st.session_state.metrics_initial = {
            "Peace Index": init_peace,
            "Carbon Emissions (Gt)": 35.0, # Use float
            "Refugee Migration (M)": 20, # Use int
            "Energy Stability Index": 0.6, # Use float
            "Economic Growth (%)": 2.5 # Use float
        }
        # Copy initial state to the current metrics state
        st.session_state.metrics = st.session_state.metrics_initial.copy()

    # --- Metric Display Area ---
    metrics_container = st.container()
    # Get keys safely, providing an empty dict if 'metrics' doesn't exist
    metric_keys = list(st.session_state.get('metrics', {}).keys())
    metrics_placeholders = {}
    num_metrics = len(metric_keys)
    cols_per_row = 4 # Adjust layout as needed
    num_rows = (num_metrics + cols_per_row - 1) // cols_per_row

    with metrics_container:
        # Create placeholders in columns dynamically
        placeholder_rows = [st.columns(cols_per_row) for _ in range(num_rows)]
        # Assign placeholders to keys
        for i, key in enumerate(metric_keys):
            row_index = i // cols_per_row
            col_index = i % cols_per_row
            # Assign the empty placeholder from the correct column
            metrics_placeholders[key] = placeholder_rows[row_index][col_index].empty()

    # Function to update the metric display placeholders
    def display_metrics(metrics_data):
        # Safely get initial metrics, default to current if initial is missing
        initial_metrics = st.session_state.get('metrics_initial', metrics_data)

        # Helper to safely get values and calculate deltas
        def get_metric_values(key, current_data, initial_data, default=0):
            current_val = current_data.get(key, default)
            initial_val = initial_data.get(key, default)
            # Ensure consistent types for subtraction
            try:
                delta = float(current_val) - float(initial_val)
            except (ValueError, TypeError):
                delta = 0 # Handle cases where conversion fails
            return current_val, delta

        # Update each metric placeholder if it exists
        if "Peace Index" in metrics_placeholders:
             val, delta = get_metric_values("Peace Index", metrics_data, initial_metrics, 0.5)
             metrics_placeholders["Peace Index"].metric("🕊️ Peace Index", f"{val:.2f}", f"{delta:+.2f}",
                                                        delta_color="normal" if delta >= -0.001 else "inverse")
        if "Carbon Emissions (Gt)" in metrics_placeholders:
            val, delta = get_metric_values("Carbon Emissions (Gt)", metrics_data, initial_metrics, 35.0)
            metrics_placeholders["Carbon Emissions (Gt)"].metric("💨 CO₂ Emissions (Gt)", f"{val:.1f}", f"{delta:+.1f}", delta_color="inverse") # Higher is worse
        if "Refugee Migration (M)" in metrics_placeholders:
            val, delta = get_metric_values("Refugee Migration (M)", metrics_data, initial_metrics, 20)
            metrics_placeholders["Refugee Migration (M)"].metric("🚶 Refugees (M)", f"{int(val):,}", f"{int(delta):+,}", delta_color="inverse") # Higher is worse
        if "Energy Stability Index" in metrics_placeholders:
             val, delta = get_metric_values("Energy Stability Index", metrics_data, initial_metrics, 0.6)
             metrics_placeholders["Energy Stability Index"].metric("⚡ Energy Stability", f"{val:.2f}", f"{delta:+.2f}",
                                                                    delta_color="normal" if delta >= -0.001 else "inverse")
        if "Economic Growth (%)" in metrics_placeholders:
            val, delta = get_metric_values("Economic Growth (%)", metrics_data, initial_metrics, 2.5)
            metrics_placeholders["Economic Growth (%)"].metric("📈 Econ Growth (%)", f"{val:.1f}%", f"{delta:+.1f}%",
                                                                delta_color="normal" if delta >= -0.001 else "inverse")

    # Initial display of metrics when script runs
    display_metrics(st.session_state.get('metrics', {})) # Use .get for safety

    # Placeholders for dynamic updates during simulation
    progress_bar_placeholder = st.empty()
    status_text_placeholder = st.empty() # For showing turn status message

    # --- Main Content Areas ---
    st.markdown("---")
    st.subheader("🗣️ Negotiation Log")
    # Use a container with a fixed height and scrollbar for the log
    negotiation_log_container = st.container(height=300) # Adjust height as needed
    negotiation_log_container.markdown("_(Simulation log will appear here...)_", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📜 Signed Treaties & Agreements")
    # Use a container with a fixed height and scrollbar for treaties
    treaty_container = st.container(height=300) # Adjust height as needed
    treaty_container.markdown("_(Signed agreements will appear here...)_", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🌐 Diplomatic Network")
    graph_placeholder = st.empty()
    graph_placeholder.markdown("_(Diplomatic network graph will appear here...)_", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📄 Simulation Analytics")
    # This placeholder will be filled with Streamlit elements at the end
    report_placeholder = st.container() # Use a container
    report_placeholder.markdown("_(Summary report will appear here after simulation...)_") # Initial text

    # --- Initialize Simulation State Lists ---
    # Initialize only if they don't exist in the session state
    if 'simulation_dialogue' not in st.session_state:
        st.session_state.simulation_dialogue = []
    if 'simulation_treaties' not in st.session_state:
        st.session_state.simulation_treaties = []
    if 'simulation_relationships' not in st.session_state:
        st.session_state.simulation_relationships = {}
    if 'simulation_graph' not in st.session_state:
         st.session_state.simulation_graph = nx.Graph()


# --- Simulation Logic ---
if start_simulation:
    # Validate nation selection
    if len(nations) < 2:
        st.error("❌ Please select at least two nations to run the simulation.")
    else:
        # --- Reset and Initialize State for a New Simulation ---
        # Clearing the dialogue and treaties lists to prevent duplicates between runs
        st.session_state.simulation_dialogue = []
        st.session_state.simulation_treaties = []
        # Reset metrics to the initial state defined earlier
        st.session_state.metrics = st.session_state.metrics_initial.copy()
        display_metrics(st.session_state.metrics) # Update dashboard to initial state

        # Clear dynamic content areas visually
        negotiation_log_container.empty().markdown("_(Simulation running...)_", unsafe_allow_html=True)
        treaty_container.empty().markdown("_(Simulation running...)_", unsafe_allow_html=True)
        graph_placeholder.empty().markdown("_(Simulation running...)_", unsafe_allow_html=True)
        report_placeholder.empty().markdown("_(Simulation running...)_") # Clear report area
        status_text_placeholder.empty()

        # Initialize graph and relationships for this run
        G = nx.Graph()
        G.add_nodes_from(nations)
        st.session_state.simulation_graph = G # Store graph in state
        # Initialize relationships with 0 (neutral)
        relationships = {n: {m: 0.0 for m in nations if m != n} for n in nations}
        st.session_state.simulation_relationships = relationships

        # Setup progress bar and status text
        progress_bar = progress_bar_placeholder.progress(0, text="Simulation Starting...")
        status_text = status_text_placeholder.text("Initializing Simulation...")

        # --- Simulation Loop ---
        try:
            metrics = st.session_state.metrics # Local reference for updates

            for turn in range(1, num_turns + 1):
                status_text.text(f"Processing Turn {turn}/{num_turns}...")
                progress = int((turn / num_turns) * 100)
                progress_bar.progress(progress, text=f"Simulation Progress: Turn {turn}/{num_turns}")

                # Select two distinct nations randomly for interaction
                speaker, receiver = random.sample(nations, 2)

                # Get recent dialogue for context (only text part)
                # Using list slicing [::-1][:3] to get the last 3 elements in reverse order
                # which is equivalent to the first 3 if prepended. Reversing before slicing
                # is safer to get the *most recent* interactions.
                context_log = [
                    entry.split("<em>Proposal:</em>")[1].split("<br>")[0].replace('"', '').strip()
                    for entry in st.session_state.simulation_dialogue[::-1][:3] # Get the text from the 3 most recent logs
                    if isinstance(entry, str) and "<em>Proposal:</em>" in entry
                ]
                # Reverse the context_log back to chronological order for LLM
                context_log.reverse()


                # Generate the diplomatic proposal message
                proposal = generate_negotiation_message(
                    speaker, receiver, scenario, negotiation_style, turn, context_log
                )

                # Determine the outcome of the proposal
                outcome, reason = determine_outcome(
                    speaker, receiver, proposal, negotiation_style, metrics
                )

                # Update global metrics based on the outcome
                metrics = update_metrics(metrics, outcome, scenario)
                st.session_state.metrics = metrics # Save updated metrics back to state
                display_metrics(metrics) # Update dashboard display

                # Log the interaction
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_entry_html = f"""
                <div class="log-entry">
                    <strong>Turn {turn} • {timestamp}</strong> | <strong>{speaker} → {receiver}</strong><br>
                    <em>Proposal:</em> "{proposal}"<br>
                    <strong>Outcome: {outcome}</strong> <em>({reason})</em>
                </div>
                """
                # Prepend new log entry to the list for newest-first display
                st.session_state.simulation_dialogue.insert(0, log_entry_html)

                # Update relationships and graph based on outcome
                relationship_change = 0.0
                current_weight = G.get_edge_data(speaker, receiver, default={'weight': 0.0})['weight']

                if outcome == "Accepted ✅":
                    relationship_change = 0.2 # Smaller increment for acceptance
                    # Add treaty only if proposal is valid
                    if proposal and not proposal.startswith("(Error:"):
                        st.session_state.simulation_treaties.insert(0, (speaker, receiver, turn, proposal)) # Prepend
                else: # Rejected
                    relationship_change = -0.1 # Smaller decrement for rejection

                # Update edge weight, clamping between -1.0 and +1.0
                new_weight = max(-1.0, min(1.0, current_weight + relationship_change))
                G.add_edge(speaker, receiver, weight=new_weight) # Updates or adds edge

                # --- Update UI (Log & Treaties) ---
                # Display the latest log entries (e.g., last 10)
                with negotiation_log_container: # Use the container
                    # Clear previous display
                    negotiation_log_container.empty()
                    # Join the first N entries (which are the newest)
                    log_display_html = "".join(st.session_state.simulation_dialogue[:10])
                    st.markdown(log_display_html, unsafe_allow_html=True)

                # Display the latest treaties using Streamlit components
                with treaty_container:
                    # Clear the container before writing to avoid appending previous turn's display
                    treaty_container.empty()
                    if st.session_state.simulation_treaties:
                        st.subheader("Recent Agreements")
                        # Show newest 5 treaties
                        for treaty in st.session_state.simulation_treaties[:5]:
                            # Use st.info to display each treaty
                            st.info(f"""
**{treaty[0]} ↔ {treaty[1]}** (Turn {treaty[2]})

Proposal: "{treaty[3]}"
""")
                    else:
                        st.markdown("<em>No treaties signed yet.</em>", unsafe_allow_html=True)


                # --- Update Graph ---
                if G.number_of_nodes() > 0:
                    plt.style.use('seaborn-v0_8-whitegrid') # Use a clean style
                    plt.figure(figsize=(10, 7)) # Adjust figure size
                    try:
                        # Use a layout algorithm that handles weights if available and sensible
                        pos = nx.kamada_kawai_layout(G, weight=None) # Kamada-Kawai often looks good
                    except Exception:
                        pos = nx.spring_layout(G, seed=42, k=0.8) # Fallback layout

                    node_colors = [COUNTRY_PROFILES.get(n, {}).get("color", "#cccccc") for n in G.nodes()]
                    # Node size based on degree (number of connections)
                    node_sizes = [1000 + G.degree(n) * 300 for n in G.nodes()]

                    # Edge properties based on weight
                    edge_weights = [G[u][v].get('weight', 0) for u, v in G.edges()]
                    # Normalize weights for width/color intensity (0 to 1 absolute)
                    max_abs_w = max(abs(w) for w in edge_weights) if edge_weights else 1.0
                    max_abs_w = max(max_abs_w, 0.1) # Avoid division by zero or tiny numbers

                    # Width based on absolute weight magnitude
                    edge_widths = [1 + (abs(w) / max_abs_w * 4) for w in edge_weights]
                    # Color based on sign (positive=green, negative=red)
                    edge_colors = ['#2ca02c' if w > 0 else '#d62728' if w < 0 else '#aaaaaa' for w in edge_weights]
                    # Alpha based on absolute weight magnitude
                    edge_alphas = [0.3 + (abs(w) / max_abs_w * 0.6) for w in edge_weights]


                    # Draw nodes
                    nx.draw_networkx_nodes( G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9, linewidths=1.0, edgecolors='grey')
                    # Draw edges
                    nx.draw_networkx_edges( G, pos, width=edge_widths, edge_color=edge_colors, alpha=edge_alphas, connectionstyle='arc3,rad=0.05') # Slight curve
                    # Draw labels (without background box)
                    nx.draw_networkx_labels( G, pos, font_size=9, font_weight="bold", font_color='black')

                    plt.title(f"Diplomatic Network (Turn {turn})", fontsize=16)
                    plt.axis("off") # Hide axes
                    plt.tight_layout() # Adjust layout
                    buf = io.BytesIO() # Save to buffer
                    plt.savefig(buf, format="png", dpi=130, bbox_inches='tight')
                    graph_placeholder.image(buf) # Display image from buffer
                    plt.close() # Close plot to free memory
                else:
                    graph_placeholder.markdown("_(Graph cannot be drawn - no nations selected)_")

                # Pause between turns if speed > 0
                if speed > 0:
                    time.sleep(speed)

            # --- Simulation End & Reporting ---
            status_text.text("Simulation Complete.")
            progress_bar.progress(100, text="Simulation Complete.")
            st.success("✅ Simulation Complete!")

            # Retrieve final state
            final_metrics = st.session_state.metrics
            initial_metrics = st.session_state.metrics_initial
            final_G = st.session_state.simulation_graph

            # Calculate final report metrics
            most_active, least_active, strongest_pair_text = "N/A", "N/A", "N/A"
            final_density, num_components = 0.0, 0

            if final_G.number_of_nodes() > 0:
                degrees = list(final_G.degree())
                if degrees:
                    # Find node with max/min degree
                    most_active = max(degrees, key=lambda x: x[1])[0]
                    least_active = min(degrees, key=lambda x: x[1])[0]
                # Calculate network density and components
                final_density = nx.density(final_G)
                if final_G.number_of_edges() > 0: # Need edges for components
                     num_components = nx.number_connected_components(final_G)
                else:
                     num_components = final_G.number_of_nodes() # Each node is a component

            # Find strongest positive relationship
            strongest_pair_text = "N/A (No positive relationships)"
            if final_G.number_of_edges() > 0:
                edge_weights = [( (u, v), final_G[u][v].get('weight', 0) ) for u, v in final_G.edges()]
                positive_weights = [(pair, w) for pair, w in edge_weights if w > 0]
                if positive_weights:
                    strongest_data = max(positive_weights, key=lambda x: x[1])
                    strongest_pair_text = f"{strongest_data[0][0]} ↔ {strongest_data[0][1]} (Weight: {strongest_data[1]:.2f})" # Use .2f for weight

            # --- Generate Final Summary Report using Streamlit elements ---
            with report_placeholder: # Use the container defined earlier
                st.subheader("Simulation Summary Report") # Changed from h3
                st.markdown(f"**Scenario:** {scenario}")
                st.markdown(f"**Duration:** {num_turns} turns")
                st.markdown(f"**Agreements Reached:** {len(st.session_state.get('simulation_treaties', []))}")
                st.markdown(f"**Network Density:** {final_density:.3f} | **Components:** {num_components}")

                st.subheader("Key Observations") # Changed from h4
                st.markdown(f"* Most active nation (highest degree): **{most_active}**")
                st.markdown(f"* Strongest positive relationship (highest edge weight): **{strongest_pair_text}**")
                st.markdown(f"* Nation with lowest degree: **{least_active}**")

                st.subheader("Final Metrics (vs Initial)") # Changed from h4
                # Using markdown with f-strings for formatted output
                fm_peace = final_metrics.get('Peace Index', 0)
                im_peace = initial_metrics.get('Peace Index', 0)
                st.markdown(f"* 🕊️ Peace Index: **{fm_peace:.2f}** ({fm_peace - im_peace:+.2f})")

                fm_co2 = final_metrics.get('Carbon Emissions (Gt)', 0)
                im_co2 = initial_metrics.get('Carbon Emissions (Gt)', 0)
                st.markdown(f"* 💨 CO₂ Emissions (Gt): **{fm_co2:.1f}** ({fm_co2 - im_co2:+.1f})")

                fm_ref = final_metrics.get('Refugee Migration (M)', 0)
                im_ref = initial_metrics.get('Refugee Migration (M)', 0)
                st.markdown(f"* 🚶 Refugees (M): **{int(fm_ref):,}** ({int(fm_ref - im_ref):+,})")

                fm_energy = final_metrics.get('Energy Stability Index', 0)
                im_energy = initial_metrics.get('Energy Stability Index', 0)
                st.markdown(f"* ⚡ Energy Stability: **{fm_energy:.2f}** ({fm_energy - im_energy:+.2f})")

                fm_econ = final_metrics.get('Economic Growth (%)', 0)
                im_econ = initial_metrics.get('Economic Growth (%)', 0)
                st.markdown(f"* 📈 Econ Growth (%): **{fm_econ:.1f}%** ({fm_econ - im_econ:+.1f}%)")


            # --- Download Button (Transcript Only) ---
            st.markdown("---")
            st.subheader("📥 Download Results")

            # Prepare transcript data
            transcript_data = f"PoliBot Pro Simulation Transcript\nScenario: {scenario}\nTurns: {num_turns}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\n"
            # Convert HTML log entries to plain text for download
            plain_log_entries = []
            for entry in reversed(st.session_state.simulation_dialogue): # Reverse back to chronological order
                if isinstance(entry, str):
                    # Basic text conversion from the HTML log entry
                    text_entry = entry.replace('<div class="log-entry">', '')
                    text_entry = text_entry.replace('</div>', '')
                    text_entry = text_entry.replace('<br>', '\n')
                    text_entry = text_entry.replace('<strong>', '') # Remove strong tags
                    text_entry = text_entry.replace('</strong>', '')
                    text_entry = text_entry.replace('<em>', '') # Remove emphasis tags
                    text_entry = text_entry.replace('</em>', '')
                    plain_log_entries.append(text_entry.strip())
            transcript_data += "\n\n---\n\n".join(plain_log_entries)

            # Single download button for the transcript
            st.download_button(
                label="📄 Download Full Transcript (.txt)",
                data=transcript_data,
                file_name=f"PoliBot_Transcript_{scenario.split(' ')[0]}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True, # Make button wide
                key="dl_transcript"
            )

        except Exception as sim_e:
             # Catch and display errors during the simulation loop
             st.error(f"An error occurred during the simulation: {sim_e}", icon="🔥")
             # Log the full traceback to console/terminal for detailed debugging
             print("--- Simulation Error Traceback ---")
             traceback.print_exc()
             print("---------------------------------")
             # Also display traceback in Streamlit app for user visibility
             st.exception(sim_e)
        finally:
             # Ensure progress bar and status text are cleared regardless of success/failure
             progress_bar_placeholder.empty()
             status_text_placeholder.empty()


# --- Footer ---
st.markdown("---")
st.caption("PoliBot Pro v1.4 - Global Crisis Negotiation Simulator")
