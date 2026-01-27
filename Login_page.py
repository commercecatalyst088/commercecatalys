import streamlit as st
import json
import os
from datetime import datetime

DATA_FILE = "data/users.json"

# ---------- Helpers ----------
def load_users():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def today():
    return datetime.today().date()

# ---------- Login ----------
def login():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users = load_users()

        if username not in users:
            st.error("User not found")
            return

        user = users[username]

        if not user["active"]:
            st.error("Account disabled")
            return

        if password != user["password"]:
            st.error("Wrong password")
            return

        expiry = datetime.strptime(user["expiry"], "%Y-%m-%d").date()
        if today() > expiry:
            st.error("Account expired")
            return

        st.session_state.user = username
        st.session_state.role = user["role"]
        st.success("Login successful")
        st.rerun()

# ---------- Admin Panel ----------
def admin_panel():
    st.title("🛠 Admin Panel")

    users = load_users()

    st.subheader("➕ Add New User")
    new_user = st.text_input("Username")
    new_pass = st.text_input("Password")
    expiry = st.date_input("Expiry Date")

    if st.button("Create User"):
        if new_user in users:
            st.error("User already exists")
        else:
            users[new_user] = {
                "password": new_pass,
                "role": "client",
                "expiry": expiry.strftime("%Y-%m-%d"),
                "active": true
            }
            save_users(users)
            st.success("User created")

    st.divider()
    st.subheader("👥 Existing Users")

    for u in users:
        st.write(u, users[u]["role"], users[u]["expiry"])

# ---------- Client Dashboard ----------
def client_dashboard():
    st.title("📊 Client Dashboard")
    st.write("Welcome,", st.session_state.user)
    st.write("यहाँ आपका main dashboard रहेगा")

# ---------- Main ----------
if "user" not in st.session_state:
    login()
else:
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    if st.session_state.role == "admin":
        admin_panel()
    else:
        client_dashboard()
