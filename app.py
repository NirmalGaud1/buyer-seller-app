import streamlit as st
import google.generativeai as genai
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="DealFixer AI", page_icon="🤝", layout="wide")

# Securely set up Gemini
API_KEY = "AIzaSyAK1drB0TgUHlf3JCsBZIYyEUQugLHhF5U"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- STYLING ---
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .deal-box { background-color: #d4edda; color: #155724; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #c3e6cb; }
    .fail-box { background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "round_count" not in st.session_state:
    st.session_state.round_count = 0
if "deal_fixed" not in st.session_state:
    st.session_state.deal_fixed = False
if "last_buyer_price" not in st.session_state:
    st.session_state.last_buyer_price = None

# --- UI SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Negotiation Settings")
    product_name = st.text_input("Product Name", value="iPhone 13 Pro")
    product_desc = st.text_area("Product Description", value="128GB, Graphite, 90% Battery Health, minor screen scratch.")
    pmax = st.number_input("AI Buyer Max Budget ($)", value=600)
    market_context = st.text_input("Market Context", value="High demand, but new model just released.")
    
    if st.button("Reset Negotiation"):
        st.session_state.messages = []
        st.session_state.round_count = 0
        st.session_state.deal_fixed = False
        st.session_state.last_buyer_price = None
        st.rerun()

# --- SYSTEM PROMPT ---
BUYER_SYSTEM_PROMPT = f"""
You are an AI Buyer negotiating on behalf of a customer for: {product_name}.
Description: {product_desc}
Market: {market_context}

RULES:
1. Your maximum budget is ${pmax}. NEVER exceed this.
2. Be polite but firm. Try to get the lowest price possible.
3. If the Seller's price is <= ${pmax}, you can accept if it feels like a fair deal.
4. You MUST include a price in every response.
5. Format: Always end with '### BUYER PRICE($price) ###'.
6. If you accept a price, add 'MAKE DEAL' after the price line.
7. Maximum rounds: 20.
"""

# --- HELPER FUNCTIONS ---
def parse_price(text):
    match = re.search(r"###\s*(?:BUYER|SELLER)\s*PRICE\s*\(\s*\$?(\d+)\s*\)\s*###", text, re.I)
    return int(match.group(1)) if match else None

def get_ai_response(user_input):
    # Construct history for Gemini
    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    full_prompt = f"{BUYER_SYSTEM_PROMPT}\n\nHistory:\n{history_str}\n\nSeller: {user_input}\nBuyer:"
    
    response = model.generate_content(full_prompt)
    return response.text.strip()

# --- MAIN UI ---
st.title("🤝 DealFixer: AI Buyer Negotiation")
st.info(f"Goal: Convince the AI Buyer to pay your price. Max Rounds: 20 | AI Budget: Hidden")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Negotiation Logic
if not st.session_state.deal_fixed and st.session_state.round_count < 20:
    if prompt := st.chat_input("Enter your offer (e.g., 'I can do $550 for this unit')"):
        # 1. User (Seller) Turn
        st.session_state.messages.append({"role": "seller", "content": prompt})
        with st.chat_message("seller"):
            st.markdown(prompt)
        
        seller_price = parse_price(prompt)
        
        # 2. AI (Buyer) Turn
        with st.spinner("AI Buyer is thinking..."):
            ai_text = get_ai_response(prompt)
            st.session_state.messages.append({"role": "buyer", "content": ai_text})
            
            with st.chat_message("buyer"):
                st.markdown(ai_text)
            
            # Check for deal
            buyer_price = parse_price(ai_text)
            st.session_state.last_buyer_price = buyer_price
            
            if "MAKE DEAL" in ai_text.upper():
                st.session_state.deal_fixed = True
            
            st.session_state.round_count += 1
            st.rerun()

# --- FINAL STATUS ---
if st.session_state.deal_fixed:
    st.markdown(f"""<div class="deal-box"><h1>🤝 DEAL CLOSED!</h1>
    <p>Final Price: ${st.session_state.last_buyer_price}</p></div>""", unsafe_allow_html=True)
    st.balloons()

elif st.session_state.round_count >= 20:
    st.markdown("""<div class="fail-box"><h1>❌ NO DEAL</h1>
    <p>Maximum negotiation rounds reached.</p></div>""", unsafe_allow_html=True)
