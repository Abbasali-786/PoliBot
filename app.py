import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import random
import time
from groq import Groq
import io
from datetime import datetime
import traceback
import re

st.set_page_config(
    page_title="🌐 PoliBot: Crisis Simulation",
    layout="wide",
    page_icon="🤖",
    initial_sidebar_state="expanded"
)

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
    .log-entry {
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        border-radius: 8px;
        background-color: #f8f9fa;
        border-left: 4px solid #6c757d;
        font-size: 0.95em;
    }
    .log-entry.intent-deal { border-left-color: #28a745; }
    .log-entry.intent-respond { border-left-color: #ffc107; }
    .log-entry.intent-comment { border-left-color: #17a2b8; }
    .log-entry.intent-alliance { border-left-color: #007bff; }
    .log-entry.intent-assist { border-left-color: #fd7e14; }
    .log-entry.intent-concern { border-left-color: #dc3545; }
    .log-entry.intent-decline { border-left-color: #6c757d; }

    h3 {
       color: #0056b3;
       border-bottom: 2px solid #007bff;
       padding-bottom: 0.3rem;
       margin-bottom: 1rem;
    }
    h4 {
        color: #333;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

try:
    groq_api_key = st.secrets.get("GROQ_API_KEY", None)
    if not groq_api_key:
        st.error("Groq API Key not found in Streamlit secrets (GROQ_API_KEY). Please add it.", icon="🚨")
        st.stop()

    groq_client = Groq(api_key=groq_api_key)
    groq_client.models.list()
except Exception as e:
    st.error(f"Failed to initialize Groq client: {e}. Check API Key and network connection.", icon="🚨")
    st.stop()

MODEL = "llama3-70b-8192"

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
    "Pakistan": {
        "strengths": ["Strategic Location", "Nuclear Capability", "Large Population", "Military Experience"],
        "weaknesses": ["Economic Volatility", "Political Instability", "Water Scarcity", "Regional Security Challenges"],
        "interests": ["National Security", "Economic Stability", "Kashmir Issue", "Regional Influence", "Counter-terrorism"],
        "color": "#006600"
    },
    "EU": {
        "strengths": ["Large Single Market", "Regulatory Power", "Diplomatic Network", "Economic Aid"],
        "weaknesses": ["Internal Divisions", "Bureaucracy", "Military Dependence (on members/NATO)", "Demographic Challenges"],
        "interests": ["European Integration", "Economic Prosperity", "Climate Action", "Rule of Law", "Neighborhood Stability"],
        "color": "#003399"
    }
}

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

class CountryAgent:
    def __init__(self, name, profile, groq_client):
        self.name = name
        self.profile = profile
        self.groq = groq_client
        self.memory = []

    def remember(self, log_entry):
        self.memory.append(log_entry)
        if len(self.memory) > 10:
            self.memory.pop(0)

    def act(self, scenario, scenario_details, turn, all_nations):
        memory_log = '\n'.join(self.memory[-5:]) if self.memory else "No recent memory."

        other_nations = [n for n in all_nations if n != self.name]
        target_options = ", ".join(other_nations) + ", GLOBAL"

        prompt = f"""
You are the official diplomatic representative (AI agent) of the country *{self.name}*.

Your job is to *negotiate, strategize, and act in the best interest of your country* during an international crisis simulation. You must be proactive, thoughtful, and aligned with national objectives.

---

## 🌍 Current Global Crisis:
*{scenario}*
- Description: {scenario_details['description']}
- Key Issues: {', '.join(scenario_details['key_issues'])}
- Historical Precedents: {scenario_details['historical']}

---

## 🏧 Your Country Profile ({self.name}):
- Strengths: {', '.join(self.profile.get('strengths', ['N/A']))}
- Weaknesses: {', '.join(self.profile.get('weaknesses', ['N/A']))}
- National Interests: {', '.join(self.profile.get('interests', ['N/A']))}

---

## 🎯 Your Current Strategic Mission (as of Turn {turn}):
Analyze recent events and interactions. Based on your memory and position, choose your next diplomatic action.

Your options for [Intent]:
1. Propose a deal (Offer a specific exchange or agreement)
2. Respond (React to a previous proposal or action directed at you - check memory)
3. Comment (Make a statement about the crisis or another nation's actions)
4. Build alliances (Suggest cooperation or partnership)
5. Request assistance (Ask for specific aid or support)
6. Raise a global concern (Highlight a major issue needing collective attention)
7. Decline to act (Pass the turn if no strategic move is beneficial)

Your options for [Target]:
- Choose one specific country from: {target_options}
- Choose 'GLOBAL' for general statements or concerns.

---

## 🧠 Recent Memory (Relevant events from last 5 turns):
{memory_log}

---

## 🗣 Output Format (MUST follow this structure EXACTLY):

[Intent]: (Choose ONE from the 7 options above)
[Target]: (Choose ONE from the target options list)
[Message]: (Your diplomatic message - 2-4 concise sentences. Be specific, reflect your interests, and relate to the crisis or memory.)


---
Example Output:
[Intent]: Propose a deal
[Target]: USA
[Message]: We propose a joint investment in climate-resilient agriculture technology. This aligns with our shared food security interests given the current crisis.

---

Remember:
- Reflect your national agenda ({', '.join(self.profile.get('interests', ['N/A']))}).
- Consider other countries' likely priorities based on the crisis.
- Act decisively to advance your interests or manage the crisis.
- Respond ONLY with the specified format. Do not add explanations or greetings.
"""

        try:
            completion = self.groq.chat.completions.create(
                model=MODEL,
                messages=[{"role": "system", "content": prompt}],
                temperature=0.75,
                max_tokens=250,
                stop=None
            )
            action_text = completion.choices[0].message.content.strip()
            if "[Intent]:" in action_text and "[Target]:" in action_text and "[Message]:" in action_text:
                return action_text
            else:
                print(f"Warning: Malformed response from {self.name}: {action_text}")
                return f"[Intent]: Decline to act\n[Target]: GLOBAL\n[Message]: (Agent decided to observe this turn due to unclear instructions or malformed response template)"

        except Exception as e:
            print(f"Error during API call for {self.name}: {e}")
            traceback.print_exc()
            return f"[Intent]: Decline to act\n[Target]: GLOBAL\n[Message]: (Technical difficulties prevented action: {e})"


def parse_action(action_text):
    intent, target, message = None, None, None
    try:
        intent_match = re.search(r"\[Intent\]:\s*(.*)", action_text, re.IGNORECASE)
        target_match = re.search(r"\[Target\]:\s*(.*)", action_text, re.IGNORECASE)
        message_match = re.search(r"\[Message\]:\s*(.*)", action_text, re.IGNORECASE | re.DOTALL)

        if intent_match:
            intent = intent_match.group(1).strip()
        if target_match:
            target = target_match.group(1).strip()
        if message_match:
            message = message_match.group(1).strip()

        valid_intents = ["Propose a deal", "Respond", "Comment", "Build alliances",
                         "Request assistance", "Raise a global concern", "Decline to act"]
        if intent not in valid_intents:
             print(f"Warning: Invalid intent parsed: '{intent}'")

        return intent, target, message

    except Exception as e:
        print(f"Error parsing action text: {e}\nRaw text: {action_text}")
        return None, None, None


def determine_action_impact(agent_name, intent, target, message, metrics, all_nations):
    impact_description = "Action noted."
    relationship_change = 0.0
    target_for_relation_change = None

    peace_index = metrics.get("Peace Index", 0.5)
    severity_factor = st.session_state.get('crisis_severity', 5) / 10.0
    peace_change = 0

    if target and target != "GLOBAL" and target in all_nations:
        target_for_relation_change = target

    if intent == "Propose a deal":
        impact_description = f"{agent_name} proposed a deal to {target}."
        peace_change = random.uniform(0.005, 0.015) * (1.1 - peace_index)
        if target_for_relation_change:
            relationship_change = random.uniform(0.05, 0.15)
            impact_description += " Potential for mutual benefit."
        else:
             impact_description += " Global cooperation suggested."

    elif intent == "Respond":
        impact_description = f"{agent_name} responded regarding {target}."
        peace_change = random.uniform(-0.01, 0.01)
        if target_for_relation_change:
            relationship_change = random.uniform(-0.05, 0.05)
            impact_description += " Dialogue continues."

    elif intent == "Comment":
        impact_description = f"{agent_name} commented on the situation regarding {target}."
        peace_change = random.uniform(-0.005, 0.005)

    elif intent == "Build alliances":
        impact_description = f"{agent_name} seeks to build an alliance with {target}."
        peace_change = random.uniform(0.01, 0.02) * (1.1 - peace_index)
        if target_for_relation_change:
            relationship_change = random.uniform(0.1, 0.2)
            impact_description += " Strengthening ties."
        else:
             impact_description += " Promoting general cooperation."


    elif intent == "Request assistance":
        impact_description = f"{agent_name} requested assistance from {target}."
        peace_change = random.uniform(-0.015, -0.005) * (1 + severity_factor)
        if target_for_relation_change:
             relationship_change = random.uniform(-0.05, 0.02)
             impact_description += " Seeking support."
        else:
             impact_description += " Highlighting global need."


    elif intent == "Raise a global concern":
        impact_description = f"{agent_name} raised a global concern."
        peace_change = random.uniform(-0.02, 0.005) * (1 + severity_factor)

    elif intent == "Decline to act":
        impact_description = f"{agent_name} chose to observe this turn."
        peace_change = 0
        relationship_change = 0

    else:
        impact_description = f"{agent_name} took an unrecognized action ({intent})."
        peace_change = random.uniform(-0.01, 0.01)

    metrics["Peace Index"] = max(0.05, min(0.95, peace_index + peace_change))

    current_peace = metrics["Peace Index"]

    if "Climate" in st.session_state.selected_scenario and "Carbon Emissions (Gt)" in metrics:
        emission_change = random.uniform(-0.05, 0.3) + (0.55 - current_peace) * 0.3
        if intent in ["Propose a deal", "Build alliances"]: emission_change -= 0.05
        if intent in ["Raise a global concern", "Request assistance"]: emission_change += 0.05
        metrics["Carbon Emissions (Gt)"] = max(10, metrics.get("Carbon Emissions (Gt)", 35.0) + emission_change)

    elif "Energy" in st.session_state.selected_scenario and "Energy Stability Index" in metrics:
        stability_change = (current_peace - 0.5) * 0.04 + random.uniform(-0.02, 0.02)
        if intent in ["Propose a deal", "Build alliances"]: stability_change += 0.02
        if intent in ["Raise a global concern", "Request assistance"]: stability_change -= 0.02
        metrics["Energy Stability Index"] = max(0.1, min(0.9, metrics.get("Energy Stability Index", 0.6) + stability_change))

    elif "Refugee" in st.session_state.selected_scenario and "Refugee Migration (M)" in metrics:
         if intent in ["Propose a deal", "Build alliances"]:
             decrease = random.randint(0, 2) * (1 + int(current_peace > 0.6))
             metrics["Refugee Migration (M)"] = max(0, metrics.get("Refugee Migration (M)", 20) - decrease)
         elif intent in ["Raise a global concern", "Request assistance"]:
             increase = random.randint(0, 1) * (1 + int(current_peace < 0.4))
             metrics["Refugee Migration (M)"] = max(0, metrics.get("Refugee Migration (M)", 20) + increase)
         else:
              metrics["Refugee Migration (M)"] = max(0, metrics.get("Refugee Migration (M)", 20) + random.randint(-1, 1))


    if "Economic Growth (%)" in metrics:
        base_growth_factor = (current_peace - 0.55) * 0.25 - severity_factor * 0.1
        intent_impact = 0
        if intent in ["Propose a deal", "Build alliances"]: intent_impact = 0.05
        if intent in ["Raise a global concern", "Request assistance"]: intent_impact = -0.03
        random_fluct = random.uniform(-0.08, 0.08)
        current_growth = metrics.get("Economic Growth (%)", 2.5)
        metrics["Economic Growth (%)"] = round(max(-15.0, current_growth + base_growth_factor + intent_impact + random_fluct), 1)

    metrics.setdefault("Carbon Emissions (Gt)", 35.0)
    metrics.setdefault("Refugee Migration (M)", 20)
    metrics.setdefault("Energy Stability Index", 0.6)
    metrics.setdefault("Economic Growth (%)", 2.5)

    return impact_description, relationship_change, target_for_relation_change


def generate_country_card(country):
    profile = COUNTRY_PROFILES.get(country)
    if not profile:
        return "<p><em>Profile not available.</em></p>"

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

st.title("🌐 PoliBot: Global Crisis Negotiation Simulator")

col_main, col_sidebar = st.columns([3, 1])

with col_sidebar:
    st.header("🛠️ Simulation Configuration")

    if 'selected_scenario' not in st.session_state:
        st.session_state.selected_scenario = list(SCENARIO_DETAILS.keys())[0]
    st.session_state.selected_scenario = st.selectbox(
        "🌍 Crisis Scenario",
        options=list(SCENARIO_DETAILS.keys()),
        index=list(SCENARIO_DETAILS.keys()).index(st.session_state.selected_scenario),
        key="scenario_select"
    )
    scenario = st.session_state.selected_scenario

    with st.expander("Scenario Details", expanded=False):
        details = SCENARIO_DETAILS[scenario]
        st.write(f"**Description:** {details['description']}")
        st.write(f"**Key Issues:** {', '.join(details['key_issues'])}")
        st.write(f"**Historical Context:** {details['historical']}")

    available_nations = sorted(list(COUNTRY_PROFILES.keys()))
    if 'selected_nations' not in st.session_state:
        st.session_state.selected_nations = ["USA", "China", "India", "EU", "Pakistan"]
    st.session_state.selected_nations = st.multiselect(
        "🌎 Participating Nations",
        options=available_nations,
        default=st.session_state.selected_nations,
        key="nation_select"
    )
    nations = st.session_state.selected_nations

    if 'sim_speed' not in st.session_state:
        st.session_state.sim_speed = 0.5
    current_speed = st.session_state.get('sim_speed', 0.5)
    if not isinstance(current_speed, (int, float)):
        current_speed = 0.5
        st.session_state.sim_speed = current_speed
    st.session_state.sim_speed = st.slider(
        "⏱️ Delay Per Agent Action (s)",
        min_value=0.0, max_value=3.0,
        value=float(current_speed),
        step=0.1,
        key="speed_slider"
    )
    speed = st.session_state.sim_speed

    if 'num_turns' not in st.session_state:
        st.session_state.num_turns = 10
    st.session_state.num_turns = st.number_input(
        "🔄 Number of Turns",
        min_value=3, max_value=30,
        value=st.session_state.num_turns,
        step=1,
        key="turns_input"
    )
    num_turns = st.session_state.num_turns

    style_options = ["Cooperative", "Competitive", "Mixed"]
    if 'negotiation_style' not in st.session_state or st.session_state.negotiation_style not in style_options:
        st.session_state.negotiation_style = "Mixed"
    st.session_state.negotiation_style = st.radio(
        "🗣️ Agent Behavior Hint (Subtle Influence)",
        options=style_options,
        index=style_options.index(st.session_state.negotiation_style),
        key="style_radio",
        help="Provides a subtle hint to agents, but their core interests dominate."
    )
    negotiation_style = st.session_state.negotiation_style

    if 'advanced_options_checked' not in st.session_state: st.session_state.advanced_options_checked = False
    if 'crisis_severity' not in st.session_state: st.session_state.crisis_severity = 5
    if 'initial_peace' not in st.session_state: st.session_state.initial_peace = 0.5

    st.session_state.advanced_options_checked = st.checkbox("Show Advanced Options", value=st.session_state.advanced_options_checked, key="advanced_checkbox")
    if st.session_state.advanced_options_checked:
        st.session_state.crisis_severity = st.slider("🔥 Crisis Severity", 1, 10, st.session_state.crisis_severity, key="severity_slider")
        st.session_state.initial_peace = st.slider("🕊️ Initial Peace Index", 0.1, 0.9, st.session_state.initial_peace, 0.05, key="peace_slider")

    start_simulation = st.button("🚀 Start Simulation", type="primary", use_container_width=True, key="start_button")

    st.markdown("---")
    st.markdown("### Selected Country Profiles")
    if nations:
        for country in sorted(nations):
            st.markdown(generate_country_card(country), unsafe_allow_html=True)
    else:
        st.warning("Please select at least two nations.")


with col_main:
    st.markdown("---")
    st.subheader("📊 Global Metrics Dashboard")

    if 'metrics' not in st.session_state or start_simulation:
        init_peace = st.session_state.initial_peace if st.session_state.advanced_options_checked else 0.5
        st.session_state.metrics_initial = {
            "Peace Index": init_peace, "Carbon Emissions (Gt)": 35.0,
            "Refugee Migration (M)": 20, "Energy Stability Index": 0.6,
            "Economic Growth (%)": 2.5
        }
        st.session_state.metrics = st.session_state.metrics_initial.copy()

    metrics_container = st.container()
    metric_keys = list(st.session_state.get('metrics', {}).keys())
    metrics_placeholders = {}
    num_metrics = len(metric_keys)
    cols_per_row = 4
    num_rows = (num_metrics + cols_per_row - 1) // cols_per_row

    with metrics_container:
        placeholder_rows = [st.columns(cols_per_row) for _ in range(num_rows)]
        for i, key in enumerate(metric_keys):
            row_index = i // cols_per_row
            col_index = i % cols_per_row
            metrics_placeholders[key] = placeholder_rows[row_index][col_index].empty()

    def display_metrics(metrics_data):
        initial_metrics = st.session_state.get('metrics_initial', metrics_data)
        def get_metric_values(key, current_data, initial_data, default=0):
            current_val = current_data.get(key, default)
            initial_val = initial_data.get(key, default)
            try: delta = float(current_val) - float(initial_val)
            except (ValueError, TypeError): delta = 0
            return current_val, delta

        if "Peace Index" in metrics_placeholders:
             val, delta = get_metric_values("Peace Index", metrics_data, initial_metrics, 0.5)
             metrics_placeholders["Peace Index"].metric("🕊️ Peace Index", f"{val:.2f}", f"{delta:+.2f}", delta_color="normal" if delta >= -0.001 else "inverse")
        if "Carbon Emissions (Gt)" in metrics_placeholders:
            val, delta = get_metric_values("Carbon Emissions (Gt)", metrics_data, initial_metrics, 35.0)
            metrics_placeholders["Carbon Emissions (Gt)"].metric("💨 CO₂ Emissions (Gt)", f"{val:.1f}", f"{delta:+.1f}", delta_color="inverse")
        if "Refugee Migration (M)" in metrics_placeholders:
            val, delta = get_metric_values("Refugee Migration (M)", metrics_data, initial_metrics, 20)
            metrics_placeholders["Refugee Migration (M)"].metric("🚶 Refugees (M)", f"{int(val):,}", f"{int(delta):+,}", delta_color="inverse")
        if "Energy Stability Index" in metrics_placeholders:
             val, delta = get_metric_values("Energy Stability Index", metrics_data, initial_metrics, 0.6)
             metrics_placeholders["Energy Stability Index"].metric("⚡ Energy Stability", f"{val:.2f}", f"{delta:+.2f}", delta_color="normal" if delta >= -0.001 else "inverse")
        if "Economic Growth (%)" in metrics_placeholders:
            val, delta = get_metric_values("Economic Growth (%)", metrics_data, initial_metrics, 2.5)
            metrics_placeholders["Economic Growth (%)"].metric("📈 Econ Growth (%)", f"{val:.1f}%", f"{delta:+.1f}%", delta_color="normal" if delta >= -0.001 else "inverse")

    display_metrics(st.session_state.get('metrics', {}))

    progress_bar_placeholder = st.empty()
    status_text_placeholder = st.empty()

    st.markdown("---")
    st.subheader("🗣️ Agent Action Log")
    negotiation_log_container = st.container(height=400)
    negotiation_log_container.markdown("_(Simulation log will appear here...)_", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📜 Significant Agreements & Actions")
    treaty_container = st.container(height=250)
    treaty_container.markdown("_(Notable agreements or alliance formations will appear here...)_", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🌐 Diplomatic Network")
    graph_placeholder = st.empty()
    graph_placeholder.markdown("_(Diplomatic network graph will appear here...)_", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📄 Simulation Analytics")
    report_placeholder = st.container()
    report_placeholder.markdown("_(Summary report will appear here after simulation...)_")

    if 'simulation_log' not in st.session_state: st.session_state.simulation_log = []
    if 'simulation_agreements' not in st.session_state: st.session_state.simulation_agreements = []
    if 'simulation_relationships' not in st.session_state: st.session_state.simulation_relationships = {}
    if 'simulation_graph' not in st.session_state: st.session_state.simulation_graph = nx.Graph()
    if 'agents' not in st.session_state: st.session_state.agents = {}


if start_simulation:
    if len(nations) < 2:
        st.error("❌ Please select at least two nations to run the simulation.")
    else:
        st.session_state.simulation_log = []
        st.session_state.simulation_agreements = []
        st.session_state.metrics = st.session_state.metrics_initial.copy()
        display_metrics(st.session_state.metrics)

        negotiation_log_container.empty().markdown("_(Simulation running...)_", unsafe_allow_html=True)
        treaty_container.empty().markdown("_(Simulation running...)_", unsafe_allow_html=True)
        graph_placeholder.empty().markdown("_(Simulation running...)_", unsafe_allow_html=True)
        report_placeholder.empty().markdown("_(Simulation running...)_")
        status_text_placeholder.empty()

        agents = {name: CountryAgent(name, COUNTRY_PROFILES[name], groq_client) for name in nations}
        st.session_state.agents = agents

        G = nx.Graph()
        G.add_nodes_from(nations)
        st.session_state.simulation_graph = G
        relationships = {n: {m: 0.0 for m in nations if m != n} for n in nations}
        st.session_state.simulation_relationships = relationships

        progress_bar = progress_bar_placeholder.progress(0, text="Simulation Starting...")
        status_text = status_text_placeholder.text("Initializing Simulation...")

        try:
            metrics = st.session_state.metrics

            for turn in range(1, num_turns + 1):
                status_text.text(f"Processing Turn {turn}/{num_turns}...")
                progress = int((turn / num_turns) * 100)
                progress_bar.progress(progress, text=f"Simulation Progress: Turn {turn}/{num_turns}")

                agent_order = random.sample(list(agents.keys()), len(agents))

                turn_actions = []

                for agent_name in agent_order:
                    agent = agents[agent_name]
                    status_text.text(f"Turn {turn}/{num_turns} - {agent_name}'s Action...")

                    action_raw = agent.act(scenario, SCENARIO_DETAILS[scenario], turn, nations)

                    intent, target, message = parse_action(action_raw)

                    if not intent or not target or not message:
                         intent, target, message = "Decline to act", "GLOBAL", "(Parsing Error)"

                    impact_desc, rel_change, rel_target = determine_action_impact(
                        agent_name, intent, target, message, metrics, nations
                    )

                    st.session_state.metrics = metrics
                    display_metrics(metrics)

                    timestamp = datetime.now().strftime("%H:%M:%S")
                    intent_class = f"intent-{intent.lower().replace(' ', '-')}"
                    log_entry_html = f"""
                    <div class="log-entry {intent_class}">
                        <strong>Turn {turn} • {timestamp} • {agent_name}</strong><br>
                        <strong>Intent:</strong> {intent} | <strong>Target:</strong> {target}<br>
                        <strong>Message:</strong> "{message}"<br>
                        <em>Impact: {impact_desc}</em>
                    </div>
                    """
                    st.session_state.simulation_log.insert(0, log_entry_html)
                    plain_log_for_memory = f"Turn {turn}: {agent_name} - Intent: {intent}, Target: {target}, Msg: '{message}', Impact: {impact_desc}"
                    turn_actions.append((agent_name, plain_log_for_memory))

                    if rel_target and rel_target != agent_name:
                        current_weight = G.get_edge_data(agent_name, rel_target, default={'weight': 0.0})['weight']
                        new_weight = max(-1.0, min(1.0, current_weight + rel_change))
                        G.add_edge(agent_name, rel_target, weight=new_weight)
                        st.session_state.simulation_relationships[agent_name][rel_target] = new_weight
                        st.session_state.simulation_relationships[rel_target][agent_name] = new_weight


                    if intent in ["Propose a deal", "Build alliances"] and rel_target:
                        agreement_log = (agent_name, rel_target, turn, intent, message)
                        st.session_state.simulation_agreements.insert(0, agreement_log)

                    with negotiation_log_container:
                        negotiation_log_container.empty()
                        log_display_html = "".join(st.session_state.simulation_log[:15])
                        st.markdown(log_display_html, unsafe_allow_html=True)

                    with treaty_container:
                        treaty_container.empty()
                        if st.session_state.simulation_agreements:
                            st.markdown("##### Recent Agreements/Overtures")
                            for agmt in st.session_state.simulation_agreements[:5]:
                                st.info(f"""
**{agmt[0]} → {agmt[1]}** (Turn {agmt[2]})
Intent: **{agmt[3]}**
Message: "{agmt[4]}"
""")
                        else:
                            st.markdown("<em>No significant agreements logged yet.</em>", unsafe_allow_html=True)


                    if G.number_of_nodes() > 0:
                        plt.style.use('seaborn-v0_8-whitegrid')
                        plt.figure(figsize=(10, 7))
                        try: pos = nx.kamada_kawai_layout(G, weight='weight', scale=1.0)
                        except Exception: pos = nx.spring_layout(G, seed=42, k=0.9, iterations=50)

                        node_colors = [COUNTRY_PROFILES.get(n, {}).get("color", "#cccccc") for n in G.nodes()]
                        node_sizes = [1200 + G.degree(n) * 250 for n in G.nodes()]

                        edge_weights = [G[u][v].get('weight', 0) for u, v in G.edges()]
                        max_abs_w = max(abs(w) for w in edge_weights) if edge_weights else 1.0
                        max_abs_w = max(max_abs_w, 0.1)

                        edge_widths = [1 + (abs(w) / max_abs_w * 4) for w in edge_weights]
                        edge_colors = ['#2ca02c' if w > 0.1 else '#d62728' if w < -0.1 else '#aaaaaa' for w in edge_weights]
                        edge_alphas = [0.4 + (abs(w) / max_abs_w * 0.5) for w in edge_weights]

                        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9, linewidths=1.0, edgecolors='grey')
                        nx.draw_networkx_edges(G, pos, width=edge_widths, edge_color=edge_colors, alpha=edge_alphas, connectionstyle='arc3,rad=0.05')
                        nx.draw_networkx_labels(G, pos, font_size=9, font_weight="bold", font_color='black')

                        plt.title(f"Diplomatic Network (End of Turn {turn})", fontsize=16)
                        plt.axis("off")
                        plt.tight_layout()
                        buf = io.BytesIO()
                        plt.savefig(buf, format="png", dpi=130, bbox_inches='tight')
                        graph_placeholder.image(buf)
                        plt.close()
                    else:
                        graph_placeholder.markdown("_(Graph requires nodes)_")

                    if speed > 0:
                        time.sleep(speed)

                for acting_agent_name, log_for_memory in turn_actions:
                     if acting_agent_name in agents:
                         agents[acting_agent_name].remember(log_for_memory)
                     parsed_target = re.search(r"Target:\s*(\S+)", log_for_memory)
                     if parsed_target:
                         target_name = parsed_target.group(1)
                         if target_name in agents and target_name != acting_agent_name:
                             memory_for_target = f"Turn {turn}: Received from {acting_agent_name} - Intent: {re.search(r'Intent:\s*(.*?),', log_for_memory).group(1)}, Msg: '{re.search(r'Msg:\s*\'(.*?)\'', log_for_memory).group(1)}'"
                             agents[target_name].remember(memory_for_target)


            status_text.text("Simulation Complete.")
            progress_bar.progress(100, text="Simulation Complete.")
            st.success("✅ Simulation Complete!")

            final_metrics = st.session_state.metrics
            initial_metrics = st.session_state.metrics_initial
            final_G = st.session_state.simulation_graph

            most_active, least_active, strongest_pair_text = "N/A", "N/A", "N/A"
            final_density, num_components = 0.0, 0

            if final_G.number_of_nodes() > 0:
                degrees = list(final_G.degree())
                if degrees:
                    most_active = max(degrees, key=lambda x: x[1])[0]
                    least_active = min(degrees, key=lambda x: x[1])[0]
                final_density = nx.density(final_G)
                if final_G.number_of_edges() > 0: num_components = nx.number_connected_components(final_G)
                else: num_components = final_G.number_of_nodes()

            strongest_pair_text = "N/A (No positive relationships)"
            if final_G.number_of_edges() > 0:
                edge_weights = [((u, v), final_G[u][v].get('weight', 0)) for u, v in final_G.edges()]
                positive_weights = [(pair, w) for pair, w in edge_weights if w > 0.1]
                if positive_weights:
                    strongest_data = max(positive_weights, key=lambda x: x[1])
                    strongest_pair_text = f"{strongest_data[0][0]} ↔ {strongest_data[0][1]} (Weight: {strongest_data[1]:.2f})"

            with report_placeholder:
                st.subheader("Simulation Summary Report")
                st.markdown(f"**Scenario:** {scenario}")
                st.markdown(f"**Duration:** {num_turns} turns ({len(nations)} agent actions per turn)")
                st.markdown(f"**Agreements Logged:** {len(st.session_state.get('simulation_agreements', []))}")
                st.markdown(f"**Network Density:** {final_density:.3f} | **Components:** {num_components}")

                st.markdown("##### Key Observations")
                st.markdown(f"* Most active nation (highest degree): **{most_active}**")
                st.markdown(f"* Strongest positive relationship (highest edge weight > 0.1): **{strongest_pair_text}**")
                st.markdown(f"* Nation with lowest degree: **{least_active}**")

                st.markdown("##### Final Metrics (vs Initial)")
                fm_peace = final_metrics.get('Peace Index', 0); im_peace = initial_metrics.get('Peace Index', 0)
                st.markdown(f"* 🕊️ Peace Index: **{fm_peace:.2f}** ({fm_peace - im_peace:+.2f})")
                fm_co2 = final_metrics.get('Carbon Emissions (Gt)', 0); im_co2 = initial_metrics.get('Carbon Emissions (Gt)', 0)
                st.markdown(f"* 💨 CO₂ Emissions (Gt): **{fm_co2:.1f}** ({fm_co2 - im_co2:+.1f})")
                fm_ref = final_metrics.get('Refugee Migration (M)', 0); im_ref = initial_metrics.get('Refugee Migration (M)', 0)
                st.markdown(f"* 🚶 Refugees (M): **{int(fm_ref):,}** ({int(fm_ref - im_ref):+,})")
                fm_energy = final_metrics.get('Energy Stability Index', 0); im_energy = initial_metrics.get('Energy Stability Index', 0)
                st.markdown(f"* ⚡ Energy Stability: **{fm_energy:.2f}** ({fm_energy - im_energy:+.2f})")
                fm_econ = final_metrics.get('Economic Growth (%)', 0); im_econ = initial_metrics.get('Economic Growth (%)', 0)
                st.markdown(f"* 📈 Econ Growth (%): **{fm_econ:.1f}%** ({fm_econ - im_econ:+.1f}%)")

            st.markdown("---")
            st.subheader("📥 Download Results")

            transcript_data = f"PoliBot Agents Simulation Transcript\nScenario: {scenario}\nTurns: {num_turns}\nNations: {', '.join(nations)}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n---\n\nAGENT ACTION LOG (Newest First):\n\n"
            plain_log_entries = []
            for entry in st.session_state.simulation_log:
                if isinstance(entry, str):
                    text_entry = re.sub(r'<[^>]+>', '', entry)
                    text_entry = text_entry.replace('&nbsp;', ' ')
                    text_entry = "\n".join([line.strip() for line in text_entry.splitlines() if line.strip()])
                    plain_log_entries.append(text_entry)
            transcript_data += "\n\n---\n\n".join(plain_log_entries)

            st.download_button(
                label="📄 Download Full Action Log (.txt)",
                data=transcript_data,
                file_name=f"PoliBot_AgentLog_{scenario.split(' ')[0]}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True,
                key="dl_transcript"
            )

        except Exception as sim_e:
             st.error(f"An error occurred during the simulation: {sim_e}", icon="🔥")
             print("--- Simulation Error Traceback ---")
             traceback.print_exc()
             print("---------------------------------")
             st.exception(sim_e)
        finally:
             progress_bar_placeholder.empty()
             status_text_placeholder.empty()


