import streamlit as st
import openai
import json

# --- CONFIGURATION ---
# In a real production environment, use st.secrets for the API key
# st.secrets["OPENAI_API_KEY"]
api_key = "YOUR_OPENAI_API_KEY_HERE" 

client = openai.OpenAI(api_key=api_key)

st.set_page_config(page_title="FirstCry Daily Training", layout="centered")

# --- CSS STYLING ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; color: #E91E63; font-weight: bold; }
    .hindi-text { font-family: 'Arial', sans-serif; font-size: 18px; }
    .stButton>button { background-color: #E91E63; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE MANAGEMENT ---
if 'generated_content' not in st.session_state:
    st.session_state['generated_content'] = None
if 'quiz_submitted' not in st.session_state:
    st.session_state['quiz_submitted'] = False

# --- AI GENERATION FUNCTION (UPDATED FOR COMPREHENSIVE COVERAGE) ---
def generate_training_material(product_text):
    prompt = f"""
    You are a professional retail trainer for FirstCry.
    Context: Use the following product details: "{product_text}"
    
    Output strictly in JSON format with the following structure:
    {{
        "summary": "A comprehensive bulleted summary in English. It MUST cover every single feature, specification, material detail, and age recommendation mentioned in the input text. Do not leave out any technical details.",
        
        "pitch_hinglish": "A detailed and persuasive sales pitch in 'Hinglish' (Hindi + English mix). IMPORTANT: You must incorporate EVERY single product specification (dimensions, weight, safety, materials, etc.) found in the input text into this pitch. Do not skip any features. Make it sound natural but ensure 100% of the product details are covered. Example: 'Madam, iska frame aluminium ka hai jo isko lightweight banata hai, aur isme 5-point safety harness bhi diya gaya hai.'",
        
        "quiz": [
            {{
                "question": "Question 1 in Hinglish covering a specific feature",
                "options": ["Option A", "Option B", "Option C"],
                "correct_index": 0 
            }},
            ... (Generate exactly 10 questions based on different features)
        ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o", # or gpt-3.5-turbo
            response_format={ "type": "json_object" },
            messages=[{"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                      {"role": "user", "content": prompt}]
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error generating content: {e}")
        return None

# --- UI LAYOUT ---
st.image("https://cdn.fcglcdn.com/brainbees/images/n/fc_logo.png", width=150)
st.title("FirstCry Product of the Day Tool")
st.markdown("Enter the raw product details below to generate daily training material.")

# Input Section
product_input = st.text_area("Paste Product Details Here:", height=150)

if st.button("Generate Training Module"):
    if product_input:
        with st.spinner("Creating Summary, Pitch, and Quiz..."):
            data = generate_training_material(product_input)
            if data:
                st.session_state['generated_content'] = data
                st.session_state['quiz_submitted'] = False
    else:
        st.warning("Please enter product details first.")

# Display Generated Content
if st.session_state['generated_content']:
    data = st.session_state['generated_content']
    
    # 1. Summary Section
    st.markdown("---")
    st.subheader("📌 Product Summary")
    st.info(data['summary'])
    
    # 2. Hindi Sales Pitch
    st.markdown("---")
    st.subheader("🗣️ Sales Pitch (Hindi)")
    st.markdown(f"<div class='hindi-text'>{data['pitch_hinglish']}</div>", unsafe_allow_html=True)
    
    # 3. Quiz Section
    st.markdown("---")
    st.subheader("📝 Daily Knowledge Check")
    
    user_answers = {}
    
    with st.form("quiz_form"):
        for i, q in enumerate(data['quiz']):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            user_answers[i] = st.radio(f"Select answer for Q{i+1}", q['options'], key=f"q{i}", index=None)
            st.write("") # Spacer
        
        submit_button = st.form_submit_button("Submit Test")

        if submit_button:
            score = 0
            total = len(data['quiz'])
            
            # Grading Logic
            st.markdown("### Results:")
            for i, q in enumerate(data['quiz']):
                correct_option = q['options'][q['correct_index']]
                user_choice = user_answers.get(i)
                
                if user_choice == correct_option:
                    score += 1
                    st.success(f"Q{i+1}: Correct! ({correct_option})")
                else:
                    st.error(f"Q{i+1}: Incorrect. The correct answer was: {correct_option}")
            
            st.session_state['quiz_submitted'] = True
            
            # Final Score Display
            if score == total:
                st.balloons()
                st.markdown(f"### 🏆 Perfect Score: {score}/{total}")
            elif score >= total/2:
                st.markdown(f"### ✅ Pass: {score}/{total}")
            else:
                st.markdown(f"### ❌ Needs Review: {score}/{total}")