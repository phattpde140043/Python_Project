import streamlit as st
import plotly.express as px
import pandas as pd
from api_utils import (
    get_country_data, get_country_info_api, get_sample_country_info_api,
    get_db_countries, valid_iso3_codes, indicator_mapping, geo_regions,get_country_data_by_iso3
)
from sidebar_info import render_sidebar
from connect_AI import get_country_info

# =========================
# 🔧 CẤU HÌNH GIAO DIỆN
# =========================
st.markdown("""
    <style>
        /* Ẩn danh sách link trang (index / Data_Page) */
        div[data-testid="stSidebarNav"] {display: none;}
        /* Ẩn nút mũi tên collapse mặc định */
        div[data-testid="collapsedControl"] {display: none;}
    </style>
""", unsafe_allow_html=True)
# =========================
# 🏷️ HEADER PYTHON-THUẦN
# =========================
st.title("📊 Dữ liệu kinh tế quốc gia")
st.divider()  # tạo một đường kẻ ngang (Streamlit 1.22+)
# =========================
# 📊 XỬ LÝ DỮ LIỆU
# =========================
def process_country_data():
    """Lấy dữ liệu từ DB và phân loại hợp lệ / bị loại."""
    data = get_db_countries()
    valid, excluded = [], []

    for country in data:
        name = country.get("name", "").lower()
        iso = country.get("iso_code", None)
        entry = {
            "code": iso,
            "country_name": country.get("name"),
            "gdp_billion": country.get("indicator", {}).get("NY.GDP.MKTP.CD", 0) / 1e9,
            "population": country.get("indicator", {}).get("SP.POP.TOTL"),
            "gdp_per_capita": country.get("indicator", {}).get("NY.GDP.PCAP.CD"),
            "unemployment_rate": country.get("indicator", {}).get("SL.UEM.TOTL.ZS"),
            "inflation_rate": country.get("indicator", {}).get("FP.CPI.TOTL.ZG")
        }

        if name == "world" or iso not in valid_iso3_codes:
            excluded.append(entry)
        else:
            valid.append(entry)

    return pd.DataFrame(valid), pd.DataFrame(excluded)

def enrich_with_coordinates(df):
    """Bổ sung tọa độ từ API."""
    coords = []
    for code in df["code"]:
        info = get_sample_country_info_api(code)
        coords.append({
            "code": code,
            "latitude": info.get("latitude") if "error" not in info else None,
            "longitude": info.get("longitude") if "error" not in info else None
        })
    return df.merge(pd.DataFrame(coords), on="code", how="left")

# Chuẩn bị dữ liệu
valid_df, excluded_df = process_country_data()
merged_df = enrich_with_coordinates(valid_df)
# =========================
# 🧭 SIDEBAR
# =========================
selected_country, iso3_code = render_sidebar(merged_df)

# =========================
# 🖥️ TRANG CHÍNH
# =========================
# Chỉ chạy khi đã chọn quốc gia
if selected_country:
    # Kiểm tra nếu quốc gia thay đổi
    if "last_country" not in st.session_state or st.session_state.last_country != selected_country:
        st.session_state.last_country = selected_country
        with st.spinner("🤖 Đang tải thông tin ..."):
            ai_info = get_country_info(selected_country)
            st.session_state.ai_info = ai_info
    st.write(st.session_state.get("ai_info", ""))

    country_data = get_country_data_by_iso3(iso3_code=iso3_code)

    for indicator_code, indicator_data in country_data["data"].items():
        # Chuẩn bị DataFrame cho từng indicator
        df = pd.DataFrame(indicator_data["data"])
        if df.empty:
            continue

        # Lấy tên đầy đủ của chỉ số từ dữ liệu JSON
        indicator_name = indicator_data.get("indicator_name", indicator_code)
        chart_title = f"{indicator_name} của {country_data['country_name']}"

        # Vẽ line chart riêng cho từng indicator
        fig = px.line(
            df,
            x="year",
            y="value",
            markers=True,
            title=chart_title,
            labels={"year": "Năm", "value": indicator_name}
        )

        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("⬅️ Hãy chọn một quốc gia ở thanh bên để xem dữ liệu chi tiết.")





