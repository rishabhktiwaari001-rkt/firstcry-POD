import streamlit as st
import openai
import json

# --- 1. CONFIGURATION & SECRETS ---
st.set_page_config(page_title="FirstCry Daily Training", layout="centered")

# Check for API Key
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    st.error("🚨 API Key missing! Please go to Settings > Secrets and add OPENAI_API_KEY.")
    st.stop()

client = openai.OpenAI(api_key=api_key)

# --- 2. LOGIN SYSTEM (Gatekeeper) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def check_login():
    st.markdown("### 🔒 FirstCry Staff Login")
    password = st.text_input("Enter Store Password", type="password")
    if st.button("Login"):
        # Ensure you added APP_PASSWORD in your Secrets, or change "1234" to your default here
        secret_pass = st.secrets.get("APP_PASSWORD", "FirstCry2026") 
        if password == secret_pass:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("❌ Incorrect Password")

if not st.session_state["logged_in"]:
    check_login()
    st.stop() # Stops the app here if not logged in

# --- 3. SESSION STATE INITIALIZATION ---
if 'generated_content' not in st.session_state:
    st.session_state['generated_content'] = None
if 'test_mode' not in st.session_state:
    st.session_state['test_mode'] = False
if 'quiz_submitted' not in st.session_state:
    st.session_state['quiz_submitted'] = False

# --- 4. CSS STYLING ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; color: #E91E63; font-weight: bold; }
    .hindi-text { font-family: 'Arial', sans-serif; font-size: 18px; color: #333; background-color: #f0f2f6; padding: 15px; border-radius: 10px; }
    .stButton>button { background-color: #E91E63; color: white; width: 100%; }
    .success-box { padding: 15px; background-color: #d4edda; color: #155724; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. AI GENERATION FUNCTION ---
def generate_training_material(product_text):
    prompt = f"""
    You are a professional retail trainer for FirstCry.
    Context: Use the following product details: "{product_text}"
    
    Output strictly in JSON format with this structure:
    {{
        "summary": "Key features bullet points (English). Cover safety, material, age, etc.",
        "pitch_hinglish": "A natural Hindi+English sales pitch. Include ALL technical specs like dimensions/materials naturally. Example: 'Madam, iska frame aluminium ka hai...'",
        "quiz": [
            {{
                "question": "Question 1 (Hinglish)",
                "options": ["Option A", "Option B", "Option C"],
                "correct_index": 0 
            }},
            ... (Generate exactly 5 questions)
        ]
    }}
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            response_format={ "type": "json_object" },
            messages=[{"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                      {"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error generating content: {e}")
        return None

# --- 6. APP UI LOGIC ---

# HEADER
st.image("https://cdn.fcglcdn.com/brainbees/images/n/fc_logo.png", width=150)
st.title("FirstCry Product of the Day")

# --- VIEW 1: INPUT & STUDY MODE (Only shows if NOT in Test Mode) ---
if not st.session_state['test_mode']:
    
    st.info("ℹ️ Step 1: Generate Training -> Step 2: Read Pitch -> Step 3: Start Test")
    
    # Only show input box if content is not yet generated
    if not st.session_state['generated_content']:
        product_input = st.text_area("Paste Product Details Here:", height=150)
        if st.button("Generate Training Module"):
            if product_input:
                with st.spinner("Creating Training Module..."):
                    data = generate_training_material(product_input)
                    if data:
                        st.session_state['generated_content'] = data
                        st.rerun()
            else:
                st.warning("Please paste product details first.")

    # If content exists, show the Study Material
    if st.session_state['generated_content']:
        data = st.session_state['generated_content']
        
        st.markdown("---")
        st.subheader("📌 Product Summary (Read Carefully)")
        st.info(data['summary'])
        
        st.markdown("---")
        st.subheader("🗣️ Sales Pitch (Hindi)")
        st.markdown(f"<div class='hindi-text'>{data['pitch_hinglish']}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.warning("⚠️ Once you click 'Start Test', this content will disappear!")
        
        if st.button("🔒 Lock Content & Start Test"):
            st.session_state['test_mode'] = True
            st.rerun()

# --- VIEW 2: EXAM MODE (Only shows if Test Mode IS Active) ---
else:
    data = st.session_state['generated_content']
    
    st.markdown("### 📝 Knowledge Check")
    st.info("The study material is now hidden. Good luck!")
    
    # STAFF NAME INPUT
    staff_name = st.text_input("Enter Staff Name (Required):")
    
    if staff_name:
        with st.form("quiz_form"):
            user_answers = {}
            for i, q in enumerate(data['quiz']):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                user_answers[i] = st.radio(f"Select answer:", q['options'], key=f"q{i}", index=None)
                st.write("") # Spacer
            
            submit_button = st.form_submit_button("Submit Test")

            if submit_button:
                score = 0
                total = len(data['quiz'])
                
                st.markdown("---")
                st.markdown(f"### 📊 Result for: **{staff_name}**")
                
                for i, q in enumerate(data['quiz']):
                    correct_idx = int(q['correct_index'])
                    correct_option = q['options'][correct_idx]
                    user_choice = user_answers.get(i)
                    
                    if user_choice == correct_option:
                        score += 1
                        st.success(f"Q{i+1}: ✅ Correct")
                    else:
                        st.error(f"Q{i+1}: ❌ Wrong. Correct: {correct_option}")
                
                # Final Score
                percentage = (score / total) * 100
                if percentage == 100:
                    st.balloons()
                    st.success(f"🏆 PERFECT SCORE! {score}/{total}")
                elif percentage >= 50:
                    st.warning(f"✅ PASSED: {score}/{total}")
                else:
                    st.error(f"❌ FAILED: {score}/{total} - Please read again.")
                    
    else:
        st.warning("Please enter your name to see the questions.")

    # Reset Button to start over
    st.markdown("---")
    if st.button("🔄 Start New Product Training"):
        st.session_state['generated_content'] = None
        st.session_state['test_mode'] = False
        st.session_state['quiz_submitted'] = False
        st.rerun()
