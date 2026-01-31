import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
from io import BytesIO

st.set_page_config(page_title="Supplier Discount Analysis", layout="wide")

st.title("Supplier Discount Analysis Dashboard (With SKU Groups)")

st.markdown(
    """
    Yeh dashboard **Supplier Listed Price (Incl. GST + Commission)** aur **Supplier Discounted Price (Incl GST and Commision)** ke beech ka 
    discount amount (₹) aur discount percentage (%) calculate karke dikhata hai.
    """
)

# Column names
COL_REASON = "Reason for Credit Entry"
COL_SUBORDER = "Sub Order No"
COL_ORDER_DATE = "Order Date"
COL_PRODUCT = "Product Name"
COL_SKU = "SKU"
COL_LIST_PRICE = "Supplier Listed Price (Incl. GST + Commission)"
COL_DISC_PRICE = "Supplier Discounted Price (Incl GST and Commision)"

required_cols = [
    COL_REASON,
    COL_SUBORDER,
    COL_ORDER_DATE,
    COL_PRODUCT,
    COL_SKU,
    COL_LIST_PRICE,
    COL_DISC_PRICE,
]

# 1) CSV Upload & Merge
with st.expander("📂 CSV Upload & Merge (Multiple Files)", expanded=True):
    uploaded_files = st.file_uploader(
        "Ek ya multiple Orders CSV files upload karein",
        type=["csv"],
        accept_multiple_files=True,
    )

    merged_df = None
    if uploaded_files:
        dfs = []
        base_cols = None

        for file in uploaded_files:
            try:
                temp_df = pd.read_csv(file)
            except pd.errors.EmptyDataError:
                st.warning(f"{file.name} khali hai (no data), isko skip kiya gaya.")
                continue
            except Exception as e:
                st.error(f"{file.name} read karne mein error: {e}")
                continue

            if temp_df.empty:
                st.warning(f"{file.name} me koi rows nahin mili, isko skip kiya gaya.")
                continue

            if base_cols is None:
                base_cols = temp_df.columns
                dfs.append(temp_df)
            else:
                common_cols = [c for c in base_cols if c in temp_df.columns]
                temp_df = temp_df[common_cols]
                temp_df = temp_df.reindex(columns=base_cols)
                dfs.append(temp_df)

        if dfs:
            merged_df = pd.concat(dfs, ignore_index=True)
            st.success(
                f"Total {len(uploaded_files)} file(s) merge ho gayi hain. "
                f"Total rows: {len(merged_df)}"
            )
        else:
            st.error("Koi valid CSV data merge nahin ho paya.")
    else:
        st.info("Yahan se apni CSV files select karke merge kar sakte hain.")

if merged_df is None:
    st.stop()

# 2) Cleaning + Discount
df = merged_df.copy()

missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"In columns ki zarurat hai, lekin file(s) me nahin mile: {missing}")
    st.stop()

df[COL_ORDER_DATE] = pd.to_datetime(df[COL_ORDER_DATE], errors="coerce")
df[COL_LIST_PRICE] = pd.to_numeric(df[COL_LIST_PRICE], errors="coerce")
df[COL_DISC_PRICE] = pd.to_numeric(df[COL_DISC_PRICE], errors="coerce")

df["Discount Amount (₹)"] = df[COL_LIST_PRICE] - df[COL_DISC_PRICE]
df["Discount %"] = (df["Discount Amount (₹)"] / df[COL_LIST_PRICE].replace(0, pd.NA)) * 100

# 3) Global Filters
st.sidebar.header("Global Filters")

min_date = df[COL_ORDER_DATE].min()
max_date = df[COL_ORDER_DATE].max()

if pd.isna(min_date) or pd.isna(max_date):
    start_date = end_date = datetime.today().date()
else:
    start_date, end_date = st.sidebar.date_input(
        "Order Date Range (Global)",
        value=(min_date.date(), max_date.date()),
    )

if isinstance(start_date, datetime):
    start_date = start_date.date()
if isinstance(end_date, datetime):
    end_date = end_date.date()

# ================= SKU Grouping System (INTEGRATED) =================
# Prepare SKU List
df[COL_SKU] = df[COL_SKU].astype(str)
all_skus = sorted(df[COL_SKU].dropna().unique().tolist())

# --- Session State Init ---
if 'sku_groups' not in st.session_state:
    st.session_state['sku_groups'] = []

st.sidebar.markdown("---")
st.sidebar.markdown("### 📦 SKU Group Manager")

# --- Group Creator Interface (Search -> Select All -> Save) ---
with st.sidebar.expander("➕ Create New Group", expanded=False):
    st.caption("Step 1: Search Keyword")
    search_keyword = st.text_input("Enter Keyword (e.g. Kurti)", key="grp_search_box")
    
    # Find Matches
    found_matches = []
    if search_keyword:
        found_matches = [s for s in all_skus if search_keyword.lower() in s.lower()]
    
    st.caption(f"Step 2: Review Selection ({len(found_matches)} found)")
    
    # --- SELECT ALL BUTTONS LOGIC ---
    col_sel1, col_sel2 = st.columns(2)
    
    def select_all_matches():
        st.session_state.preview_multiselect = found_matches
    
    def deselect_all_matches():
        st.session_state.preview_multiselect = []
    
    if "preview_multiselect" not in st.session_state:
        st.session_state.preview_multiselect = []

    with col_sel1:
        st.button("✅ Select All", on_click=select_all_matches, use_container_width=True)
    with col_sel2:
        st.button("❌ Deselect All", on_click=deselect_all_matches, use_container_width=True)

    selected_for_group = st.multiselect(
        "Verify SKUs to add:",
        options=found_matches,
        key="preview_multiselect"
    )
    
    st.caption("Step 3: Name & Save")
    group_name_input = st.text_input("Group Name", key="grp_name_box")
    
    def save_filtered_group():
        if group_name_input and selected_for_group:
            found = False
            for g in st.session_state["sku_groups"]:
                if g["name"] == group_name_input:
                    g["skus"] = selected_for_group
                    found = True
                    break
            if not found:
                st.session_state["sku_groups"].append({"name": group_name_input, "skus": selected_for_group})
            st.toast(f"✅ Group '{group_name_input}' Saved with {len(selected_for_group)} SKUs!")
        else:
            st.toast("⚠️ Name and valid selection required.")
    
    st.button("💾 Save Verified Group", on_click=save_filtered_group)
    
    st.markdown("---")
    if st.button("🧹 Clear All Groups"):
        st.session_state["sku_groups"] = []
        st.rerun()

# --- Group Selection Logic ---
st.sidebar.markdown("#### Select & View Groups")

group_options = [f"{g['name']} ({len(g['skus'])})" for g in st.session_state['sku_groups']]
selected_group_labels = st.sidebar.multiselect("1. Select Saved Groups", group_options)

skus_from_groups = []
for label in selected_group_labels:
    actual_name = label.rsplit(" (", 1)[0]
    for g in st.session_state['sku_groups']:
        if g['name'] == actual_name:
            skus_from_groups.extend(g['skus'])
            break
skus_from_groups = list(set(skus_from_groups))

# View Group Contents
if skus_from_groups:
    with st.sidebar.expander(f"👁️ View SKUs in Selection ({len(skus_from_groups)})"):
        st.dataframe(pd.DataFrame(skus_from_groups, columns=["Included SKUs"]), hide_index=True)

# --- Manual Extras ---
available_extra_options = sorted(list(set(all_skus) - set(skus_from_groups)))
manual_skus = st.sidebar.multiselect(
    "2. Add Extra SKUs (Unique only)", 
    options=available_extra_options,
    help="Allows adding single SKUs that are not in the selected groups."
)

# Final Combine
final_sku_list = list(set(skus_from_groups) | set(manual_skus))

# --- Apply Filters ---
mask_date_global = (df[COL_ORDER_DATE].dt.date >= start_date) & (
    df[COL_ORDER_DATE].dt.date <= end_date
)

# Apply SKU Filter if selected
if final_sku_list:
    mask_sku_global = df[COL_SKU].isin(final_sku_list)
    st.sidebar.success(f"✨ Filtering by {len(final_sku_list)} SKUs")
else:
    mask_sku_global = True
    st.sidebar.text("Showing All Data")

# NOTE: Yahan pehle hum sirf discount > 0 filter kar rahe the.
# Ab hum saara filtered data rakhenge aur neeche split karenge.
gdf = df[mask_date_global & mask_sku_global].copy()

# 4) Detailed Filters (multi-select)
st.subheader("Filters (Applied to both Tables)")

col_f1, col_f2 = st.columns(2)

with col_f1:
    reasons_list = sorted(gdf[COL_REASON].dropna().unique().tolist())
    selected_reasons = st.multiselect(
        "Reason for Credit Entry (multi-select)",
        options=["All"] + reasons_list,
        default=["All"],
    )

with col_f2:
    available_dates = sorted(gdf[COL_ORDER_DATE].dropna().dt.date.unique().tolist())
    date_labels = [d.strftime("%Y-%m-%d") for d in available_dates]
    selected_dates = st.multiselect(
        "Order Date (Specific, multi-select)",
        options=["All"] + date_labels,
        default=["All"],
    )

# Apply filters to the main dataset first
fdf_all = gdf.copy()

if "All" not in selected_reasons:
    fdf_all = fdf_all[fdf_all[COL_REASON].isin(selected_reasons)]

if "All" not in selected_dates:
    sel_dates_obj = [datetime.strptime(d, "%Y-%m-%d").date() for d in selected_dates]
    fdf_all = fdf_all[fdf_all[COL_ORDER_DATE].dt.date.isin(sel_dates_obj)]

# SPLIT DATA: Discounted vs Non-Discounted
fdf = fdf_all[fdf_all["Discount Amount (₹)"] > 0].copy()       # Discounted Table ke liye
ndf = fdf_all[fdf_all["Discount Amount (₹)"] <= 0].copy()      # Non-Discounted Table ke liye

# 5) Summary (bigger cards, based on fdf - Only Discounted Data)
st.markdown("## 1. Discounted Data Summary")
st.markdown("Ye data sirf un orders ka hai jahan **Discount > 0** hai.")

total_discount_amount = fdf["Discount Amount (₹)"].sum(skipna=True)
avg_discount_percent = fdf["Discount %"].mean(skipna=True)
total_rows_with_discount = len(fdf)
total_orders = len(fdf[COL_SUBORDER].dropna().unique())
total_revenue_after_discount = fdf[COL_DISC_PRICE].sum(skipna=True)

c1, c2, c3, c4, c5 = st.columns(5)

card_style = "background-color:{bg};padding:16px;border-radius:10px;text-align:center;"

with c1:
    st.markdown(
        f"""
        <div style="{card_style.format(bg='#e3f2fd')}">
        <div style="font-size:14px;color:#555;">Total Orders (Filtered)</div>
        <div style="font-size:26px;font-weight:bold;color:#0d47a1;">{total_orders}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div style="{card_style.format(bg='#fce4ec')}">
        <div style="font-size:14px;color:#555;">Total Discount Amount</div>
        <div style="font-size:26px;font-weight:bold;color:#880e4f;">{total_discount_amount:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div style="{card_style.format(bg='#e8f5e9')}">
        <div style="font-size:14px;color:#555;">Average Discount (%)</div>
        <div style="font-size:26px;font-weight:bold;color:#1b5e20;">{avg_discount_percent:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""
        <div style="{card_style.format(bg='#fff3e0')}">
        <div style="font-size:14px;color:#555;">Rows With Discount</div>
        <div style="font-size:26px;font-weight:bold;color:#e65100;">{int(total_rows_with_discount)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c5:
    st.markdown(
        f"""
        <div style="{card_style.format(bg='#ede7f6')}">
        <div style="font-size:14px;color:#555;">Revenue After Discount</div>
        <div style="font-size:26px;font-weight:bold;color:#311b92;">{total_revenue_after_discount:,.2f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# 6) Detailed Table (Discounted)
st.subheader("✅ Detailed Table: Discounted Orders (Discount > 0)")

fdf["Discount Amount (₹)"] = fdf["Discount Amount (₹)"].round(2)
fdf["Discount %"] = fdf["Discount %"].round(2)

display_cols_full = [
    COL_REASON,
    COL_SUBORDER,
    COL_ORDER_DATE,
    COL_SKU,
    COL_PRODUCT,
    COL_LIST_PRICE,
    COL_DISC_PRICE,
    "Discount Amount (₹)",
    "Discount %",
]

st.dataframe(fdf[display_cols_full], use_container_width=True)

# 7) PDF – sirf Discounted Rows ke liye
st.markdown("### Download PDF (Only Discounted Rows)")

pdf_cols = [COL_SUBORDER, COL_SKU, "Discount %"]
pdf_df = fdf[pdf_cols].copy()

def df_to_pdf(dataframe: pd.DataFrame) -> bytes:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "Discount Report (Sub Order No, SKU, Discount %)", ln=1, align="C")

    pdf.set_font("Arial", size=10)

    max_width = 280
    num_cols = len(dataframe.columns)
    col_width = max_width / num_cols

    # Header
    for col in dataframe.columns:
        header_txt = str(col).replace("₹", "INR")
        pdf.cell(col_width, 10, header_txt[:30], border=1, align="C")
    pdf.ln(10)

    # Rows
    for _, row in dataframe.iterrows():
        for col in dataframe.columns:
            txt = str(row[col]).replace("₹", "INR")
            if len(txt) > 30:
                txt = txt[:27] + "..."
            pdf.cell(col_width, 8, txt, border=1)
        pdf.ln(8)

    pdf_bytes = pdf.output(dest="S")
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode("latin-1", "ignore")
    return pdf_bytes

if not pdf_df.empty:
    pdf_bytes = df_to_pdf(pdf_df)
    buffer = BytesIO(pdf_bytes)

    st.download_button(
        label="Download PDF (Sub Order No, SKU, Discount %)",
        data=buffer,
        file_name=f"discount_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
    )
else:
    st.info("Current filters ke hisaab se koi discounted rows nahin mili.")


# ---------------------------------------------------------
# 8) NEW SECTION: Non-Discounted Table
# ---------------------------------------------------------
st.markdown("---")
st.subheader("❌ Detailed Table: Non-Discounted Orders (Zero Discount)")
st.markdown("Ye wo orders hain jahan Listed Price aur Discounted Price same thi (Discount = 0).")

if not ndf.empty:
    ndf["Discount Amount (₹)"] = ndf["Discount Amount (₹)"].round(2)
    ndf["Discount %"] = 0.0  # Since it's no discount

    # Summary metric for Non-Discounted
    count_nd = len(ndf)
    revenue_nd = ndf[COL_DISC_PRICE].sum(skipna=True)
    
    col_nd1, col_nd2 = st.columns(2)
    with col_nd1:
        st.info(f"Total Non-Discounted Rows: **{count_nd}**")
    with col_nd2:
        st.info(f"Revenue from Non-Discounted: **₹ {revenue_nd:,.2f}**")

    # Showing the table
    st.dataframe(ndf[display_cols_full], use_container_width=True)
else:
    st.success("Badhai ho! Selected filters mein koi bhi 'Zero Discount' order nahi hai. (Sab par discount mila hai).")
