import streamlit as st
from google import genai
import os

# =================================================================
# SECTION 1: CONFIGURATION & SETUP
# =================================================================

# --- 1.1 CONSTANTS (YOUR CUSTOM RULES) ---
# Multiplier thresholds used for analysis
LOW_MULTIPLIER_THRESHOLD = 1.50
HIGH_MULTIPLIER_THRESHOLD = 8.00

# Streak requirements for the signal
REQUIRED_LOW_STREAK = 7
SAFE_HIGH_STREAK = 20

# --- 1.2 GEMINI CLIENT INITIALIZATION ---
@st.cache_resource
def get_gemini_client():
    """Initializes the Gemini client securely from the environment variable."""
    try:
        # The client automatically looks for the GEMINI_API_KEY environment variable.
        return genai.Client()
    except Exception as e:
        st.error(f"Error initializing Gemini Client. Please ensure GEMINI_API_KEY is set. Error: {e}")
        return None

client = get_gemini_client()


# =================================================================
# SECTION 2: CORE LOGIC FUNCTIONS
# =================================================================

def generate_risk_averse_signal(history):
    """
    Checks the two primary custom safety conditions (low streak and variance absence).
    Returns a tuple: (message_string, is_bet_signal_bool).
    """
    
    # --- Data Integrity Check ---
    if len(history) < SAFE_HIGH_STREAK:
        return f"🛑 ERROR: Need at least {SAFE_HIGH_STREAK} rounds of history for safe analysis.", False
    
    # --- CHECK 1: The Low Multiplier Streak (7x < 1.50x) ---
    low_streak_count = 0
    # Iterate backwards through the required streak length
    for multiplier in reversed(history[-REQUIRED_LOW_STREAK:]):
        if multiplier < LOW_MULTIPLIER_THRESHOLD:
            low_streak_count += 1
        else:
            break
    is_low_streak_ready = (low_streak_count >= REQUIRED_LOW_STREAK)

    # --- CHECK 2: Absence of Recent High Multiplier (No 8.00x+ in 20 rounds) ---
    high_hit_recently = any(m >= HIGH_MULTIPLIER_THRESHOLD for m in history[-SAFE_HIGH_STREAK:])
            
    # --- FINAL SIGNAL DECISION ---
    if is_low_streak_ready and not high_hit_recently:
        # Both safety conditions are met. Signal given.
        message = (
            f"🎯 **HIGH-TARGET SIGNAL!** **BET NOW!** 🎯\n\n"
            f"**Conditions Met (100% accurate rule execution):**\n"
            f"  1. Low Streak: {low_streak_count} consecutive rounds **< {LOW_MULTIPLIER_THRESHOLD}x**.\n"
            f"  2. Safety Check: **NO** multiplier **>= {HIGH_MULTIPLIER_THRESHOLD}x** recently.\n\n"
            f"**ACTION:** Target **3.00x** (Aggressive) or **2.00x** (Moderate)."
        )
        return message, True
    else:
        # One or both safety conditions failed. DO NOT BET.
        reason = []
        if not is_low_streak_ready: reason.append(f"🔴 **Low Streak NOT Ready** (only {low_streak_count} below {LOW_MULTIPLIER_THRESHOLD}x).")
        if high_hit_recently: reason.append(f"🔴 **High Variance Detected** (a {HIGH_MULTIPLIER_THRESHOLD}x+ hit occurred recently).")
            
        message = (
            f"❌ **NO SIGNAL.** **DO NOT BET.**\n\n"
            f"**Reason(s) to Wait:**\n* {' '.join(reason)}\n"
            f"**Action:** Wait for safety conditions to align."
        )
        return message, False


def get_ai_analysis(history_list, traditional_signal):
    """Sends the data and traditional result to Gemini for a human-like risk assessment."""
    if not client: return "⚠️ Gemini AI Analysis is unavailable."

    prompt = (
        f"Analyze the sequence: {history_list}. The calculated signal is: '{traditional_signal}'. Based on crash game risk principles, provide a quick 3-4 sentence risk assessment."
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Gemini API Error: Could not generate analysis. ({e})"


# =================================================================
# SECTION 3: STREAMLIT APP LAYOUT & EXECUTION
# =================================================================

st.set_page_config(page_title="Custom Signal AI", layout="centered")
st.title("🛡️ Custom Signal Checker + Gemini AI")
st.markdown("Paste the **last 20+ multiplier results** below (separated by commas or spaces).")

history_string = st.text_area(
    "Multiplier History",
    placeholder="e.g., 1.65, 3.10, 1.01, 1.45, 1.12, ... (minimum 20 values)",
    height=150
)

if st.button("CHECK BETTING SIGNAL"):
    if not history_string:
        st.warning("Please paste the multiplier history to analyze.")
    else:
        try:
            # Data preparation: convert string input to a list of floats
            history_list = [float(x.strip()) for x in history_string.replace(",", " ").split() if x.strip()]
            
            # 1. Run Traditional Signal
            signal_message, is_bet_signal = generate_risk_averse_signal(history_list)
            
            # Display Traditional Signal
            if is_bet_signal:
                st.success(signal_message)
            else:
                st.error(signal_message)
            
            # 2. Run AI Analysis
            if len(history_list) >= SAFE_HIGH_STREAK:
                with st.spinner('🤖 Gemini AI is generating risk assessment...'):
                    ai_analysis = get_ai_analysis(history_list, signal_message)
                    st.info(f"**Gemini AI Risk Assessment:**\n{ai_analysis}")
            else:
                st.info(f"Need at least {SAFE_HIGH_STREAK} rounds for full AI analysis.")

        except ValueError:
            st.error("❌ Error: Please ensure all pasted values are valid numbers.")

st.markdown("---")
st.caption("The core logic uses your specific parameters (7x < 1.50x, no 8.00x+ in 20).")