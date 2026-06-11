"""
CERELOG — AI Seizure Pattern Diary v2
No API key required. Rule-based pattern detection engine.
"""

import streamlit as st
import json
import re
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.graph_objects as go
import random

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Cerelog — Seizure Diary",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# COLOR SCHEMES
# ─────────────────────────────────────────────
SCHEMES = {
    "🌊 Navy & Gold": {
        "bg": "#0a1628", "panel": "#0f2040", "border": "#1e3a5f",
        "accent": "#f5c842", "accent2": "#4d96ff",
        "text": "#f0f4ff", "muted": "#8ba3c7", "dim": "#3a5070",
        "safe": "#2ecc71", "warn": "#f5c842", "alert": "#e74c3c",
        "btn_bg": "#0f2040", "card_bg": "#0d1e3a"
    },
    "🌸 Pink & White": {
        "bg": "#fff0f5", "panel": "#ffe4ee", "border": "#ffb3cc",
        "accent": "#ff6b9d", "accent2": "#c084fc",
        "text": "#2d1b2e", "muted": "#7a4060", "dim": "#c490a0",
        "safe": "#22c55e", "warn": "#f59e0b", "alert": "#ef4444",
        "btn_bg": "#ffe4ee", "card_bg": "#fff5f8"
    },
    "🌿 Forest & Cream": {
        "bg": "#0f1f0f", "panel": "#162816", "border": "#254025",
        "accent": "#7ec850", "accent2": "#d4b483",
        "text": "#f0f4e8", "muted": "#8aaa70", "dim": "#3a5030",
        "safe": "#4ade80", "warn": "#fbbf24", "alert": "#f87171",
        "btn_bg": "#162816", "card_bg": "#122012"
    },
    "🌑 Dark & Teal": {
        "bg": "#07090f", "panel": "#0d1117", "border": "#1e2d45",
        "accent": "#00e5b4", "accent2": "#4d96ff",
        "text": "#e8f0fe", "muted": "#94a3b8", "dim": "#4a5568",
        "safe": "#00c853", "warn": "#ffd93d", "alert": "#ff4444",
        "btn_bg": "#0d1117", "card_bg": "#080c14"
    },
}

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "logs" not in st.session_state:
    st.session_state.logs = {}
if "seizures" not in st.session_state:
    st.session_state.seizures = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "scheme_name" not in st.session_state:
    st.session_state.scheme_name = "🌊 Navy & Gold"
if "show_confetti" not in st.session_state:
    st.session_state.show_confetti = False

C = SCHEMES[st.session_state.scheme_name]

# ─────────────────────────────────────────────
# DYNAMIC CSS
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {{ font-family: 'Space Grotesk', sans-serif; }}
.stApp {{ background-color: {C['bg']}; color: {C['text']}; }}

.main-header {{
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem; font-weight: 700;
    color: {C['accent']}; letter-spacing: -0.02em;
    margin-bottom: 0.1rem;
}}
.sub-header {{ color: {C['muted']}; font-size: 1rem; margin-bottom: 1.5rem; }}
.section-title {{
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem; color: {C['dim']};
    text-transform: uppercase; letter-spacing: 0.12em;
    margin-bottom: 0.8rem; padding-bottom: 0.4rem;
    border-bottom: 1px solid {C['border']};
}}
.metric-card {{
    background: {C['card_bg']}; border: 1px solid {C['border']};
    border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;
}}
.ai-bubble {{
    background: {C['panel']}; border-left: 3px solid {C['accent']};
    border-radius: 0 10px 10px 0; padding: 0.9rem 1.1rem;
    margin: 0.4rem 0; font-size: 0.93rem; line-height: 1.7;
    color: {C['text']};
}}
.user-bubble {{
    background: {C['card_bg']}; border-left: 3px solid {C['accent2']};
    border-radius: 0 10px 10px 0; padding: 0.9rem 1.1rem;
    margin: 0.4rem 0; font-size: 0.93rem; color: {C['text']};
}}
.disclaimer {{
    background: {C['panel']}; border: 1px solid {C['border']};
    border-radius: 8px; padding: 0.7rem 1rem; margin-top: 1rem;
    font-size: 0.78rem; color: {C['muted']}; line-height: 1.5;
}}
.trigger-tag {{
    display: inline-block; background: {C['panel']};
    border: 1px solid {C['accent']}; border-radius: 20px;
    padding: 0.2rem 0.7rem; font-size: 0.78rem;
    color: {C['accent']}; margin: 0.2rem;
    font-family: 'Space Mono', monospace;
}}
.risk-high {{ color: {C['alert']}; font-weight: 700; font-size: 2rem; }}
.risk-med  {{ color: {C['warn']};  font-weight: 700; font-size: 2rem; }}
.risk-low  {{ color: {C['safe']};  font-weight: 700; font-size: 2rem; }}
.seizure-card {{
    background: {C['card_bg']}; border: 1px solid {C['alert']};
    border-radius: 10px; padding: 0.9rem 1.1rem; margin-bottom: 0.7rem;
}}
.stButton>button {{
    background: {C['btn_bg']}; border: 1px solid {C['border']};
    color: {C['text']}; border-radius: 8px;
    font-family: 'Space Mono', monospace; font-size: 0.78rem;
    transition: all 0.2s;
}}
.stButton>button:hover {{ border-color: {C['accent']}; color: {C['accent']}; }}
div[data-testid="stSelectbox"] label,
div[data-testid="stSlider"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stCheckbox"] label {{
    color: {C['muted']} !important;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: 'Space Mono', monospace; font-size: 0.78rem; color: {C['muted']};
}}
.stTabs [aria-selected="true"] {{ color: {C['accent']} !important; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONFETTI
# ─────────────────────────────────────────────
def show_confetti():
    colors = [C['accent'], C['accent2'], C['safe'], C['warn'], '#ff6b9d', '#c084fc']
    colors_js = json.dumps(colors)
    st.markdown(f"""
    <canvas id="confetti-canvas" style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999;"></canvas>
    <script>
    (function() {{
        const canvas = document.getElementById('confetti-canvas');
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        const colors = {colors_js};
        const particles = Array.from({{length: 120}}, () => ({{
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height - canvas.height,
            r: Math.random() * 8 + 4,
            d: Math.random() * 120 + 20,
            color: colors[Math.floor(Math.random() * colors.length)],
            tilt: Math.floor(Math.random() * 10) - 10,
            tiltAngle: 0, tiltAngleInc: Math.random() * 0.07 + 0.05
        }}));
        let frame = 0;
        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => {{
                ctx.beginPath();
                ctx.lineWidth = p.r / 2;
                ctx.strokeStyle = p.color;
                ctx.moveTo(p.x + p.tilt + p.r / 4, p.y);
                ctx.lineTo(p.x + p.tilt, p.y + p.tilt + p.r / 4);
                ctx.stroke();
                p.tiltAngle += p.tiltAngleInc;
                p.y += (Math.cos(frame / 20) + 1 + p.r / 2) / 2;
                p.tilt = Math.sin(p.tiltAngle - frame / 3) * 15;
            }});
            frame++;
            if (frame < 180) requestAnimationFrame(draw);
            else ctx.clearRect(0, 0, canvas.width, canvas.height);
        }}
        draw();
    }})();
    </script>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# KNOWN RESEARCH TRIGGERS
# ─────────────────────────────────────────────
RESEARCH_TRIGGERS = {
    "sleep_deprivation": {
        "label": "Sleep deprivation",
        "icon": "😴",
        "science": "Sleep deprivation lowers seizure threshold by reducing GABAergic inhibition and increasing cortical excitability. Studies show seizure risk increases significantly after fewer than 6 hours of sleep.",
        "check": lambda log: float(log.get("sleep_hours", 8)) < 6
    },
    "high_stress": {
        "label": "High stress",
        "icon": "😤",
        "science": "Stress activates the HPA axis, releasing cortisol which can lower seizure threshold. Chronic stress also disrupts sleep architecture, compounding seizure risk.",
        "check": lambda log: int(log.get("stress", 1)) >= 7
    },
    "missed_medication": {
        "label": "Missed medication",
        "icon": "💊",
        "science": "Missed anti-epileptic doses are the leading cause of breakthrough seizures in controlled epilepsy. Even one missed dose can cause a rebound excitability effect.",
        "check": lambda log: "missed" in log.get("medication", "").lower()
    },
    "poor_food": {
        "label": "Poor nutrition / missed meal",
        "icon": "🍽️",
        "science": "Hypoglycemia from missed meals can trigger seizures. Blood glucose drops increase neuronal excitability and can destabilize seizure threshold.",
        "check": lambda log: int(log.get("food", 10)) <= 3
    },
    "low_mood": {
        "label": "Low or anxious mood",
        "icon": "😢",
        "science": "Anxiety and depression are highly comorbid with epilepsy. Emotional stress and mood dysregulation share overlapping neurochemical pathways with seizure generation.",
        "check": lambda log: any(
            m in ["😢 Sad", "😰 Anxious", "Very Low", "Low"]
            for m in [log.get("mood_am",""), log.get("mood_pm",""), log.get("mood_eve","")]
        )
    },
}

LIFESTYLE_TRIGGERS = [
    "Strobe / flashing lights", "Screens for long time", "Alcohol", "Caffeine",
    "Swimming", "Exercise — intense", "Illness / fever", "Menstrual cycle",
    "Travel / jet lag", "Loud music / concert", "Skipped breakfast",
    "Dehydration", "Hot weather", "Emotional shock",
    "Missed meal", "High blood sugar", "Low blood sugar",
    "Anxiety episode", "High stress day", "Sleep deprived",
    "Missed medication", "Pain / migraine", "Photosensitive trigger",
    "Alcohol consumed", "After exercise crash", "REM sleep disrupted",
    "Mental overload / burnout"
]

# ─────────────────────────────────────────────
# RULE-BASED AI ENGINE
# ─────────────────────────────────────────────
def analyze_triggers():
    """Find trigger patterns from logs + seizures."""
    if not st.session_state.seizures:
        return [], []

    found_triggers = {}
    all_days = len(st.session_state.logs)

    for seizure in st.session_state.seizures:
        sz_date_str = str(seizure.get("datetime", ""))[:10]
        try:
            sz_date = date.fromisoformat(sz_date_str)
        except:
            continue

        # Check 2 days before seizure
        for delta in [0, 1, 2]:
            check_date = (sz_date - timedelta(days=delta)).isoformat()
            log = st.session_state.logs.get(check_date, {})
            if not log:
                continue
            for key, trigger in RESEARCH_TRIGGERS.items():
                if trigger["check"](log):
                    if key not in found_triggers:
                        found_triggers[key] = {"count": 0, "trigger": trigger}
                    found_triggers[key]["count"] += 1

        # Check seizure notes for lifestyle triggers
        notes_text = (
            str(seizure.get("before", "")) + " " +
            str(seizure.get("activities", "")) + " " +
            str(seizure.get("notes", "")) + " " +
            str(seizure.get("strobe", ""))
        ).lower()

        for lt in LIFESTYLE_TRIGGERS:
            keyword = lt.split(" ")[0].lower()
            if keyword in notes_text or lt.lower() in notes_text:
                key = f"lifestyle_{lt}"
                if key not in found_triggers:
                    found_triggers[key] = {"count": 0, "trigger": {"label": lt, "icon": "⚡", "science": f"Personal pattern detected: {lt} appears in your seizure notes."}}
                found_triggers[key]["count"] += 1

    # Sort by frequency
    sorted_triggers = sorted(found_triggers.values(), key=lambda x: x["count"], reverse=True)
    top_triggers = sorted_triggers[:5]

    # Patterns
    patterns = []
    if all_days >= 3:
        seizure_sleep = []
        normal_sleep = []
        for d, log in st.session_state.logs.items():
            is_seizure_day = any(str(s.get("datetime",""))[:10] == d for s in st.session_state.seizures)
            sleep = float(log.get("sleep_hours", 8))
            if is_seizure_day:
                seizure_sleep.append(sleep)
            else:
                normal_sleep.append(sleep)

        if seizure_sleep and normal_sleep:
            avg_sz = sum(seizure_sleep) / len(seizure_sleep)
            avg_norm = sum(normal_sleep) / len(normal_sleep)
            if avg_norm - avg_sz > 0.5:
                patterns.append(f"You averaged {avg_sz:.1f} hrs sleep before seizure days vs {avg_norm:.1f} hrs on normal days.")

        seizure_stress = []
        normal_stress = []
        for d, log in st.session_state.logs.items():
            is_seizure_day = any(str(s.get("datetime",""))[:10] == d for s in st.session_state.seizures)
            stress = int(log.get("stress", 5))
            if is_seizure_day:
                seizure_stress.append(stress)
            else:
                normal_stress.append(stress)

        if seizure_stress and normal_stress:
            avg_sz_s = sum(seizure_stress) / len(seizure_stress)
            avg_norm_s = sum(normal_stress) / len(normal_stress)
            if avg_sz_s - avg_norm_s > 1.0:
                patterns.append(f"Your stress was {avg_sz_s:.1f}/10 before seizure days vs {avg_norm_s:.1f}/10 on normal days.")

    return top_triggers, patterns

def predict_risk_tomorrow():
    today_str = date.today().isoformat()
    log = st.session_state.logs.get(today_str, {})
    if not log:
        return None, [], "No log for today yet."

    risk_score = 0
    risk_factors = []

    sleep = float(log.get("sleep_hours", 8))
    if sleep < 5:
        risk_score += 3
        risk_factors.append(f"😴 Very low sleep ({sleep} hrs)")
    elif sleep < 6.5:
        risk_score += 2
        risk_factors.append(f"😴 Low sleep ({sleep} hrs)")

    stress = int(log.get("stress", 1))
    if stress >= 8:
        risk_score += 3
        risk_factors.append(f"😤 Very high stress ({stress}/10)")
    elif stress >= 6:
        risk_score += 2
        risk_factors.append(f"😤 Elevated stress ({stress}/10)")

    if "missed" in log.get("medication", "").lower():
        risk_score += 4
        risk_factors.append("💊 Missed medication")
    elif "late" in log.get("medication", "").lower():
        risk_score += 1
        risk_factors.append("💊 Late medication")

    food = int(log.get("food", 10))
    if food <= 3:
        risk_score += 2
        risk_factors.append(f"🍽️ Poor nutrition ({food}/10)")

    moods = [log.get("mood_am",""), log.get("mood_pm",""), log.get("mood_eve","")]
    low_moods = sum(1 for m in moods if "😢" in m or "😰" in m or "Low" in m)
    if low_moods >= 2:
        risk_score += 2
        risk_factors.append("😢 Low mood for most of the day")

    if risk_score >= 6:
        level = "HIGH"
        rec = "Prioritize sleep tonight. Take medication on time. Avoid screens before bed. Consider telling someone you trust about your elevated risk tomorrow."
    elif risk_score >= 3:
        level = "MODERATE"
        rec = "Try to get at least 7-8 hours of sleep. Reduce screen time. Stay hydrated and eat a good meal before bed."
    else:
        level = "LOW"
        rec = "You are in good shape. Keep up the healthy habits."

    return level, risk_factors, rec

def chatbot_response(user_input):
    """Rule-based chatbot with epilepsy knowledge + personal data reasoning."""
    text = user_input.lower()
    logs = st.session_state.logs
    seizures = st.session_state.seizures
    total_logs = len(logs)
    total_seizures = len(seizures)

    # Normalize typos / shorthand
    text = re.sub(r'seiz\w*', 'seizure', text)
    text = re.sub(r'med\w*', 'medication', text)
    text = re.sub(r'slp|slep', 'sleep', text)
    text = re.sub(r'str\w{0,3}s', 'stress', text)

    top_triggers, patterns = analyze_triggers()

    # TRIGGER QUESTIONS
    if any(w in text for w in ["trigger", "cause", "why", "what makes", "pattern"]):
        if not seizures:
            return ("I do not have any seizure events logged yet. Once you log a few seizures using the ⚡ Log Seizure tab, "
                    "I can start analyzing your personal trigger patterns.\n\n"
                    "Common research-backed triggers include: sleep deprivation, missed medication, high stress, "
                    "poor nutrition, and strobe/flashing lights.")
        response = f"Based on your {total_seizures} logged seizure(s) and {total_logs} days of health data, here is what I found:\n\n"
        if top_triggers:
            response += "**Your likely triggers:**\n"
            for t in top_triggers[:3]:
                trig = t["trigger"]
                response += f"\n{trig['icon']} **{trig['label']}** (appeared {t['count']} time(s) before a seizure)\n"
                response += f"_{trig['science']}_\n"
        if patterns:
            response += "\n**Patterns in your data:**\n"
            for p in patterns:
                response += f"• {p}\n"
        response += "\n\n⚕️ *Share this with your neurologist — they can help interpret these patterns clinically.*"
        return response

    # SLEEP SCIENCE
    elif any(w in text for w in ["sleep", "tired", "rest", "insomnia"]):
        avg_sleep = None
        if logs:
            sleeps = [float(l.get("sleep_hours", 8)) for l in logs.values()]
            avg_sleep = sum(sleeps) / len(sleeps)
        response = "**Sleep and seizure risk — the science:**\n\n"
        response += ("Sleep deprivation is one of the most well-documented seizure triggers. "
                     "During sleep, the brain clears metabolic waste and resets inhibitory neurotransmitters like GABA. "
                     "When you sleep less than 6-7 hours, GABAergic inhibition weakens and cortical excitability rises — "
                     "this directly lowers your seizure threshold.\n\n")
        if avg_sleep:
            response += f"Your average sleep from logged days: **{avg_sleep:.1f} hours**.\n"
            if avg_sleep < 6:
                response += "⚠️ This is below the recommended 7-9 hours and may be increasing your risk.\n"
            else:
                response += "✓ This is within a healthy range.\n"
        response += "\n⚕️ *Always discuss sleep concerns with your neurologist.*"
        return response

    # MEDICATION
    elif any(w in text for w in ["medication", "medicine", "drug", "pill", "dose"]):
        missed_days = sum(1 for l in logs.values() if "missed" in l.get("medication","").lower())
        response = "**Medication and seizure control:**\n\n"
        response += ("Missing even one dose of anti-epileptic medication (AED) is the leading cause of breakthrough seizures "
                     "in people with otherwise well-controlled epilepsy. AEDs maintain a steady blood level — "
                     "a missed dose causes a rapid drop that can trigger rebound excitability.\n\n")
        if missed_days > 0:
            response += f"⚠️ You have logged **{missed_days} missed dose day(s)**. This is an important pattern to discuss with your doctor.\n"
        else:
            response += "✓ No missed medication days logged.\n"
        response += "\n⚕️ *Never change or stop medication without your neurologist's guidance.*"
        return response

    # STRESS
    elif any(w in text for w in ["stress", "anxiety", "anxious", "worried", "nervous"]):
        avg_stress = None
        if logs:
            stresses = [int(l.get("stress", 5)) for l in logs.values()]
            avg_stress = sum(stresses) / len(stresses)
        response = "**Stress, anxiety, and seizures:**\n\n"
        response += ("Stress activates the hypothalamic-pituitary-adrenal (HPA) axis, releasing cortisol. "
                     "Elevated cortisol can reduce GABA receptor sensitivity and increase glutamate activity — "
                     "both of which lower seizure threshold. Chronic stress also disrupts sleep, which compounds the risk.\n\n")
        if avg_stress:
            response += f"Your average stress level: **{avg_stress:.1f}/10**.\n"
            if avg_stress >= 6:
                response += "⚠️ This is elevated. Stress management techniques like breathing exercises, gentle exercise, and consistent sleep may help.\n"
        response += "\n⚕️ *If anxiety is severe, speak with your neurologist about options.*"
        return response

    # RISK / PREDICTION
    elif any(w in text for w in ["risk", "tomorrow", "predict", "chance", "likely"]):
        level, factors, rec = predict_risk_tomorrow()
        if not level:
            return "Log today's health data in the Daily Log tab and I can predict tomorrow's risk for you."
        response = f"**Tomorrow's predicted risk: {level}**\n\n"
        if factors:
            response += "Risk factors from today:\n"
            for f in factors:
                response += f"• {f}\n"
        response += f"\n**Recommendation:** {rec}\n"
        response += "\n⚕️ *This is an estimate based on your personal patterns, not a medical diagnosis.*"
        return response

    # DIET / FOOD
    elif any(w in text for w in ["food", "eat", "diet", "meal", "nutrition", "glucose", "sugar"]):
        return ("**Food, blood sugar, and seizures:**\n\n"
                "Skipping meals causes blood glucose to drop, which increases neuronal excitability. "
                "The ketogenic diet has strong clinical evidence for reducing seizures in drug-resistant epilepsy — "
                "it works by shifting the brain's fuel source from glucose to ketones, which have anti-seizure properties.\n\n"
                "General recommendations:\n"
                "• Eat regular meals — do not skip breakfast\n"
                "• Reduce refined sugar and processed carbohydrates\n"
                "• Stay hydrated — dehydration can also lower seizure threshold\n\n"
                "⚕️ *Discuss major dietary changes with your neurologist before starting.*")

    # STROBE / LIGHTS
    elif any(w in text for w in ["strobe", "light", "flash", "screen", "tv", "photosensitive"]):
        return ("**Photosensitivity and seizures:**\n\n"
                "About 3% of people with epilepsy have photosensitive epilepsy — triggered by flickering or flashing lights. "
                "Common triggers include TV screens, video games, disco lights, and sunlight through trees or windows.\n\n"
                "Protective strategies:\n"
                "• Sit at least 2 metres from screens\n"
                "• Use matte screen filters\n"
                "• Wear blue-light filtering glasses\n"
                "• Cover one eye when exposed to potential flicker\n\n"
                "⚕️ *Ask your neurologist about photosensitivity testing (photic stimulation during EEG).*")

    # WHAT TO TELL DOCTOR
    elif any(w in text for w in ["doctor", "neurologist", "tell", "appointment", "report"]):
        response = "**What to tell your neurologist:**\n\n"
        response += f"From your Cerelog data ({total_logs} days logged, {total_seizures} seizures recorded):\n\n"
        top_triggers, patterns = analyze_triggers()
        if top_triggers:
            response += "**Potential triggers identified:**\n"
            for t in top_triggers[:3]:
                response += f"• {t['trigger']['icon']} {t['trigger']['label']} (seen {t['count']} time(s) before seizures)\n"
        if patterns:
            response += "\n**Data patterns:**\n"
            for p in patterns:
                response += f"• {p}\n"
        missed = sum(1 for l in logs.values() if "missed" in l.get("medication","").lower())
        if missed:
            response += f"\n• {missed} missed medication day(s) logged\n"
        response += "\nYou can also use the **Export for Doctor** button in the sidebar to download your full data as a file to bring to your appointment."
        return response

    # GREETING
    elif any(w in text for w in ["hi", "hello", "hey", "help"]):
        return (f"Hi! I am your Cerelog AI assistant. I can help you:\n\n"
                f"• Find your seizure triggers from your logged data\n"
                f"• Explain the science behind common triggers\n"
                f"• Predict tomorrow's risk based on today's health data\n"
                f"• Prepare questions for your neurologist\n\n"
                f"You have {total_logs} days logged and {total_seizures} seizures recorded. "
                f"What would you like to know?")

    # DEFAULT
    else:
        return (f"I am not sure I understood that perfectly — but here is what I can help with:\n\n"
                f"• **Triggers** — ask 'what are my triggers?'\n"
                f"• **Sleep** — ask 'why does sleep affect seizures?'\n"
                f"• **Stress** — ask 'how does stress affect my risk?'\n"
                f"• **Risk** — ask 'what is my risk tomorrow?'\n"
                f"• **Doctor** — ask 'what should I tell my doctor?'\n\n"
                f"You have {total_logs} days logged and {total_seizures} seizures recorded.\n\n"
                f"⚕️ *I can make mistakes. Always verify important health information with your neurologist.*")

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div class="main-header" style="font-size:1.5rem;">🧠 CERELOG</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Seizure Pattern Diary</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<div class="section-title">Color Theme</div>', unsafe_allow_html=True)
    scheme_choice = st.selectbox("Theme", list(SCHEMES.keys()),
                                  index=list(SCHEMES.keys()).index(st.session_state.scheme_name),
                                  label_visibility="collapsed")
    if scheme_choice != st.session_state.scheme_name:
        st.session_state.scheme_name = scheme_choice
        st.rerun()

    st.markdown("---")
    st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
    st.metric("Days logged", len(st.session_state.logs))
    st.metric("Seizures recorded", len(st.session_state.seizures))

    st.markdown("---")
    if st.button("📤 Export for Doctor", use_container_width=True):
        export_data = {
            "exported": datetime.now().isoformat(),
            "logs": st.session_state.logs,
            "seizures": st.session_state.seizures
        }
        st.download_button(
            "⬇️ Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name=f"cerelog_export_{date.today()}.json",
            mime="application/json",
            use_container_width=True
        )

    st.markdown(f"""
    <div class="disclaimer">
    ⚕️ <strong>Medical disclaimer</strong><br>
    Cerelog is not a medical device and does not provide medical advice.
    All information is for personal tracking purposes only.
    Always consult your neurologist before making any changes to your treatment.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
if st.session_state.show_confetti:
    show_confetti()
    st.session_state.show_confetti = False

st.markdown(f'<div class="main-header">CERELOG</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">AI-powered seizure pattern diary — log, detect, predict</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Daily Log", "⚡ Log Seizure", "📊 Patterns", "🤖 AI Chat", "🔮 Tomorrow's Risk"
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
        sleep_hours = st.slider("😴 Hours of sleep", 0.0, 12.0,
                                float(existing.get("sleep_hours", 7.0)), 0.5)
        stress = st.slider("😤 Stress level (1=calm, 10=extreme)", 1, 10,
                           int(existing.get("stress", 3)))
        food = st.slider("🍽️ Food quality (1=poor, 10=great)", 1, 10,
                         int(existing.get("food", 7)))

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**😊 Mood — split by time of day**")
        mood_options = ["😊 Happy", "😌 Calm", "😐 Neutral", "😢 Sad", "😰 Anxious", "😤 Irritable", "😴 Exhausted"]
        mood_am = st.selectbox("Morning", mood_options,
                               index=mood_options.index(existing.get("mood_am", "😊 Happy")) if existing.get("mood_am") in mood_options else 0)
        mood_pm = st.selectbox("Afternoon", mood_options,
                               index=mood_options.index(existing.get("mood_pm", "😌 Calm")) if existing.get("mood_pm") in mood_options else 1)
        mood_eve = st.selectbox("Evening", mood_options,
                                index=mood_options.index(existing.get("mood_eve", "😌 Calm")) if existing.get("mood_eve") in mood_options else 1)

    with col4:
        exercise_opts = ["None", "Light walk", "Moderate", "Intense workout"]
        med_opts = ["Yes — on time", "Yes — late", "Missed dose", "No medication prescribed"]
        exercise = st.selectbox("🏃 Exercise", exercise_opts,
                                index=exercise_opts.index(existing.get("exercise", "None")) if existing.get("exercise") in exercise_opts else 0)
        medication = st.selectbox("💊 Medication taken", med_opts,
                                  index=med_opts.index(existing.get("medication", "Yes — on time")) if existing.get("medication") in med_opts else 0)

        st.markdown("**⚡ Any known triggers today?**")
        trigger_checks = {}
        for lt in LIFESTYLE_TRIGGERS[:7]:
            trigger_checks[lt] = st.checkbox(lt, value=existing.get(f"trigger_{lt}", False))

    notes = st.text_area("📝 Notes", value=existing.get("notes", ""),
                         placeholder="Anything unusual? Headache, aura, feeling off...", height=80)

    if st.button("💾 Save Daily Log", use_container_width=True):
        entry = {
            "sleep_hours": sleep_hours, "stress": stress, "food": food,
            "mood_am": mood_am, "mood_pm": mood_pm, "mood_eve": mood_eve,
            "exercise": exercise, "medication": medication, "notes": notes
        }
        for lt, val in trigger_checks.items():
            entry[f"trigger_{lt}"] = val
        st.session_state.logs[log_date_str] = entry
        st.session_state.show_confetti = True
        st.success(f"✓ Log saved for {log_date_str}! 🎉")
        st.rerun()

    st.markdown(f"""
    <div class="disclaimer">
    ⚕️ This app is for personal tracking only. It is not a medical device.
    Always share your logs with your neurologist.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 2 — LOG SEIZURE
# ─────────────────────────────────────────────
with tab2:
    st.markdown('<div class="section-title">Log a Seizure Event</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-card">
    <div style="font-size:0.85rem; color:{C['muted']};">
    Research shows that 60-70% of people with epilepsy can identify personal triggers once they start tracking.
    The more detail you log, the better the AI can find your patterns.
    </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        sz_date = st.date_input("Date", value=date.today(), key="sz_date")
        sz_time = st.time_input("Approximate time", key="sz_time")
        severity = st.slider("Severity (1=mild, 10=severe)", 1, 10, 5)
        duration = st.number_input("Duration (minutes)", 0, 120, 2)
        location = st.text_input("Where were you?", placeholder="home, school, outdoors...")

    with col2:
        before = st.text_area("What were you doing before?",
                              placeholder="watching a movie, just woke up, exercising...", height=90)
        activities = st.text_area("Activities in the past 2 hours?",
                                  placeholder="video games, swimming, studying...", height=70)
        strobe = st.selectbox("Flashing / flickering lights?",
                              ["No", "Yes — TV/screen", "Yes — sunlight flickering",
                               "Yes — other", "Unsure"])
        who_with = st.text_input("Who were you with?",
                                 placeholder="alone, with family, at school...")
        sz_notes = st.text_area("Anything else?",
                                placeholder="missed medication, poor sleep, high stress...", height=70)

    if st.button("⚡ Log This Seizure", use_container_width=True):
        entry = {
            "datetime": f"{sz_date} {sz_time}",
            "severity": severity, "duration": duration,
            "location": location, "before": before,
            "activities": activities, "strobe": strobe,
            "who_with": who_with, "notes": sz_notes
        }
        st.session_state.seizures.append(entry)
        st.session_state.show_confetti = True
        st.success("✓ Seizure logged.")
        st.rerun()

    if st.session_state.seizures:
        st.markdown("---")
        st.markdown('<div class="section-title">Seizure History</div>', unsafe_allow_html=True)
        for s in reversed(st.session_state.seizures):
            st.markdown(f"""
            <div class="seizure-card">
            <strong>{s.get('datetime','?')}</strong> — Severity {s.get('severity','?')}/10
            — {s.get('duration','?')} min<br>
            <small style="color:{C['muted']};">Before: {s.get('before','?')}</small><br>
            <small style="color:{C['muted']};">Strobe: {s.get('strobe','?')}
            | Location: {s.get('location','?')}</small>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 3 — PATTERNS
# ─────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">Patterns & Trigger Analysis</div>', unsafe_allow_html=True)

    if len(st.session_state.logs) < 2:
        st.info("Log at least 2 days of data to see patterns.")
    else:
        rows = []
        for d, log in sorted(st.session_state.logs.items()):
            row = {"date": d}
            row.update(log)
            row["had_seizure"] = any(
                str(s.get("datetime",""))[:10] == d
                for s in st.session_state.seizures
            )
            rows.append(row)

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"])
        seizure_days = df[df["had_seizure"] == True]

        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df["date"], y=df["sleep_hours"],
                mode="lines+markers", line=dict(color=C['accent2'], width=2),
                marker=dict(size=6), name="Sleep hrs"))
            if not seizure_days.empty:
                fig.add_trace(go.Scatter(x=seizure_days["date"], y=seizure_days["sleep_hours"],
                    mode="markers", marker=dict(color=C['alert'], size=14, symbol="x-thin", line=dict(width=3)),
                    name="Seizure day"))
            fig.update_layout(title="Sleep Hours", paper_bgcolor=C['bg'],
                plot_bgcolor=C['panel'], font=dict(color=C['text'], size=11),
                height=260, margin=dict(l=40,r=20,t=40,b=40))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df["date"], y=df["stress"],
                mode="lines+markers", line=dict(color=C['warn'], width=2),
                marker=dict(size=6), name="Stress"))
            if not seizure_days.empty:
                fig2.add_trace(go.Scatter(x=seizure_days["date"], y=seizure_days["stress"],
                    mode="markers", marker=dict(color=C['alert'], size=14, symbol="x-thin", line=dict(width=3)),
                    name="Seizure day"))
            fig2.update_layout(title="Stress Level", paper_bgcolor=C['bg'],
                plot_bgcolor=C['panel'], font=dict(color=C['text'], size=11),
                height=260, margin=dict(l=40,r=20,t=40,b=40))
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.markdown('<div class="section-title">Your Top Triggers</div>', unsafe_allow_html=True)

        top_triggers, patterns = analyze_triggers()
        if not top_triggers:
            st.info("Log more seizure events to see trigger analysis.")
        else:
            for t in top_triggers:
                trig = t["trigger"]
                st.markdown(f"""
                <div class="metric-card">
                <strong>{trig['icon']} {trig['label']}</strong>
                — appeared <strong>{t['count']}</strong> time(s) before a seizure<br>
                <small style="color:{C['muted']};">{trig['science']}</small>
                </div>
                """, unsafe_allow_html=True)

        if patterns:
            st.markdown("---")
            st.markdown('<div class="section-title">Data Patterns</div>', unsafe_allow_html=True)
            for p in patterns:
                st.markdown(f'<span class="trigger-tag">📊 {p}</span>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="disclaimer">
    ⚕️ These patterns are based on your personal logged data only.
    They are not a medical diagnosis. Share findings with your neurologist.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# TAB 4 — AI CHAT
# ─────────────────────────────────────────────
with tab4:
    st.markdown('<div class="section-title">AI Health Assistant</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="disclaimer" style="margin-bottom:1rem;">
    🤖 This AI uses rule-based reasoning on your logged data + research-backed epilepsy knowledge.
    It can make mistakes. Always verify with your neurologist.
    </div>
    """, unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        css_class = "user-bubble" if msg["role"] == "user" else "ai-bubble"
        prefix = "You" if msg["role"] == "user" else "Cerelog AI"
        st.markdown(f'<div class="{css_class}"><strong>{prefix}:</strong> {msg["content"]}</div>',
                    unsafe_allow_html=True)

    st.markdown("**Quick questions:**")
    qcols = st.columns(3)
    quick_qs = [
        ("🔍 My triggers", "What are my triggers based on my data?"),
        ("😴 Sleep science", "Why does sleep affect seizures?"),
        ("🏥 For my doctor", "What should I tell my neurologist?"),
    ]
    for i, (label, question) in enumerate(quick_qs):
        with qcols[i]:
            if st.button(label, use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": question})
                response = chatbot_response(question)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()

    if (st.session_state.chat_history and
            st.session_state.chat_history[-1]["role"] == "user"):
        last = st.session_state.chat_history[-1]["content"]
        response = chatbot_response(last)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

    user_input = st.text_input("Ask anything...",
                               placeholder="What are my triggers? Why does stress cause seizures?",
                               key="chat_input")
    col_send, col_clear = st.columns([3, 1])
    with col_send:
        if st.button("Send →", use_container_width=True):
            if user_input.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_input})
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
        st.warning("Log today's health data in the Daily Log tab first.")
    else:
        if st.button("🔮 Predict Tomorrow's Risk", use_container_width=True):
            level, factors, rec = predict_risk_tomorrow()
            color_map = {"HIGH": C['alert'], "MODERATE": C['warn'], "LOW": C['safe']}
            color = color_map.get(level, C['muted'])
            css_class = {"HIGH": "risk-high", "MODERATE": "risk-med", "LOW": "risk-low"}.get(level, "")

            st.markdown(f"""
            <div class="metric-card" style="border-color:{color}; text-align:center;">
            <div style="font-size:0.7rem; color:{C['muted']}; font-family:'Space Mono',monospace;
                        text-transform:uppercase; letter-spacing:0.1em;">Tomorrow's predicted risk</div>
            <div class="{css_class}">{level}</div>
            </div>
            """, unsafe_allow_html=True)

            if factors:
                st.markdown("**Risk factors from today:**")
                for f in factors:
                    st.markdown(f'<span class="trigger-tag">{f}</span>', unsafe_allow_html=True)

            st.markdown(f"""
            <div class="ai-bubble" style="margin-top:1rem;">
            <strong>Recommendation for tonight:</strong><br>{rec}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div class="metric-card">
    <div style="font-size:0.72rem; color:{C['dim']}; font-family:'Space Mono',monospace;
                text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem;">How this works</div>
    <div style="font-size:0.88rem; color:{C['muted']}; line-height:1.7;">
    The AI scores today's sleep, stress, medication, food, and mood against research-backed
    thresholds for seizure risk. It cross-references with your personal seizure history to
    weight factors that have appeared before your own seizure events.
    Sleep deprivation, missed medication, and high stress are the three most common
    modifiable seizure triggers in clinical research.
    </div>
    </div>
    <div class="disclaimer">
    ⚕️ This prediction is an estimate based on population research and your personal data.
    It is not a medical diagnosis. This AI can make mistakes.
    Always consult your neurologist for medical advice.
    </div>
    """, unsafe_allow_html=True)
