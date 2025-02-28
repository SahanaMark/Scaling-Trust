import streamlit as st
import requests
import firebase_admin
import google.generativeai as genai
from firebase_admin import credentials, firestore

# Load Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_keys.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Perspective API Key
PERSPECTIVE_API_KEY = "AIzaSyB113fKzZfa4iqpcs63wbHRRo1CGC5uWBA"
PERSPECTIVE_URL = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"

# GenAI API Key
GOOGLE_GENAI_API_KEY = "YOUR_GEMINI_API_KEY"  # Replace with your API Key
genai.configure(api_key=GOOGLE_GENAI_API_KEY)

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

def rewrite_post(text):
    """ Uses Google's GenAI (Gemini API) to rewrite a flagged post in a neutral/positive tone. """
    model = genai.GenerativeModel("gemini-pro")
    prompt = f"""
    The following text may contain offensive or inappropriate content:
    
    "{text}"
    
    Please rewrite it in a more positive, neutral, and respectful tone while maintaining its original intent.
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def handle_toxicity(text, toxicity_score):
    """ Handles the post based on toxicity level and rewrites flagged content. """
    if toxicity_score > 7:
        return "🚫 Post Blocked: Contains excessive toxicity!"
    
    elif 1 < toxicity_score < 4:
        db.collection("flagged_posts").add({"post": text, "toxicity_score": toxicity_score})
        rewritten_text = rewrite_post(text)
        return f"⚠️ Post Flagged & Rewritten:\n\n**New Version:** {rewritten_text}"
    
    elif toxicity_score < 1:
        return text

    else:
        # Save to Firebase and Rewrite
        db.collection("flagged_posts").add({"post": text, "toxicity_score": toxicity_score})
        rewritten_text = rewrite_post(text)
        return f"⚠️ Post Flagged & Rewritten:\n\n**New Version:** {rewritten_text}"


# Streamlit UI
st.title("🛡️ Social Media Toxicity Checker with GenAI")

user_input = st.text_area("Enter your post:")
if st.button("Analyze"):
    if user_input.strip():
        toxicity_score = analyze_toxicity(user_input)
        decision = handle_toxicity(user_input, toxicity_score)
        st.write(f"🔍 **Toxicity Score:** {toxicity_score:.2f}")
        st.warning(decision)
    else:
        st.error("Please enter a post to analyze.")
