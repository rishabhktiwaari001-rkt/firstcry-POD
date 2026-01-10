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
        # Checks against the password in Secrets (or defaults to Firstcry2026)
        secret_pass = st.secrets.get("APP_PASSWORD", "Firstcry2026") 
        if password == secret_pass:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("❌ Incorrect Password")

if not st.session_state["logged_in"]:
    check_login()
    st.stop()

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
        "summary": "A comprehensive bulleted summary in English. It MUST cover every single feature, specification, material detail, and age recommendation mentioned in the input text. Do not leave out any technical details.",
        
        "pitch_hinglish": "A detailed and persuasive sales pitch in 'Hinglish' (Hindi + English mix). IMPORTANT: You must incorporate EVERY single product specification (dimensions, weight, safety, materials, etc.) found in the input text into this pitch. Do not skip any features. Make it sound natural but ensure 100% of the product details are covered.",
        
        "quiz": [
            {{
                "question": "Question 1 in Hinglish covering a specific feature",
                "options": ["Option A", "Option B", "Option C"],
                "correct_index": 0 
            }},
            ... (Generate exactly 5 questions based on different features)
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

# --- VIEW 1: STUDY MODE (Shows Summary & Pitch) ---
if not st.session_state['test_mode']:
    
    st.info("ℹ️ Step 1: Generate Training -> Step 2: Read Pitch -> Step 3: Start Test")
    
    # Input Box
    if not st.session_state['generated_content']:
        product_input = st.text_area("Paste Product Details Here:", height=150)
        if st.button("Generate Training Module"):
            if product_input:
                with st.spinner("Creating Summary, Pitch, and Quiz..."):
                    data = generate_training_material(product_input)
                    if data:
                        st.session_state['generated_content'] = data
                        st.rerun()
            else:
                st.warning("Please paste product details first.")

    # Show Content (Summary + Pitch)
    if st.session_state['generated_content']:
        data = st.session_state['generated_content']
        
        st.markdown("---")
        st.subheader("📌 Product Summary")
        st.info(data['summary'])
        
        st.markdown("---")
        st.subheader("🗣️ Sales Pitch (Hindi)")
        st.markdown(f"<div class='hindi-text'>{data['pitch_hinglish']}</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.warning("⚠️ Once you click 'Start Test', the summary and pitch will disappear!")
        
        if st.button("🔒 Lock Content & Start Test"):
            st.session_state['test_mode'] = True
            st.rerun()

# --- VIEW 2: EXAM MODE (Summary Hidden + Anti-Cheat Locked Inputs) ---
else:
    data = st.session_state['generated_content']
    
    st.markdown("### 📝 Knowledge Check")
    st.info("The study material is now hidden. Good luck!")
    
    # STAFF NAME INPUT
    staff_name = st.text_input("Enter Staff Name (Required):", disabled=st.session_state['quiz_submitted'])
    
    if staff_name:
        # Determine if inputs should be disabled (locked)
        is_locked = st.session_state['quiz_submitted']

        with st.form("quiz_form"):
            user_answers = {}
            for i, q in enumerate(data['quiz']):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                # KEY CHANGE: 'disabled=is_locked' prevents changing answers after submit
                user_answers[i] = st.radio(
                    f"Select answer:", 
                    q['options'], 
                    key=f"q{i}", 
                    index=None, 
                    disabled=is_locked 
                )
                st.write("") # Spacer
            
            # Show Submit Button only if NOT yet submitted
            submit_button = st.form_submit_button("Submit Test", disabled=is_locked)

            if submit_button:
                st.session_state['quiz_submitted'] = True
                st.rerun()

        # --- RESULTS SECTION (Runs outside the form so it persists) ---
        if st.session_state['quiz_submitted']:
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
            
            # Final Score Logic
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

    # Reset Button
    st.markdown("---")
    if st.button("🔄 Start New Product Training"):
        st.session_state['generated_content'] = None
        st.session_state['test_mode'] = False
        st.session_state['quiz_submitted'] = False
        st.rerun()
