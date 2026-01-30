import streamlit as st
import pandas as pd
from io import BytesIO

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please Login")
    st.stop()

st.set_page_config(
    page_title="Direct Paste Image Listing Tool",
    layout="wide"
)

st.title("🧵 Direct Paste Image Listing Tool (Streamlit)")
st.write("Image links paste करें → Style बनाएं → Excel download करें")

# ================= INPUT SECTION =================

st.markdown("### 📋 Image Links Paste करें (एक लाइन में एक link)")

links_text = st.text_area(
    "Paste image links here",
    height=260,
    placeholder=(
        "https://image1.jpg\n"
        "https://image2.jpg\n"
        "https://image3.jpg\n"
        "https://image4.jpg\n"
        "https://image5.jpg"
    )
)

images_per_style = st.number_input(
    "एक Style में कितनी Images होंगी?",
    min_value=1,
    max_value=30,
    value=5
)

repeat_rows = st.number_input(
    "एक Style को कितनी Rows में Repeat करना है? (Ctrl + D जैसा)",
    min_value=1,
    max_value=30,
    value=4
)

# ================= PROCESS =================

if links_text.strip():
    links = [l.strip() for l in links_text.splitlines() if l.strip()]

    total_styles = len(links) // images_per_style

    if total_styles == 0:
        st.warning("❗ Image links की संख्या style size से कम है.")
    else:
        st.markdown("## ✏️ हर Style के लिए Product ID / Style ID लिखें")

        style_ids = []
        for i in range(total_styles):
            sid = st.text_input(
                f"Style {i+1} – Product ID / Style ID",
                key=f"style_{i}"
            )
            style_ids.append(sid)

        if st.button("✅ Generate Final Excel"):
            final_rows = []

            for i in range(total_styles):
                style_images = links[
                    i * images_per_style:(i + 1) * images_per_style
                ]

                for _ in range(repeat_rows):
                    row = []
                    row.extend(style_images)
                    row.append(style_ids[i])
                    final_rows.append(row)

            # Column headers
            columns = [f"Image_{i+1}" for i in range(images_per_style)]
            columns.append("Product ID / Style ID")

            output_df = pd.DataFrame(final_rows, columns=columns)

            st.success("✅ Excel Successfully Generated!")

            st.markdown("## 📋 Full Preview (Copy–Paste Ready)")
            st.dataframe(output_df, use_container_width=True)

            # Download Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                output_df.to_excel(
                    writer,
                    index=False,
                    sheet_name="Final_Output"
                )

            st.download_button(
                label="⬇️ Download Final Excel",
                data=output.getvalue(),
                file_name="direct_paste_style_listing.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
