import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import random
import time  # <-- Corrected: Import time
from groq import Groq

# --- Streamlit App Setup ---
st.set_page_config(page_title="PoliBot: Global Crisis Negotiation Simulator", layout="wide")
st.title("🌐 PoliBot: Global Crisis Negotiation Simulator")

# --- Groq API Setup ---
groq_client = Groq(api_key="GROQ_API_KEY")  # <-- Put your Groq API key here
MODEL = "llama3-70b-8192"

# --- Helper Function to Generate LLM Message ---
def generate_negotiation_message(speaker, receiver, scenario, negotiation_style):
    system_prompt = f"""
    You are simulating a diplomat for {speaker} negotiating with {receiver}.
    Current global crisis: {scenario}.
    Negotiation style: {negotiation_style}.
    Propose a realistic diplomatic offer or demand to {receiver}.
    Keep it short and formal (2-3 sentences).
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{speaker} initiates a diplomatic communication with {receiver}."}
    ]

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model=MODEL,
        )
        reply = chat_completion.choices[0].message.content
        return reply.strip()
    except Exception as e:
        return f"(Error: {str(e)})"

# --- Sidebar - User Controls ---
st.sidebar.header("🛠️ Setup Simulation")

scenario = st.sidebar.selectbox(
    "Select Crisis Scenario",
    ("🌪️ Climate Collapse", "🦠 Pandemic Outbreak", "⚡ Energy Crisis", "🚰 Water Scarcity", "🛂 Refugee Crisis")
)

nations = st.sidebar.multiselect(
    "Select Participating Nations",
    ["USA", "China", "India", "Russia", "Germany", "Brazil", "France", "UK", "Japan", "South Africa"],
    default=["USA", "China", "India"]
)

speed = st.sidebar.slider("Simulation Speed (seconds per turn)", min_value=0, max_value=10, value=3)

num_turns = st.sidebar.number_input("Number of Turns", min_value=1, max_value=50, value=10)

negotiation_style = st.sidebar.selectbox(
    "Negotiation Style",
    ("Cooperative", "Competitive", "Mixed")
)

model_choice = st.sidebar.selectbox(
    "LLM Model",
    ("Groq LLaMA 3", "Other (not implemented)")
)

start_simulation = st.sidebar.button("🚀 Start Simulation")

# --- Main Panel Layout ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🌍 World State Dashboard")
    world_metrics = {
        "Carbon Emissions (Gt)": random.randint(20, 50),
        "Global GDP (Trillions)": random.randint(70, 100),
        "Refugee Migration (Millions)": random.randint(10, 30),
        "Peace Index": random.uniform(0, 1),
        "Global Temperature (°C)": random.uniform(1.0, 3.0)
    }
    for metric, value in world_metrics.items():
        st.metric(label=metric, value=round(value, 2))

with col2:
    st.subheader("🗣️ Negotiation Log")
    negotiation_log = st.empty()

st.subheader("📜 Treaty Proposals Board")
treaty_board = st.empty()

st.subheader("🔗 Alliances & Relations Graph")
graph_placeholder = st.empty()

st.subheader("📈 Simulation Summary")
report_placeholder = st.empty()

# --- Simulation Logic ---
if start_simulation:
    with st.spinner("Simulating negotiations..."):
        dialogue = []
        treaties = []

        # Graph setup
        G = nx.Graph()
        G.add_nodes_from(nations)

        for turn in range(1, num_turns + 1):
            st.write(f"### 🔄 Turn {turn}")

            speaker, receiver = random.sample(nations, 2)

            # Generate negotiation proposal using LLM
            proposal = generate_negotiation_message(speaker, receiver, scenario, negotiation_style)

            # Decide outcome randomly
            outcome = random.choice(["Accepted ✅", "Rejected ❌", "Pending 🕊️"])

            dialogue.append(f"**{speaker}**: {proposal} ({outcome})")

            # Update treaties and graph
            if outcome == "Accepted ✅":
                G.add_edge(speaker, receiver)
                treaties.append((speaker, receiver))

            # Update Negotiation Log
            negotiation_log.markdown("\n\n".join(dialogue[-10:]))

            # Update Treaty Board
            treaty_board.table({"Proposal": [d for d in dialogue[-5:]]})

            # Update Graph Visualization
            plt.figure(figsize=(6, 4))
            pos = nx.spring_layout(G, seed=42)
            nx.draw(G, pos, with_labels=True, node_color="skyblue", node_size=1500, edge_color="gray")
            graph_placeholder.pyplot(plt)
            plt.clf()

            time.sleep(speed)   # <-- CORRECTED Sleep

        # Final Summary
        peace_change = random.uniform(-0.2, 0.2)
        report_placeholder.success(
            f"Simulation completed! {len(treaties)} treaties signed. Peace Index changed by {peace_change:.2f}."
        )
