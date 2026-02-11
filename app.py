import streamlit as st
import google.generativeai as genai
import re

# --- CONFIGURATION ---
st.set_page_config(page_title="DealFixer AI", page_icon="🤝", layout="wide")

# Securely set up Gemini
API_KEY = "AIzaSyCOrBVIVA2J2MC7ZVhqGzWOGCMMlj2p958"
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

# --- PRODUCTS DATA ---
products = {
    "iPhone 13 Pro": {
        "desc": "128GB, Graphite, 90% Battery Health, minor screen scratch.",
        "image_url": "https://i5.walmartimages.com/seo/Apple-iPhone-13-Pro-A2483-128GB-Graphite-US-Model-Factory-Unlocked-Cell-Phone-Excellent-Condition_8e0eb526-dd51-4a57-85a7-54795b2825b9.0167a44259317a663d7722b6c18a1614.jpeg",
        "market_context": "High demand, but new model just released.",
        "default_seller_min": 500,
        "default_buyer_max": 600
    },
    "Samsung Galaxy S23": {
        "desc": "256GB, Phantom Black, excellent condition.",
        "image_url": "https://i.ytimg.com/vi/ehRc2ms-mxM/maxresdefault.jpg",
        "market_context": "Competitive market with many alternatives.",
        "default_seller_min": 700,
        "default_buyer_max": 800
    },
    "Dell XPS 13 Laptop": {
        "desc": "Intel i7, 16GB RAM, 512GB SSD, like new.",
        "image_url": "http://media.wired.com/photos/60f72daa3b922f01a2083b7e/master/pass/Gear-Dell-XPS-13-2021.jpg",
        "market_context": "Premium laptop segment, steady demand.",
        "default_seller_min": 900,
        "default_buyer_max": 1100
    },
    "Sony WH-1000XM5 Headphones": {
        "desc": "Noise-cancelling, black, barely used.",
        "image_url": "https://i.ytimg.com/vi/v6EjmbMgv80/maxresdefault.jpg",
        "market_context": "High-end audio, popular for travel.",
        "default_seller_min": 250,
        "default_buyer_max": 350
    }
}

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "round_count" not in st.session_state:
    st.session_state.round_count = 0
if "deal_fixed" not in st.session_state:
    st.session_state.deal_fixed = False
if "last_price" not in st.session_state:
    st.session_state.last_price = None

# --- UI SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Negotiation Settings")
    product_name = st.selectbox("Product", list(products.keys()))
    product = products[product_name]
    product_desc = st.text_area("Product Description", value=product["desc"])
    market_context = st.text_input("Market Context", value=product["market_context"])
    seller_min = st.number_input("AI Seller Reserve Price ($)", value=product["default_seller_min"])
    buyer_max = st.number_input("AI Buyer Max Budget ($)", value=product["default_buyer_max"])
    
    if st.button("Reset Negotiation"):
        st.session_state.messages = []
        st.session_state.round_count = 0
        st.session_state.deal_fixed = False
        st.session_state.last_price = None
        st.rerun()

# --- SYSTEM PROMPTS ---
BUYER_SYSTEM_PROMPT = f"""
You are an AI Buyer negotiating on behalf of a customer for: {product_name}.
Description: {product_desc}
Market: {market_context}

RULES:
1. Your maximum budget is ${buyer_max}. NEVER exceed this.
2. Be polite but firm. Try to get the lowest price possible.
3. If the Seller's price is <= ${buyer_max}, you can accept if it feels like a fair deal.
4. You MUST include a price in every response.
5. Format: Always end with '### BUYER PRICE($price) ###'.
6. If you accept a price, add 'MAKE DEAL' after the price line.
7. Maximum rounds: 20.
"""

SELLER_SYSTEM_PROMPT = f"""
You are an AI Seller negotiating for: {product_name}.
Description: {product_desc}
Market: {market_context}

RULES:
1. Your minimum reserve price is ${seller_min}. NEVER go below this.
2. Be polite but firm. Try to get the highest price possible.
3. If the Buyer's price is >= ${seller_min}, you can accept if it feels like a fair deal.
4. You MUST include a price in every response.
5. Format: Always end with '### SELLER PRICE($price) ###'.
6. If you accept a price, add 'MAKE DEAL' after the price line.
7. Maximum rounds: 20.
"""

# --- HELPER FUNCTIONS ---
def parse_price(text):
    match = re.search(r"###\s*(?:BUYER|SELLER)\s*PRICE\s*\(\s*\$?(\d+)\s*\)\s*###", text, re.I)
    return int(match.group(1)) if match else None

def get_ai_buyer_response(seller_input):
    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    full_prompt = f"{BUYER_SYSTEM_PROMPT}\n\nHistory:\n{history_str}\n\nSeller: {seller_input}\nBuyer:"
    response = model.generate_content(full_prompt)
    return response.text.strip()

def get_ai_seller_response(buyer_input):
    history_str = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    full_prompt = f"{SELLER_SYSTEM_PROMPT}\n\nHistory:\n{history_str}\n\nBuyer: {buyer_input}\nSeller:"
    response = model.generate_content(full_prompt)
    return response.text.strip()

# --- MAIN UI ---
st.title("🤝 DealFixer: AI vs AI Negotiation")
st.info(f"Watch the AI Seller and AI Buyer negotiate for the {product_name}. Max Rounds: 20 | Seller Reserve: Hidden | Buyer Budget: Hidden")

# Display Product Image
st.image(product["image_url"], caption=product_name, use_column_width=True)

# Display Chat History (if any)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Start Negotiation Button
if st.button("Start AI vs AI Negotiation"):
    st.session_state.messages = []
    st.session_state.round_count = 0
    st.session_state.deal_fixed = False
    st.session_state.last_price = None
    
    with st.spinner("Simulating negotiation..."):
        # Initial Seller Offer
        initial_prompt = f"{SELLER_SYSTEM_PROMPT}\n\nThe buyer has shown interest. Start the negotiation with your initial asking price.\nSeller:"
        ai_text = model.generate_content(initial_prompt).text.strip()
        st.session_state.messages.append({"role": "seller", "content": ai_text})
        with st.chat_message("seller"):
            st.markdown(ai_text)
        seller_price = parse_price(ai_text)
        st.session_state.last_price = seller_price
        
        deal_fixed = False
        round_count = 0
        
        while not deal_fixed and round_count < 20:
            # AI Buyer Turn
            ai_text = get_ai_buyer_response(st.session_state.messages[-1]["content"])
            st.session_state.messages.append({"role": "buyer", "content": ai_text})
            with st.chat_message("buyer"):
                st.markdown(ai_text)
            buyer_price = parse_price(ai_text)
            st.session_state.last_price = buyer_price
            if "MAKE DEAL" in ai_text.upper():
                deal_fixed = True
                break
            
            # AI Seller Turn
            ai_text = get_ai_seller_response(st.session_state.messages[-1]["content"])
            st.session_state.messages.append({"role": "seller", "content": ai_text})
            with st.chat_message("seller"):
                st.markdown(ai_text)
            seller_price = parse_price(ai_text)
            st.session_state.last_price = seller_price
            if "MAKE DEAL" in ai_text.upper():
                deal_fixed = True
            
            round_count += 1
        
        st.session_state.deal_fixed = deal_fixed
        st.session_state.round_count = round_count
    st.rerun()

# --- FINAL STATUS ---
if st.session_state.deal_fixed:
    st.markdown(f"""<div class="deal-box"><h1>🤝 DEAL CLOSED!</h1>
    <p>Final Price: ${st.session_state.last_price}</p></div>""", unsafe_allow_html=True)
    st.balloons()

elif st.session_state.round_count >= 5:
    st.markdown("""<div class="fail-box"><h1>❌ NO DEAL</h1>
    <p>Maximum negotiation rounds reached.</p></div>""", unsafe_allow_html=True)
