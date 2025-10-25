# ===============================
# 📁 sidebar_info.py
# ===============================
import streamlit as st
import pandas as pd
from api_utils import get_sample_country_info_api,get_country_info_detail


def render_sidebar(merged_df):
    """Hiển thị sidebar thông tin quốc gia + AI (phiên bản có lazy loading)"""

    # --- Header ---
    st.sidebar.header("Thông tin quốc gia")

    # --- Dropdown chọn quốc gia ---
    country_list = merged_df["country_name"].sort_values().tolist()
    selected_country = st.sidebar.selectbox(
        "Chọn quốc gia",
        options=["-- Chọn quốc gia --"] + country_list,
        index=0
    )

    # Nếu chưa chọn (vẫn ở placeholder)
    if selected_country == "-- Chọn quốc gia --":
        st.sidebar.info("⬅️ Vui lòng chọn một quốc gia để xem thông tin chi tiết.")
        return None, None

    # ===============================
    # 🧭 Khi người dùng đã chọn quốc gia
    # ===============================
    country_data = merged_df[merged_df["country_name"] == selected_country].iloc[0]
    iso3_code = country_data["code"]

    # --- Lấy dữ liệu chi tiết từ API ---
    country_info = get_country_info_detail(country_data["code"])

    # --- Hiển thị thông tin chi tiết ---
    st.sidebar.subheader(f"🌍 {selected_country}")

    if "error" not in country_info:
        st.sidebar.write(f"**Mã ISO3:** `{country_info['code']}`")
        st.sidebar.write(f"**Tên chính thức:** {country_info['official']}")
        st.sidebar.write(f"**Thủ đô:** {country_info['capital']}")
        st.sidebar.write(f"**Khu vực:** {country_info['region']} ({country_info['subregion']})")
        st.sidebar.write(f"**Diện tích:** {country_info['area']:.2f} km²")
        st.sidebar.write(f"**Dân số:** {country_info['population']:,}")
        st.sidebar.write(f"**Múi giờ:** {', '.join(country_info['timezones'])}")
        st.sidebar.write(f"**Tọa độ:** ({country_info['latitude']:.2f}, {country_info['longitude']:.2f})")
        st.sidebar.write(f"**Mức thu nhập:** {country_info['income_level']}")

        # Tiền tệ
        if (curr := country_info.get("currencies")):
            st.sidebar.write("**Tiền tệ:** " + ", ".join(
                [f"{k}: {v.get('name')} ({v.get('symbol', 'N/A')})" for k, v in curr.items()]
            ))

        # Ngôn ngữ
        if (langs := country_info.get("languages")):
            st.sidebar.write("**Ngôn ngữ:** " + ", ".join([f"{k}: {v}" for k, v in langs.items()]))

        # Biên giới
        borders = ", ".join(country_info["borders"]) if country_info.get("borders") else "Không có"
        st.sidebar.write(f"**Biên giới:** {borders}")
    else:
        st.sidebar.error(country_info["error"])

    # --- Trả về kết quả cho main page ---
    return selected_country, iso3_code
