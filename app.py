<code class="language-python">import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
API_KEY = "***"
API_URL = "https://api.groq.com/openai/v1/chat/completions"

st.set_page_config(page_title="Celebro Summary Hub", page_icon="🧠", layout="centered")

# Custom CSS
st.markdown("<style>.stButton>button { width: 100%; border-radius: 20px; background-color: #ef1a2d; color: white; }</style>", unsafe_allow_html=True)

# --- DATABASE ---
def load_data():
    try:
        return pd.read_csv("summaries.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Date", "URL", "Summary"])

def save_data(df):
    df.to_csv("summaries.csv", index=False)

# --- LOGIC ---
def fetch_content(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        return soup.get_text()[:10000]
    except:
        return "Could not retrieve content from URL."

def generate_summary(text):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-8b-8192", 
        "messages": [{"role": "system", "content": "You are Celebro. Provide a concise summary."},
                     {"role": "user", "content": text}]
    }
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        return response.json()['choices'][0]['message']['content']
    except:
        return "AI Error: Please check your API Key."

# --- UI ---
st.title("🧠 Celebro Summary Hub")
st.subheader("Your permanent archive of insights")

with st.form("input_form"):
    url_input = st.text_input("Paste your resource link here:")
    submit = st.form_submit_button("Generate Summary")

if submit and url_input:
    with st.spinner("Celebro is thinking..."):
        content = fetch_content(url_input)
        summary = generate_summary(content)
        
        df = load_data()
        new_entry = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), url_input, summary]], 
                                 columns=["Date", "URL", "Summary"])
        df = pd.concat([df, new_entry], ignore_index=True)
        save_data(df)
        st.success("Summary generated and saved!")

# --- DISPLAY HISTORY ---
st.divider()
st.write("### 📚 Previous Summaries")
df_history = load_data()

if not df_history.empty:
    for index, row in df_history.iloc[::-1].iterrows():
        st.write(f"**{row['Date']}** - [{row['URL']}]({row['URL']})")
        st.write(row['Summary'])
        st.divider()
else:
    st.info("No summaries yet. Paste a link above to start!")
</code>
