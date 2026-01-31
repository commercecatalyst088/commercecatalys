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
    /* पूरे पेज का बैकग्राउंड हल्का ग्रे करें */
    .stApp {
        background-color: #fce4ec; 
    }
    
    /* लॉगिन फॉर्म को कार्ड जैसा बनाना */
    [data-testid="stForm"] {
        background-color: #ffffff;
        padding: 40px;
        border-radius: 8px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.1);
        border: 1px solid #e0e0e0;
    }

    /* इनपुट बॉक्स स्टाइल */
    .stTextInput > div > div > input {
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 10px;
    }

    /* बटन स्टाइल */
    .stButton > button {
        width: 100%;
        background-color: #ff4081; 
        color: white;
        border: none;
        padding: 12px;
        border-radius: 5px;
        font-size: 16px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #e91e63;
        color: white;
        border: none;
    }
    
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

if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
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
# LOGIN PAGE
# =========================
def login_page():
    st.write("") 
    st.write("")
    st.write("")

    col1, col2, col3 = st.columns([1.5, 2, 1.5])

    with col2:
        with st.form("login_form", clear_on_submit=False):
            st.markdown("<h2>Login Panel</h2>", unsafe_allow_html=True)
            
            email = st.text_input("Email ID or Mobile Number")
            password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Log In")
            
            if submitted:
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

                if users[email]["device"] == "":
                    users[email]["device"] = current_device
                    save_users(users)
                elif users[email]["device"] != current_device:
                    st.error("❌ Account registered on another device")
                    return

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
st.sidebar.success(f"User: {st.session_state.user_email}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.device_id = None
    st.rerun()

# Admin Panel
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

# --- MAIN DASHBOARD CONTENT ---
st.title("📊 Secure Dashboard")
st.success("Login Successful. Welcome to the secure area.")

# ----------------------------------------------------
# 📺 TUTORIAL SECTION (YouTube Links)
# ----------------------------------------------------
st.markdown("---")
st.header("📺 How to Use (Tutorials)")

with st.expander("🎥 Watch Video Tutorials", expanded=True):
    st.info("Tutorial videos will appear here. (Admin can add links below)")
    
    # FUTURE: Jab aapke paas video aa jaye, to niche wali line ka # hata kar link daal de:
    # st.video("https://www.youtube.com/watch?v=YOUR_VIDEO_LINK_HERE")
    
    # Example placeholder (filhal ke liye)
    st.write("1. Dashboard Overview (Coming Soon)")
    st.write("2. How to Upload Files (Coming Soon)")

# ----------------------------------------------------
# 📞 CONTACT & SUPPORT SECTION
# ----------------------------------------------------
st.markdown("---")
st.header("📞 Contact & Support")

col_contact1, col_contact2 = st.columns(2)

with col_contact1:
    st.subheader("💬 Chat on WhatsApp")
    st.write("Need quick help? Chat with Admin directly.")
    
    # ⚠️ EDIT HERE: Replace 91XXXXXXXXXX with your actual number
    whatsapp_number = "918010952817" 
    whatsapp_url = f"https://wa.me/{whatsapp_number}"
    
    st.markdown(f'''
        <a href="{whatsapp_url}" target="_blank">
            <button style="background-color:#25D366;color:white;border:none;padding:10px 20px;border-radius:5px;font-size:16px;font-weight:bold;cursor:pointer;width:100%;">
                🟢 Chat on WhatsApp
            </button>
        </a>
    ''', unsafe_allow_html=True)

with col_contact2:
    st.subheader("📧 Send Direct Email")
    st.write("Send a message directly to Admin.")
    
    # FormSubmit Form -> commercecatalyst088@gmail.com
    contact_form = """
    <form action="https://formsubmit.co/commercecatalyst088@gmail.com" method="POST">
        <input type="hidden" name="_captcha" value="false">
        <input type="text" name="name" placeholder="Your Name" required style="width:100%;padding:10px;margin-bottom:10px;border:1px solid #ccc;border-radius:4px;">
        <input type="email" name="email" placeholder="Your Email" required style="width:100%;padding:10px;margin-bottom:10px;border:1px solid #ccc;border-radius:4px;">
        <textarea name="message" placeholder="Your Message / Suggestion" required style="width:100%;padding:10px;margin-bottom:10px;border:1px solid #ccc;border-radius:4px;min-height:100px;"></textarea>
        <button type="submit" style="background-color:#0d47a1;color:white;border:none;padding:10px 20px;border-radius:5px;font-size:16px;cursor:pointer;width:100%;">📩 Send Message</button>
    </form>
    """
    st.markdown(contact_form, unsafe_allow_html=True)
