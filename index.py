import streamlit as st
import plotly.express as px
import pandas as pd
from api_utils import (
    get_country_data, get_country_info_api, get_sample_country_info_api,
    get_db_countries, valid_iso3_codes, indicator_mapping, geo_regions
)


# Ẩn sidebar mặc định của Streamlit multi-page app
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {display: none;}
        div[data-testid="collapsedControl"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# =========================
# 🔧 CẤU HÌNH GIAO DIỆN
# =========================
st.set_page_config(page_title="World Map Interactive", layout="wide")

# CSS
try:
    with open("style.css", "r",encoding="utf-8") as css_file:
        st.markdown(f"<style>{css_file.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("⚠️ Không tìm thấy file `style.css`.")

# Header HTML
try:
    with open("header.html", "r",encoding="utf-8") as html_file:
        st.markdown(html_file.read(), unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("⚠️ Không tìm thấy file `header.html`.")

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
# 🌍 HIỂN THỊ BẢN ĐỒ
# =========================
st.markdown("### 🌐 Bản đồ tương tác các chỉ số kinh tế")

# Chọn chỉ số hiển thị
col_label, col_dropdown = st.columns([1, 3])
with col_label:
    st.markdown("**Chọn chỉ số hiển thị:**")
with col_dropdown:
    selected_indicator = st.selectbox(
        "Chọn chỉ số",
        options=list(indicator_mapping.keys()),
        format_func=lambda x: indicator_mapping[x],
        label_visibility="collapsed"
    )

map_title = f"Bản đồ {indicator_mapping[selected_indicator]} năm 2024"
fig = px.choropleth(
    merged_df,
    locations="code",
    color=selected_indicator,
    hover_name="country_name",
    hover_data=["population", "gdp_per_capita", "unemployment_rate", "inflation_rate"],
    color_continuous_scale=px.colors.sequential.Plasma,
    title=map_title,
    projection="natural earth"
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# 📋 HIỂN THỊ BẢNG DỮ LIỆU
# =========================
def format_df(df):
    """Định dạng lại bảng dữ liệu cho dễ đọc."""
    df = df.copy()
    for col in ["gdp_billion", "gdp_per_capita", "unemployment_rate", "inflation_rate", "latitude", "longitude"]:
        if col in df:
            df[col] = df[col].round(2)

    df = df.rename(columns={
        "code": "Mã ISO",
        "country_name": "Tên quốc gia",
        "gdp_billion": "Tổng GDP (tỷ USD)",
        "population": "Dân số",
        "gdp_per_capita": "GDP bình quân (USD)",
        "unemployment_rate": "Tỷ lệ thất nghiệp (%)",
        "inflation_rate": "Tỷ lệ lạm phát (%)",
        "latitude": "Vĩ độ",
        "longitude": "Kinh độ"
    })
    return df

display_df = format_df(merged_df)

# Tạo mapping format cho Styler
format_map = {
    "Tổng GDP (tỷ USD)": "{:,.2f}",
    "Dân số": "{:,.0f}",               
    "GDP bình quân (USD)": "{:,.2f}",
    "Tỷ lệ thất nghiệp (%)": "{:,.2f}",
    "Tỷ lệ lạm phát (%)": "{:,.2f}",
    "Vĩ độ": "{:,.2f}",
    "Kinh độ": "{:,.2f}"
}
styled = display_df.style.format(format_map)


st.subheader("Dữ liệu các chỉ số kinh tế quốc gia:")
search_valid = st.text_input("Tìm kiếm quốc gia (theo tên hoặc mã ISO):", key="valid_search")

if search_valid:
    display_df = display_df[
        display_df["Tên quốc gia"].str.contains(search_valid, case=False, na=False) |
        display_df["Mã ISO"].str.contains(search_valid, case=False, na=False)
    ]
st.dataframe(styled, use_container_width=True, height=400)

# =========================
# 📊 BIỂU ĐỒ TRÒN PHÂN BỐ GDP & DÂN SỐ
# =========================
geo_df = excluded_df[excluded_df["code"].isin(geo_regions)]
if not geo_df.empty:
    st.markdown("### 📊 Phân bố kinh tế & dân số theo khu vực")

    # Format text hiển thị khi hover
    geo_df["hover_gdp"] = (
        "Khu vực: " + geo_df["country_name"].astype(str) +
        "<br>GDP (tỷ USD): " + geo_df["gdp_billion"].map("{:,.2f}".format) +
        "<br>Dân số: " + geo_df["population"].map("{:,.0f}".format)
    )
    geo_df["hover_pop"] = geo_df["hover_gdp"]  # dùng chung format

    # Biểu đồ tròn GDP
    fig_gdp = px.pie(
        geo_df,
        values="gdp_billion",
        names="country_name",
        title="💰 Tỷ trọng GDP theo khu vực",
        hole=0.3
    )
    fig_gdp.update_traces(textinfo="percent+label", hovertemplate="%{customdata}")
    fig_gdp.update_traces(customdata=geo_df["hover_gdp"])

    # Biểu đồ tròn Dân số
    fig_pop = px.pie(
        geo_df,
        values="population",
        names="country_name",
        title="👥 Tỷ trọng dân số theo khu vực",
        hole=0.3
    )
    fig_pop.update_traces(textinfo="percent+label", hovertemplate="%{customdata}")
    fig_pop.update_traces(customdata=geo_df["hover_pop"])

    # Hiển thị song song
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_gdp, use_container_width=True)
    with col2:
        st.plotly_chart(fig_pop, use_container_width=True)
else:
    st.info("Không có nhóm khu vực địa lý trong dữ liệu bị loại.")

# =========================
# 💰 NHÓM THU NHẬP / PHÁT TRIỂN KINH TẾ
# =========================
income_groups = [
    "HIC",  # High income
    "UMC",  # Upper middle income
    "MIC",  # Middle income
    "LMC",  # Lower middle income
    "LIC",  # Low income
    "LMY",  # Low & middle income
    "LDC",  # Least developed countries (UN)
    "HPC",  # Heavily indebted poor countries
]

income_df = excluded_df[excluded_df["code"].isin(income_groups)]

if not income_df.empty:
    st.markdown("### 💸 Phân bố GDP & dân số theo **nhóm thu nhập** (World Bank classification)")

    # Biểu đồ tròn GDP
    fig_gdp_income = px.pie(
        income_df,
        values="gdp_billion",
        names="country_name",
        title="💰 Tỷ trọng GDP theo nhóm thu nhập",
        hover_data=["code", "gdp_billion", "population"],
        hole=0.3
    )
    fig_gdp_income.update_traces(textinfo="percent+label")

    # Biểu đồ tròn Dân số
    fig_pop_income = px.pie(
        income_df,
        values="population",
        names="country_name",
        title="👥 Tỷ trọng dân số theo nhóm thu nhập",
        hover_data=["code", "population", "gdp_billion"],
        hole=0.3
    )
    fig_pop_income.update_traces(textinfo="percent+label")

    # Hiển thị song song
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_gdp_income, use_container_width=True)
    with col2:
        st.plotly_chart(fig_pop_income, use_container_width=True)

    # Hiển thị bảng dữ liệu gốc
    st.markdown("#### 📋 Dữ liệu chi tiết theo nhóm thu nhập")
    income_display = format_df(income_df)
    st.dataframe(
        income_display.style.format({
            "Tổng GDP (tỷ USD)": "{:,.2f}",
            "Dân số": "{:,.0f}"
        }),
        use_container_width=True,
        height=400
    )

else:
    st.info("Không có nhóm thu nhập trong dữ liệu bị loại.")

# Bảng dữ liệu bị loại
if not excluded_df.empty:
    st.subheader("🚫 Dữ liệu bị loại (không ánh xạ được quốc gia)")
    excluded_display = format_df(excluded_df)
    st.dataframe(excluded_display, use_container_width=True, height=400)

