import streamlit as st
import json
import os
import hashlib
import platform
from datetime import datetime

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Secure Client Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# CUSTOM CSS (Meesho Style)
# =========================
st.markdown("""
<style>
    /* पूरे पेज का बैकग्राउंड हल्का ग्रे करें ताकि बॉक्स उभर कर आए */
    .stApp {
        background-color: #fce4ec; /* हल्का पिंक (Meesho style vibe) या #f0f2f5 रख सकते हैं */
    }
    
    /* लॉगिन फॉर्म को कार्ड जैसा बनाना */
    [data-testid="stForm"] {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 8px; /* कोनों को थोड़ा गोल करना */
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1); /* परछाई (Shadow) */
        border: 1px solid #e0e0e0;
    }

    /* इनपुट बॉक्स को थोड़ा सुंदर बनाना */
    .stTextInput > div > div > input {
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 10px;
    }

    /* बटन को पूरा चौड़ा (Full Width) और पिंक करना */
    .stButton > button {
        width: 100%;
        background-color: #ff4081; /* Meesho Pink Color */
        color: white;
        border: none;
        padding: 12px;
        border-radius: 5px;
        font-size: 16px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #e91e63; /* Hover करने पर गहरा पिंक */
        color: white;
        border: none;
    }
    
    /* हेडिंग को सेंटर करना */
    h2 {
        text-align: center;
        font-family: 'Arial', sans-serif;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "device_id" not in st.session_state:
    st.session_state.device_id = None

# =========================
# FILE HANDLERS
# =========================
USER_FILE = "users.json"

# (Safety check: Create file if not exists)
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        # Default Admin for testing
        json.dump({"admin@test.com": {"password": "123", "expiry": "2030-01-01", "device": ""}}, f)

def load_users():
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=2)

def device_fingerprint():
    base = platform.system() + platform.machine() + platform.processor()
    return hashlib.sha256(base.encode()).hexdigest()

def is_expired(date_str):
    today = datetime.today().date()
    expiry = datetime.strptime(date_str, "%Y-%m-%d").date()
    return today > expiry

# =========================
# LOGIN PAGE (DESIGNED)
# =========================
def login_page():
    # ऊपर थोड़ी जगह छोड़ें
    st.write("") 
    st.write("")
    st.write("")

    # 3 कॉलम बनाए: [खाली जगह] [लॉगिन बॉक्स] [खाली जगह]
    # बीच वाला कॉलम '2' रखा है ताकि बॉक्स की चौड़ाई सही रहे
    col1, col2, col3 = st.columns([1.5, 2, 1.5])

    with col2:
        # st.form ऑटो-फिल की समस्या को ठीक करता है
        with st.form("login_form", clear_on_submit=False):
            st.markdown("<h2>Login Panel</h2>", unsafe_allow_html=True)
            
            # ईमेल और पासवर्ड इनपुट
            email = st.text_input("Email ID or Mobile Number")
            password = st.text_input("Password", type="password")
            
            # लॉगिन बटन (फॉर्म के अंदर)
            submitted = st.form_submit_button("Log In")
            
            if submitted:
                # फॉर्म सबमिट होने पर ही यह कोड चलेगा
                users = load_users()

                if email not in users:
                    st.error("Invalid User ID")
                    return

                if users[email]["password"] != password:
                    st.error("Incorrect Password")
                    return

                if is_expired(users[email]["expiry"]):
                    st.error("❌ Subscription Expired")
                    return

                current_device = device_fingerprint()

                # डिवाइस लॉक लॉजिक
                if users[email]["device"] == "":
                    users[email]["device"] = current_device
                    save_users(users)
                elif users[email]["device"] != current_device:
                    st.error("❌ Account registered on another device")
                    return

                # लॉगिन सफल
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.device_id = current_device
                st.success("Login Successful!")
                st.rerun()

# =========================
# GLOBAL LOCK
# =========================
if not st.session_state.logged_in:
    login_page()
    st.stop()

# =========================
# MAIN APP AFTER LOGIN
# =========================
# साइडबार
st.sidebar.success(f"User: {st.session_state.user_email}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.device_id = None
    st.rerun()

# एडमिन पैनल
if st.session_state.user_email == "admin@test.com":
    st.sidebar.subheader("👑 Admin Panel")
    users = load_users()
    
    with st.sidebar.expander("➕ Add User"):
        new_email = st.text_input("New Email")
        new_pass = st.text_input("New Password")
        new_exp = st.date_input("Expiry")
        if st.button("Create"):
            users[new_email] = {"password": new_pass, "expiry": str(new_exp), "device": ""}
            save_users(users)
            st.success("Done")
            
    with st.sidebar.expander("⚙ Manage"):
        u_sel = st.selectbox("Select User", list(users.keys()))
        if st.button("Reset Device"):
            users[u_sel]["device"] = ""
            save_users(users)
            st.success("Device Reset")
        if st.button("Delete User"):
            if u_sel != "admin@test.com":
                users.pop(u_sel)
                save_users(users)
                st.rerun()

# डैशबोर्ड
st.title("📊 Secure Dashboard")
st.success("Login Successful. Welcome to the secure area.")
