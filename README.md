# Cerelog — AI Seizure Pattern Diary

A Streamlit web app for people with epilepsy to log daily health data, record seizure events, and use AI to identify personal triggers and predict risk.

## Features

- **Daily Log** — sleep, stress, mood (AM/PM/evening), food, exercise, medication
- **Seizure Log** — detailed event logging with trigger questions
- **Pattern Charts** — visualize sleep and stress against seizure days
- **AI Trigger Analysis** — AI finds your personal patterns and explains the science
- **AI Chat** — ask questions about your data anytime
- **Tomorrow's Risk** — daily risk prediction based on today's health data
- **Doctor Export** — download your full log as JSON to share with your neurologist

## Deploy on Streamlit Cloud

1. Fork this repo on GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add your Anthropic API key as a secret: `ANTHROPIC_API_KEY`
5. Deploy

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Built by
Cerelog — seizure prediction wearable project
