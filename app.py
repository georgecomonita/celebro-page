import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import os
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
API_KEY = os.getenv("GROQ_API_KEY")
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Celebro Summary Hub",
    page_icon="🧠",
    layout="centered"
)

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


# --- DATA ---
def load_data():
    try:
        return pd.read_csv("summaries.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "URL", "Summary"])


def save_data(df):
    df.to_csv("summaries.csv", index=False)


# --- SCRAPER (FIXED) ---
def fetch_content(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # remove junk
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        # prefer article content
        article = soup.find("article")

        if article:
            text = article.get_text(separator=" ", strip=True)
        else:
            # fallback: main content only (less noise than full page)
            main = soup.find("main")
            text = main.get_text(separator=" ", strip=True) if main else soup.get_text(separator=" ", strip=True)

        text = " ".join(text.split())  # normalize spaces

        return text[:8000]  # limit for API safety

    except Exception as e:
        return f"SCRAPER_ERROR: {e}"


# --- AI SUMMARY (FIXED) ---
def generate_summary(text):

    if "SCRAPER_ERROR" in text:
        return "Cannot generate summary because page content could not be extracted."

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional news summarizer. "
                    "Return a structured summary with: "
                    "1. Title idea, 2. Key points, 3. Short conclusion."
                )
            },
            {
                "role": "user",
                "content": f"Summarize this article:\n\n{text}"
            }
        ],
        "temperature": 0.3,
        "max_tokens": 350
    }

    try:
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)

        # IMPORTANT DEBUG STEP
        if response.status_code != 200:
            return f"API_ERROR {response.status_code}: {response.text}"

        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"AI_ERROR: {e}"


# --- UI ---
st.title("🧠 Celebro Summary Hub")
st.subheader("Paste any article URL and get AI summary")

with st.form("input_form"):
    url_input = st.text_input("Paste your resource link here:")
    submit = st.form_submit_button("Generate Summary")


# --- RUN ---
if submit and url_input:

    with st.spinner("Fetching & summarizing..."):

        content = fetch_content(url_input)
        summary = generate_summary(content)

        df = load_data()

        new_entry = pd.DataFrame([[
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            url_input,
            summary
        ]], columns=["Date", "URL", "Summary"])

        df = pd.concat([df, new_entry], ignore_index=True)
        save_data(df)

        st.success("Done!")

        st.write("### ✨ Generated Summary")
        st.write(summary)


# --- HISTORY ---
st.divider()
st.write("### 📚 Previous Summaries")

df_history = load_data()

if not df_history.empty:
    for _, row in df_history.iloc[::-1].iterrows():
        st.write(f"**{row['Date']}** - [{row['URL']}]({row['URL']})")
        st.write(row["Summary"])
        st.divider()
else:
    st.info("No summaries yet.")
