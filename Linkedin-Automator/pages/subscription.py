import streamlit as st

# Streamlit App Config
st.set_page_config(
    page_title="Subscription Plans | AI Cover Letter Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Page Title
st.title("📄 AI Cover Letter Generator")
st.subheader("Simple, Transparent Pricing for Every Job Seeker")

# --- CSS Styling ---
st.markdown("""
<style>
.card {
    border: 2px solid #e0e0e0;
    border-radius: 12px;
    padding: 25px 20px;
    background-color: #ffffff;
    box-shadow: 2px 4px 10px rgba(0,0,0,0.05);
    transition: 0.3s;
}
.card:hover {
    box-shadow: 2px 6px 15px rgba(0,0,0,0.15);
}
.plan-title {
    font-size: 24px;
    font-weight: 600;
    color: #333333;
}
.plan-price {
    font-size: 32px;
    font-weight: 700;
    margin: 10px 0;
}
ul {
    padding-left: 20px;
}
li {
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- Plan Rendering Function ---
def render_plan(title, price, letter_count, features, color):
    return f"""
    <div class='card' style='color: black;'>
        <div class='plan-title' style='color:{color}'>{title}</div>
        <div class='plan-price'>₹{price}/month</div>
        <p><strong>{letter_count} AI Cover Letters</strong></p>
        <ul>
            {''.join([f"<li>{f}</li>" for f in features])}
        </ul>
    </div>
    """


# --- Plans Layout ---
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(render_plan(
        title="🆓 Free Plan",
        price="0",
        letter_count="3",
        features=[
            "Access to GPT-3.5",
            "1 Resume PDF Parse per Letter",
            "Ideal for Testing and Exploration",
        ],
        color="#2ecc71"
    ), unsafe_allow_html=True)

with col2:
    st.markdown(render_plan(
        title="💡 Basic Plan",
        price="199",
        letter_count="15",
        features=[
            "Access to GPT-3.5",
            "1 Resume PDF Parse per Letter",
            "Priority Access",
            "Support via Email",
        ],
        color="#3498db"
    ), unsafe_allow_html=True)

with col3:
    st.markdown(render_plan(
        title="🚀 Pro Plan",
        price="499",
        letter_count="60",
        features=[
            "Access to GPT-3.5",
            "1 Resume PDF Parse per Letter",
            "High Priority Support",
            "Best for Active Job Seekers",
        ],
        color="#e74c3c"
    ), unsafe_allow_html=True)

# --- Bottom Section ---
st.markdown("---")
st.info("💡 All plans include Resume-to-Text Conversion (via ComPDFKit) and GPT-3.5 Cover Letter Generation. Prices include infrastructure & API costs.")

st.markdown("""
### 📦 Future Features (Coming Soon)
- 🔐 User Authentication (Supabase Session)
- 💳 Razorpay / Stripe Payment Integration
- 🧠 Personalized Letter History + Editing
- 🔁 Renewals & Upgrades
""")

# Session tracking (template for future)
if 'user_plan' not in st.session_state:
    st.session_state.user_plan = "Free"

st.sidebar.success(f"✅ Current Plan: {st.session_state.user_plan}")
