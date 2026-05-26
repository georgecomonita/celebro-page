import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import os

# --- CONFIGURATION ---
API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Celebro Summary Hub",
    page_icon="🧠",
    layout="centered"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
.stButton > button {
    width: 100%;
    border-radius: 20px;
    background-color: #ef1a2d;
    color: white;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- DATABASE FUNCTIONS ---
def load_data():
    try:
        return pd.read_csv("summaries.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "URL", "Summary"])

def save_data(df):
    df.to_csv("summaries.csv", index=False)

# --- FETCH WEBSITE CONTENT ---
def fetch_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script/style tags
        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text(separator=" ", strip=True)

        return text[:10000]

    except Exception as e:
        return f"Could not retrieve content from URL.\nError: {e}"

# --- GENERATE AI SUMMARY ---
def generate_summary(text):

    if not API_KEY:
        return "Missing GROQ_API_KEY environment variable."

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Celebro, an AI assistant that creates concise, "
                    "clear summaries of articles, webpages, and resources."
                )
            },
            {
                "role": "user",
                "content": text
            }
        ],
        "temperature": 0.5,
        "max_tokens": 300
    }

    try:
        response = requests.post(
            API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"AI Error: {e}"

# --- UI ---
st.title("🧠 Celebro Summary Hub")
st.subheader("Your permanent archive of insights")

with st.form("input_form"):

    url_input = st.text_input(
        "Paste your resource link here:"
    )

    submit = st.form_submit_button(
        "Generate Summary"
    )

# --- PROCESS INPUT ---
if submit and url_input:

    with st.spinner("Celebro is thinking..."):

        content = fetch_content(url_input)

        summary = generate_summary(content)

        df = load_data()

        new_entry = pd.DataFrame(
            [[
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                url_input,
                summary
            ]],
            columns=["Date", "URL", "Summary"]
        )

        df = pd.concat(
            [df, new_entry],
            ignore_index=True
        )

        save_data(df)

        st.success("Summary generated and saved!")

        st.write("### ✨ Generated Summary")
        st.write(summary)

# --- HISTORY ---
st.divider()

st.write("### 📚 Previous Summaries")

df_history = load_data()

if not df_history.empty:

    for _, row in df_history.iloc[::-1].iterrows():

        st.write(
            f"**{row['Date']}** - "
            f"[Open Link]({row['URL']})"
        )

        st.write(row["Summary"])

        st.divider()

else:
    st.info(
        "No summaries yet. Paste a link above to start!"
    )
