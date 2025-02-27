#AIzaSyB113fKzZfa4iqpcs63wbHRRo1CGC5uWBA
import streamlit as st
import requests
import firebase_admin
from firebase_admin import credentials, firestore

# Load Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Perspective API Key
PERSPECTIVE_API_KEY = "AIzaSyB113fKzZfa4iqpcs63wbHRRo1CGC5uWBA"
PERSPECTIVE_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"

def analyze_toxicity(text):
    """ Sends text to Perspective API and returns toxicity score. """
    payload = {
        "comment": {"text": text},
        "languages": ["en"],
        "requestedAttributes": {"TOXICITY": {}}
    }
    response = requests.post(f"{PERSPECTIVE_URL}?key={PERSPECTIVE_API_KEY}", json=payload)
    data = response.json()
    return data["attributeScores"]["TOXICITY"]["summaryScore"]["value"] * 10  # Scale 0-10

def handle_toxicity(text, toxicity_score):
    """ Handles the post based on toxicity level. """
    if toxicity_score > 6:
        return "🚫 Post Blocked: Contains excessive toxicity!"
    elif toxicity_score < 4:
        db.collection("1").add({"post": text, "toxicity_score": toxicity_score})
        return "⚠️ Post Flagged: This may need review."
    elif toxicity_score < 1:
        return text
    else:
        # Save to Firebase
        
        db.collection("1").add({"post": text, "toxicity_score": toxicity_score})
        return "⚠️ Post Flagged & Sent to Firebase for Review."

# Streamlit UI
st.title("🛡️ Social Media Toxicity Checker")

user_input = st.text_area("Enter your post:")
if st.button("Analyze"):
    if user_input.strip():
        toxicity_score = analyze_toxicity(user_input)
        decision = handle_toxicity(user_input, toxicity_score)
        st.write(f"🔍 **Toxicity Score:** {toxicity_score:.2f}")
        st.warning(decision)
    else:
        st.error("Please enter a post to analyze.")
