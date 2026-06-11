"""
CERELOG — AI Seizure Pattern Diary
===================================
Log daily health data, seizure events, and let AI find your triggers.
"""

import streamlit as st
import anthropic
import json
import os
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cerelog — Seizure Pattern Diary",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
    }

    .stApp {
        background-color: #07090f;
        color: #e8f0fe;
    }

    .main-header {
        font-family: 'Space Mono', monospace;
        font-size: 2.2rem;
        font-weight: 700;
        color: #4d96ff;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem;
    }

    .sub-header {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1rem;
        color: #94a3b8;
        margin-bottom: 2rem;
    }

    .metric-card {
        background: #0d1117;
        border: 1px solid #1e2d45;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }

    .metric-label {
        font-family: 'Space Mono', monospace;
        font-size: 0.65rem;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.3rem;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #e8f0fe;
    }

    .risk-high { color: #ff4444; }
    .risk-med  { color: #ffd93d; }
    .risk-low  { color: #00c853; }

    .seizure-card {
        background: #1a0000;
        border: 1px solid #ff4444;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }

    .trigger-tag {
        display: inline-block;
        background: #0d1117;
        border: 1px solid #1e2d45;
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.8rem;
        color: #4d96ff;
        margin: 0.2rem;
        font-family: 'Space Mono', monospace;
    }

    .section-title {
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
        color: #4a5568;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #1e2d45;
    }

    .ai-message {
        background: #080c14;
        border-left: 3px solid #4d96ff;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #e8f0fe;
    }

    .user-message {
        background: #0d1117;
        border-left: 3px solid #6bcb77;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
        font-size: 0.95rem;
        color: #e8f0fe;
    }

    .stButton button {
        background: #0d1117;
        border: 1px solid #1e2d45;
        color: #e8f0fe;
        border-radius: 8px;
        font-family: 'Space Mono', monospace;
        font-size: 0.8rem;
        transition: all 0.2s;
    }

    .stButton button:hover {
        border-color: #4d96ff;
        color: #4d96ff;
    }

    div[data-testid="stSelectbox"] label,
    div[data-testid="stSlider"] label,
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextArea"] label,
    div[data-testid="stNumberInput"] label {
        color: #94a3b8 !important;
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Space Mono', monospace;
        font-size: 0.8rem;
        color: #94a3b8;
    }

    .stTabs [aria-selected="true"] {
        color: #4d96ff !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "logs" not in st.session_state:
    st.session_state.logs = {}  # date_str -> log dict
if "seizures" not in st.session_state:
    st.session_state.seizures = []  # list of seizure dicts
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_client():
    key = st.session_state.api_key
    if not key or not key.startswith("sk-ant"):
        return None
    return anthropic.Anthropic(api_key=key)

def summarize_logs_for_ai():
    """Build a compact text summary of all logs + seizures for AI context."""
    lines = ["=== PATIENT HEALTH LOG ===\n"]
    for d, log in sorted(st.session_state.logs.items()):
        lines.append(f"Date: {d}")
        lines.append(f"  Sleep: {log.get('sleep_hours', '?')} hrs | Stress: {log.get('stress', '?')}/10")
        lines.append(f"  Mood AM/PM/EVE: {log.get('mood_am','?')} / {log.get('mood_pm','?')} / {log.get('mood_eve','?')}")
        lines.append(f"  Exercise: {log.get('exercise','?')} | Medication: {log.get('medication','?')}")
        lines.append(f"  Food quality: {log.get('food','?')}/10")
        if log.get('notes'):
            lines.append(f"  Notes: {log['notes']}")
        lines.append("")

    if st.session_state.seizures:
        lines.append("=== SEIZURE EVENTS ===\n")
        for s in st.session_state.seizures:
            lines.append(f"Date/Time: {s.get('datetime','?')}")
            lines.append(f"  What happened before: {s.get('before','?')}")
            lines.append(f"  Activities: {s.get('activities','?')}")
            lines.append(f"  Strobe/flashing lights: {s.get('strobe','?')}")
            lines.append(f"  Location: {s.get('location','?')}")
            lines.append(f"  Duration: {s.get('duration','?')} min")
            lines.append(f"  Severity: {s.get('severity','?')}/10")
            lines.append(f"  Additional notes: {s.get('notes','?')}")
            lines.append("")

    return "\n".join(lines)

def call_ai(user_message, system_prompt=None):
    client = get_client()
    if not client:
        return "⚠️ No API key set. Go to Settings in the sidebar to add your Anthropic API key."

    if system_prompt is None:
        system_prompt = f"""You are Cerelog's AI health assistant — a knowledgeable, warm, and scientifically grounded companion for people managing epilepsy.

Your job is to:
1. Find patterns in health and seizure data
2. Identify potential triggers based on research
3. Predict risk levels for tomorrow based on today's log
4. Suggest evidence-based lifestyle adjustments
5. Answer questions about epilepsy science clearly

Here is the patient's health data:
{summarize_logs_for_ai()}

Guidelines:
- Be warm, supportive, and honest
- Always reference the actual data when identifying patterns
- Cite research when making scientific claims (e.g. "Studies show sleep deprivation lowers seizure threshold by...")
- Never diagnose — always recommend sharing findings with their neurologist
- When you find a trigger pattern, explain the science behind WHY that trigger affects seizure risk
- Keep responses focused and actionable
- End analysis responses with: "Share this with your neurologist — they can help you interpret these patterns clinically."
"""

    messages = []
    for msg in st.session_state.chat_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_prompt,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        return f"⚠️ AI error: {str(e)}"

def predict_tomorrow_risk():
    """Ask AI to predict tomorrow's risk based on today's log."""
    today_str = date.today().isoformat()
    today_log = st.session_state.logs.get(today_str, {})
    if not today_log:
        return None, "No log for today yet."

    prompt = f"""Based on today's health data and the patient's seizure history, predict tomorrow's seizure risk.

Today's data:
- Sleep: {today_log.get('sleep_hours', '?')} hours
- Stress: {today_log.get('stress', '?')}/10
- Medication taken: {today_log.get('medication', '?')}
- Exercise: {today_log.get('exercise', '?')}
- Food quality: {today_log.get('food', '?')}/10
- Mood: {today_log.get('mood_am','?')} / {today_log.get('mood_pm','?')} / {today_log.get('mood_eve','?')}

Give:
1. Risk level: LOW / MODERATE / HIGH
2. Top 2 risk factors from today
3. One specific thing they can do tonight to reduce tomorrow's risk
4. The science behind your prediction (1-2 sentences)

Be specific and direct. Format as JSON with keys: risk_level, risk_factors, recommendation, science"""

    response = call_ai(prompt)
    try:
        import re
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data.get("risk_level", "UNKNOWN"), data
    except:
        pass
    return "UNKNOWN", response

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="main-header" style="font-size:1.4rem;">🧠 CERELOG</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Seizure Pattern AI</div>', unsafe_allow_html=True)

    st.markdown("---")

    # API Key
    st.markdown('<div class="section-title">Settings</div>', unsafe_allow_html=True)
    api_input = st.text_input(
        "Anthropic API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="sk-ant-..."
    )
    if api_input != st.session_state.api_key:
        st.session_state.api_key = api_input
        st.success("API key saved!")

    st.markdown("---")

    # Quick stats
    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
    total_logs = len(st.session_state.logs)
    total_seizures = len(st.session_state.seizures)
    st.metric("Days logged", total_logs)
    st.metric("Seizures recorded", total_seizures)

    st.markdown("---")

    # Export
    if st.button("📤 Export for Doctor"):
        export_data = {
            "logs": st.session_state.logs,
            "seizures": st.session_state.seizures,
            "exported": datetime.now().isoformat()
        }
        st.download_button(
            "Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"cerelog_export_{date.today()}.json",
            mime="application/json"
        )

# ─────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="main-header">CERELOG</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-powered seizure pattern diary — log, detect, predict</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Daily Log",
    "⚡ Log Seizure",
    "📊 Patterns",
    "🤖 AI Chat",
    "🔮 Tomorrow's Risk"
])

# ─────────────────────────────────────────────
# TAB 1 — DAILY LOG
# ─────────────────────────────────────────────
with tab1:
    st.markdown('<div class="section-title">Daily Health Log</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        log_date = st.date_input("Date", value=date.today())
        log_date_str = log_date.isoformat()
        existing = st.session_state.logs.get(log_date_str, {})

        if existing:
            st.success(f"✓ Log exists for {log_date_str}")

    with col2:
        st.markdown("**Sleep**")
        sleep_hours = st.slider("Hours of sleep", 0.0, 12.0,
                                float(existing.get("sleep_hours", 7.0)), 0.5)

        st.markdown("**Stress Level**")
        stress = st.slider("Stress (1=none, 10=extreme)", 1, 10,
                           int(existing.get("stress", 3)))

        st.markdown("**Food Quality**")
        food = st.slider("Food quality (1=poor, 10=excellent)", 1, 10,
                         int(existing.get("food", 7)))

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**Mood — split by time of day**")
        mood_options = ["Great", "Good", "Neutral", "Low", "Very Low"]
        mood_am = st.selectbox("Morning mood", mood_options,
                               index=mood_options.index(existing.get("mood_am", "Good")))
        mood_pm = st.selectbox("Afternoon mood", mood_options,
                               index=mood_options.index(existing.get("mood_pm", "Good")))
        mood_eve = st.selectbox("Evening mood", mood_options,
                                index=mood_options.index(existing.get("mood_eve", "Good")))

    with col4:
        st.markdown("**Activities & Medication**")
        exercise = st.selectbox("Exercise", ["None", "Light walk", "Moderate", "Intense"],
                                index=["None", "Light walk", "Moderate", "Intense"].index(
                                    existing.get("exercise", "None")))
        medication = st.selectbox("Medication taken", ["Yes — on time", "Yes — late", "Missed dose", "No medication"],
                                  index=["Yes — on time", "Yes — late", "Missed dose", "No medication"].index(
                                      existing.get("medication", "Yes — on time")))
        notes = st.text_area("Notes (anything unusual today?)",
                             value=existing.get("notes", ""), height=100)

    if st.button("💾 Save Daily Log", use_container_width=True):
        st.session_state.logs[log_date_str] = {
            "sleep_hours": sleep_hours,
            "stress": stress,
            "food": food,
            "mood_am": mood_am,
            "mood_pm": mood_pm,
            "mood_eve": mood_eve,
            "exercise": exercise,
            "medication": medication,
            "notes": notes
        }
        st.success(f"✓ Log saved for {log_date_str}")
        st.rerun()

# ─────────────────────────────────────────────
# TAB 2 — LOG SEIZURE
# ─────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">Log a Seizure Event</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="metric-card">
    <div class="metric-label">Why log this?</div>
    Research shows that 60-70% of epilepsy patients can identify personal triggers once they start tracking.
    The more detail you log, the better the AI can find your patterns.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        seizure_date = st.date_input("Date of seizure", value=date.today(), key="sz_date")
        seizure_time = st.time_input("Approximate time", key="sz_time")
        severity = st.slider("Severity (1=mild, 10=severe)", 1, 10, 5)
        duration = st.number_input("Duration (minutes)", 0, 60, 2)
        location = st.text_input("Where were you?", placeholder="e.g. home, school, outdoors")

    with col2:
        before = st.text_area("What were you doing before the seizure?",
                              placeholder="e.g. watching a movie, just woke up, exercising...",
                              height=100)
        activities = st.text_area("Any specific activities in the past 2 hours?",
                                  placeholder="e.g. watching TV, swimming, playing video games...",
                                  height=80)
        strobe = st.selectbox("Were there any flashing or flickering lights?",
                              ["No", "Yes — TV/screen", "Yes — sunlight flickering", "Yes — other", "Unsure"])
        sz_notes = st.text_area("Anything else that might be relevant?",
                                placeholder="stress, missed medication, poor sleep the night before...",
                                height=80)

    if st.button("⚡ Log This Seizure", use_container_width=True):
        seizure_entry = {
            "datetime": f"{seizure_date} {seizure_time}",
            "severity": severity,
            "duration": duration,
            "location": location,
            "before": before,
            "activities": activities,
            "strobe": strobe,
            "notes": sz_notes
        }
        st.session_state.seizures.append(seizure_entry)
        st.success("✓ Seizure logged.")

        # Auto-trigger AI analysis
        if get_client() and len(st.session_state.seizures) >= 2:
            with st.spinner("AI is analyzing your seizure patterns..."):
                analysis = call_ai(
                    "I just logged a new seizure. Based on all my seizure data and health logs, what patterns do you see? What might my triggers be? Be specific.",
                )
            st.markdown('<div class="section-title" style="margin-top:1rem;">AI Pattern Analysis</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="ai-message">{analysis}</div>', unsafe_allow_html=True)

    # Show existing seizures
    if st.session_state.seizures:
        st.markdown("---")
        st.markdown('<div class="section-title">Seizure History</div>', unsafe_allow_html=True)
        for i, s in enumerate(reversed(st.session_state.seizures)):
            st.markdown(f"""
            <div class="seizure-card">
            <strong>{s.get('datetime','?')}</strong> — Severity {s.get('severity','?')}/10 — {s.get('duration','?')} min<br>
            <small style="color:#94a3b8;">Before: {s.get('before','?')}</small><br>
            <small style="color:#94a3b8;">Strobe: {s.get('strobe','?')} | Location: {s.get('location','?')}</small>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 3 — PATTERNS
# ─────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">Health & Seizure Patterns</div>', unsafe_allow_html=True)

    if len(st.session_state.logs) < 2:
        st.info("Log at least 2 days of data to see patterns.")
    else:
        # Build dataframe
        rows = []
        for d, log in sorted(st.session_state.logs.items()):
            row = {"date": d}
            row.update(log)
            # Mark seizure days
            row["had_seizure"] = any(
                s.get("datetime", "").startswith(d)
                for s in st.session_state.seizures
            )
            rows.append(row)

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])

        col1, col2 = st.columns(2)

        with col1:
            # Sleep chart
            fig_sleep = go.Figure()
            fig_sleep.add_trace(go.Scatter(
                x=df["date"], y=df["sleep_hours"],
                mode="lines+markers",
                line=dict(color="#4d96ff", width=2),
                marker=dict(size=6),
                name="Sleep hours"
            ))
            # Mark seizure days
            seizure_days = df[df["had_seizure"] == True]
            if not seizure_days.empty:
                fig_sleep.add_trace(go.Scatter(
                    x=seizure_days["date"],
                    y=seizure_days["sleep_hours"],
                    mode="markers",
                    marker=dict(color="#ff4444", size=12, symbol="x"),
                    name="Seizure day"
                ))
            fig_sleep.update_layout(
                title="Sleep Hours (× = seizure day)",
                paper_bgcolor="#07090f",
                plot_bgcolor="#0d1117",
                font=dict(color="#e8f0fe", size=11),
                height=280,
                margin=dict(l=40, r=20, t=40, b=40)
            )
            st.plotly_chart(fig_sleep, use_container_width=True)

        with col2:
            # Stress chart
            fig_stress = go.Figure()
            fig_stress.add_trace(go.Scatter(
                x=df["date"], y=df["stress"],
                mode="lines+markers",
                line=dict(color="#ffd93d", width=2),
                marker=dict(size=6),
                name="Stress"
            ))
            if not seizure_days.empty:
                fig_stress.add_trace(go.Scatter(
                    x=seizure_days["date"],
                    y=seizure_days["stress"],
                    mode="markers",
                    marker=dict(color="#ff4444", size=12, symbol="x"),
                    name="Seizure day"
                ))
            fig_stress.update_layout(
                title="Stress Level (× = seizure day)",
                paper_bgcolor="#07090f",
                plot_bgcolor="#0d1117",
                font=dict(color="#e8f0fe", size=11),
                height=280,
                margin=dict(l=40, r=20, t=40, b=40)
            )
            st.plotly_chart(fig_stress, use_container_width=True)

        # AI trigger analysis
        st.markdown("---")
        st.markdown('<div class="section-title">AI Trigger Analysis</div>', unsafe_allow_html=True)

        if st.button("🔍 Analyze My Triggers", use_container_width=True):
            if not get_client():
                st.warning("Add your API key in Settings to use AI analysis.")
            else:
                with st.spinner("Analyzing your data for trigger patterns..."):
                    analysis = call_ai(
                        """Analyze all my health logs and seizure events. 
                        1. What are my top 3 most likely triggers? Explain the science behind each.
                        2. What patterns do you see between my lifestyle data and seizure days?
                        3. What specific changes would most reduce my risk?
                        4. What should I tell my neurologist?
                        Be specific and reference my actual data."""
                    )
                st.markdown(f'<div class="ai-message">{analysis}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 4 — AI CHAT
# ─────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-title">Talk to Your AI Health Assistant</div>', unsafe_allow_html=True)

    # Show chat history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-message">You: {msg["content"]}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-message">Cerelog AI: {msg["content"]}</div>',
                        unsafe_allow_html=True)

    # Suggested questions
    st.markdown("**Quick questions:**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("What are my triggers?"):
            st.session_state.chat_history.append(
                {"role": "user", "content": "What are my triggers based on my data?"})
            st.rerun()
    with col2:
        if st.button("Why does sleep affect seizures?"):
            st.session_state.chat_history.append(
                {"role": "user",
                 "content": "Explain the science of why sleep deprivation increases seizure risk."})
            st.rerun()
    with col3:
        if st.button("What should I tell my doctor?"):
            st.session_state.chat_history.append(
                {"role": "user",
                 "content": "Based on my data, what are the most important things to tell my neurologist?"})
            st.rerun()

    # Check if there is a pending message to respond to
    if (st.session_state.chat_history and
            st.session_state.chat_history[-1]["role"] == "user"):
        last_msg = st.session_state.chat_history[-1]["content"]
        with st.spinner("Thinking..."):
            response = call_ai(last_msg)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

    # Input
    user_input = st.text_input("Ask anything about your seizures, triggers, or health...",
                               placeholder="e.g. Do I have more seizures when I'm stressed?",
                               key="chat_input")

    col_send, col_clear = st.columns([3, 1])
    with col_send:
        if st.button("Send", use_container_width=True):
            if user_input.strip():
                st.session_state.chat_history.append(
                    {"role": "user", "content": user_input})
                st.rerun()
    with col_clear:
        if st.button("Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

# ─────────────────────────────────────────────
# TAB 5 — TOMORROW'S RISK
# ─────────────────────────────────────────────
with tab5:
    st.markdown('<div class="section-title">Tomorrow\'s Risk Prediction</div>', unsafe_allow_html=True)

    today_str = date.today().isoformat()
    today_log = st.session_state.logs.get(today_str)

    if not today_log:
        st.warning("Log today's health data first to get tomorrow's risk prediction.")
    elif not get_client():
        st.warning("Add your API key in Settings to use risk prediction.")
    else:
        if st.button("🔮 Predict Tomorrow's Risk", use_container_width=True):
            with st.spinner("Calculating risk..."):
                risk_level, risk_data = predict_tomorrow_risk()

            color_map = {"LOW": "#00c853", "MODERATE": "#ffd93d", "HIGH": "#ff4444"}
            color = color_map.get(risk_level, "#94a3b8")

            st.markdown(f"""
            <div class="metric-card" style="border-color: {color}; text-align: center;">
                <div class="metric-label">Tomorrow's predicted risk</div>
                <div class="metric-value" style="color: {color}; font-size: 3rem;">{risk_level}</div>
            </div>
            """, unsafe_allow_html=True)

            if isinstance(risk_data, dict):
                factors = risk_data.get("risk_factors", [])
                if factors:
                    st.markdown("**Risk factors from today:**")
                    for f in factors:
                        st.markdown(f'<span class="trigger-tag">{f}</span>', unsafe_allow_html=True)

                rec = risk_data.get("recommendation", "")
                if rec:
                    st.markdown(f"""
                    <div class="ai-message" style="margin-top:1rem;">
                    <strong>Recommendation for tonight:</strong><br>{rec}
                    </div>
                    """, unsafe_allow_html=True)

                science = risk_data.get("science", "")
                if science:
                    st.markdown(f"""
                    <div class="metric-card" style="margin-top:1rem;">
                    <div class="metric-label">The science behind this</div>
                    {science}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ai-message">{risk_data}</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
        <div class="metric-card">
        <div class="metric-label">How this works</div>
        The AI looks at today's sleep, stress, medication adherence, and food quality — 
        then cross-references with your seizure history to identify which factors 
        correlate most with your seizure days. Research shows that 
        <strong>sleep deprivation, missed medication, and high stress</strong> are the 
        three most common modifiable seizure triggers across epilepsy patients.
        </div>
        """, unsafe_allow_html=True)
