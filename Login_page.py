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
# SESSION STATE
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "device_id" not in st.session_state:
    st.session_state.device_id = None

# =========================
# FILE
# =========================
USER_FILE = "users.json"

# =========================
# HELPERS
# =========================
def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

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
    st.title("🔐 Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()

        if email not in users:
            st.error("Invalid user")
            return

        if users[email]["password"] != password:
            st.error("Wrong password")
            return

        if is_expired(users[email]["expiry"]):
            st.error("❌ Subscription expired")
            return

        current_device = device_fingerprint()

        if users[email]["device"] == "":
            users[email]["device"] = current_device
            save_users(users)

        elif users[email]["device"] != current_device:
            st.error("❌ Account already registered on another device")
            return

        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.session_state.device_id = current_device
        st.success("Login successful")
        st.rerun()

# =========================
# GLOBAL LOCK
# =========================
if not st.session_state.logged_in:
    login_page()
    st.stop()

# =========================
# SIDEBAR
# =========================
st.sidebar.success("Logged in")
st.sidebar.write(st.session_state.user_email)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.device_id = None
    st.rerun()

# =========================
# ADMIN PANEL
# =========================
if st.session_state.user_email == "admin@test.com":
    st.sidebar.subheader("👑 Admin Panel")

    users = load_users()

    st.sidebar.markdown("### ➕ Add New User")
    new_email = st.sidebar.text_input("User Email")
    new_password = st.sidebar.text_input("Password")
    new_expiry = st.sidebar.date_input("Expiry Date")

    if st.sidebar.button("Add User"):
        users[new_email] = {
            "password": new_password,
            "expiry": str(new_expiry),
            "device": ""
        }
        save_users(users)
        st.sidebar.success("User added")

    st.sidebar.markdown("### 🔄 Reset Device")
    selected = st.sidebar.selectbox("Select User", users.keys())

    if st.sidebar.button("Reset Selected Device"):
        users[selected]["device"] = ""
        save_users(users)
        st.sidebar.success("Device reset done")

    st.sidebar.markdown("### ❌ Remove User")
    if st.sidebar.button("Delete User"):
        if selected != "admin@test.com":
            users.pop(selected)
            save_users(users)
            st.sidebar.success("User deleted")

# =========================
# MAIN DASHBOARD
# =========================
st.title("📊 Secure Dashboard")
st.success("✔ Login, Device Lock & Expiry Active")
