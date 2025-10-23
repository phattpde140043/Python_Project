import streamlit as st
import plotly.express as px
import pandas as pd
from api_utils import get_country_data, get_country_info_api, get_sample_country_info_api, get_db_countries
from connect_AI import get_country_info

# Đọc nội dung file CSS
try:
    with open("style.css", "r") as css_file:
        css = css_file.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("Không tìm thấy file style.css. Vui lòng đảm bảo file tồn tại trong thư mục hiện tại.")

# Cấu trúc HTML của headbar
try:
    with open("header.html", "r") as html_file:
        html = html_file.read()
    st.markdown(f"{html}", unsafe_allow_html=True)
except FileNotFoundError:
    st.error("Không tìm thấy file header.html. Vui lòng đảm bảo file tồn tại trong thư mục hiện tại.")

# CSS để hạn chế margin
st.markdown("""
    <style>
        .main .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .stPlotlyChart {
            margin-top: 0px;
            margin-bottom: 0px;
        }
        .stSelectbox {
            margin-top: 0px;
            margin-bottom: 0px;
        }
        .stMarkdown {
            margin-top: 0px;
            margin-bottom: 0px;
        }
    </style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="World Map Interactive", layout="wide")

# Ánh xạ tên cột sang tiếng Việt
indicator_mapping = {
    "gdp_billion": "Tổng GDP (tỷ USD)",
    "population": "Dân số",
    "gdp_per_capita": "GDP bình quân đầu người (USD)",
    "unemployment_rate": "Tỷ lệ thất nghiệp (%)",
    "inflation_rate": "Tỷ lệ lạm phát (%)"
}

# Danh sách mã ISO3 hợp lệ (một phần, dựa trên tiêu chuẩn ISO 3166-1 alpha-3)
valid_iso3_codes ={'DZA', 'BEL', 'GNB', 'HUN', 'NLD', 'BWA', 'BLZ', 'HKG',
                    'FIN', 'MLT', 'ARM', 'MNE', 'MNG', 'AUS', 'SWZ', 'MRT',
                    'URY', 'BIH', 'MDG', 'BRB', 'ECU', 'CAF', 'SUR', 'OMN',
                    'GIN', 'MAR', 'KHM', 'SWE', 'LVA', 'TJK', 'MWI', 'PRT',
                    'USA', 'HND', 'PHL', 'SDN', 'NPL', 'TKM', 'IRL', 'SOM',
                    'BOL', 'GMB', 'LBR', 'UKR', 'IRN', 'LUX', 'AUT', 'GEO',
                    'NIC', 'LBN', 'AGO', 'COD', 'ISR', 'CHE', 'THA', 'RUS',
                    'QAT', 'TTO', 'ITA', 'PRI', 'TLS', 'TZA', 'COL', 'ALB',
                    'ROU', 'COM', 'DNK', 'MDA', 'SRB', 'KEN', 'GBR', 'KGZ',
                    'GTM', 'JAM', 'KOR', 'COG', 'CYP', 'CHN', 'MDV', 'SYR',
                    'PSE', 'IND', 'ZAF', 'STP', 'PAK', 'SVN', 'POL', 'LTU',
                    'ESP', 'ARG', 'GRC', 'REU', 'HTI', 'CRI', 'SAU', 'GAB',
                    'NZL', 'SVK', 'NER', 'LBY', 'EGY', 'ERI', 'SLV', 'SEN',
                    'BEN', 'CHL', 'MLI', 'BTN', 'SLE', 'MKD', 'PRY', 'NOR',
                    'DEU', 'JOR', 'KWT', 'BGD', 'ARE', 'YEM', 'HRV', 'LSO',
                    'ZMB', 'MOZ', 'VNM', 'ETH', 'NAM', 'TUN', 'AZE', 'LKA',
                    'CZE', 'PAN', 'LAO', 'GHA', 'BLR', 'PER', 'AFG', 'LIE',
                    'BRA', 'DOM', 'IDN', 'IRQ', 'BGR', 'BDI', 'FRA', 'BFA',
                    'UZB', 'RWA', 'EST', 'VEN', 'CMR', 'CUB', 'MMR', 'TWN',
                    'KAZ', 'TUR', 'FJI', 'BHR', 'TCD', 'PNG', 'SGP', 'CIV',
                    'MEX', 'GUY', 'NGA', 'CAN', 'MUS', 'MYS', 'JPN', 'ISL',
                    'TGO', 'AND', 'UGA', 'ZWE', 'DJI', 'GNQ'}

# Hàm xử lý dữ liệu từ get_db_countries()
def process_country_data():
    data = get_db_countries()
    valid_data = []
    excluded_data = []
    
    for country in data:
        name = country.get("name", "").lower()
        iso_code = country.get("iso_code", None)
        # Kiểm tra điều kiện để phân loại hàng
        if name == "world" or iso_code not in valid_iso3_codes:
            excluded_data.append({
                "code": iso_code,
                "country_name": country.get("name", None),
                "gdp_billion": country.get("indicator", {}).get("NY.GDP.MKTP.CD", 0) / 1e9,
                "population": country.get("indicator", {}).get("SP.POP.TOTL", None),
                "gdp_per_capita": country.get("indicator", {}).get("NY.GDP.PCAP.CD", None),
                "unemployment_rate": country.get("indicator", {}).get("SL.UEM.TOTL.ZS", None),
                "inflation_rate": country.get("indicator", {}).get("FP.CPI.TOTL.ZG", None)
            })
        else:
            valid_data.append({
                "code": iso_code,
                "country_name": country.get("name", None),
                "gdp_billion": country.get("indicator", {}).get("NY.GDP.MKTP.CD", 0) / 1e9,
                "population": country.get("indicator", {}).get("SP.POP.TOTL", None),
                "gdp_per_capita": country.get("indicator", {}).get("NY.GDP.PCAP.CD", None),
                "unemployment_rate": country.get("indicator", {}).get("SL.UEM.TOTL.ZS", None),
                "inflation_rate": country.get("indicator", {}).get("FP.CPI.TOTL.ZG", None)
            })
    
    valid_df = pd.DataFrame(valid_data)
    excluded_df = pd.DataFrame(excluded_data)
    return valid_df, excluded_df

# Lấy dữ liệu từ get_db_countries()
valid_df, excluded_df = process_country_data()

# Lấy thông tin tọa độ từ API
def enrich_with_coordinates(df):
    coords = []
    for code in df["code"]:
        country_info = get_sample_country_info_api(code)
        if "error" not in country_info:
            coords.append({
                "code": code,
                "latitude": country_info.get("latitude"),
                "longitude": country_info.get("longitude")
            })
        else:
            coords.append({"code": code, "latitude": None, "longitude": None})
    coords_df = pd.DataFrame(coords)
    return df.merge(coords_df, on="code", how="left")

# Gộp dữ liệu với tọa độ
merged_df = enrich_with_coordinates(valid_df)

# Tạo hàng ngang cho nhãn và dropdown
col_label, col_dropdown = st.columns([1, 3])  # Nhãn chiếm 1/4, dropdown chiếm 3/4
with col_label:
    st.markdown("**Chọn chỉ số hiển thị:**", unsafe_allow_html=True)
with col_dropdown:
    selected_indicator = st.selectbox(
        "Chọn chỉ số",
        options=list(indicator_mapping.keys()),
        format_func=lambda x: indicator_mapping[x],  # Hiển thị tên tiếng Việt
        label_visibility="collapsed"  # Ẩn nhãn mặc định của selectbox
    )

# Tạo tiêu đề bản đồ động dựa trên chỉ số được chọn
map_title = f"Bản đồ {indicator_mapping[selected_indicator]} năm 2024"

# Tạo bản đồ
fig = px.choropleth(
    merged_df,
    locations="code",
    color=selected_indicator,  # Sử dụng cột được chọn từ dropdown
    hover_name="country_name",
    hover_data=["population", "gdp_per_capita", "unemployment_rate", "inflation_rate"],
    color_continuous_scale=px.colors.sequential.Plasma,
    title=map_title,
    projection="natural earth"
)

st.markdown('<div id="map"></div>', unsafe_allow_html=True)
st.plotly_chart(fig, use_container_width=True)

# Hiển thị bảng dữ liệu hợp lệ dùng để vẽ bản đồ
st.subheader("Dữ liệu dùng để vẽ bản đồ")
# Ô tìm kiếm cho bảng hợp lệ
search_term_valid = st.text_input("Tìm kiếm quốc gia (theo tên hoặc mã ISO):", key="search_valid")
# Định dạng lại merged_df để hiển thị đẹp hơn
display_df = merged_df.copy()
display_df["gdp_billion"] = display_df["gdp_billion"].round(2)  # Làm tròn 2 chữ số
display_df["gdp_per_capita"] = display_df["gdp_per_capita"].round(2)
display_df["unemployment_rate"] = display_df["unemployment_rate"].round(2)
display_df["inflation_rate"] = display_df["inflation_rate"].round(2)
display_df["latitude"] = display_df["latitude"].round(2)
display_df["longitude"] = display_df["longitude"].round(2)
# Đổi tên cột sang tiếng Việt để dễ hiểu
display_df = display_df.rename(columns={
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
# Lọc bảng theo từ khóa tìm kiếm
if search_term_valid:
    display_df = display_df[
        display_df["Tên quốc gia"].str.lower().str.contains(search_term_valid.lower(), na=False) |
        display_df["Mã ISO"].str.lower().str.contains(search_term_valid.lower(), na=False)
    ]
st.dataframe(display_df, use_container_width=True, height=400)

# Hiển thị bảng dữ liệu bị loại
st.subheader("Dữ liệu bị loại (không ánh xạ được với quốc gia)")
# Ô tìm kiếm cho bảng bị loại
search_term_excluded = st.text_input("Tìm kiếm quốc gia bị loại (theo tên hoặc mã ISO):", key="search_excluded")
# Định dạng lại excluded_df để hiển thị đẹp hơn
if not excluded_df.empty:
    display_excluded_df = excluded_df.copy()
    display_excluded_df["gdp_billion"] = display_excluded_df["gdp_billion"].round(2)
    display_excluded_df["gdp_per_capita"] = display_excluded_df["gdp_per_capita"].round(2)
    display_excluded_df["unemployment_rate"] = display_excluded_df["unemployment_rate"].round(2)
    display_excluded_df["inflation_rate"] = display_excluded_df["inflation_rate"].round(2)
    # Đổi tên cột sang tiếng Việt
    display_excluded_df = display_excluded_df.rename(columns={
        "code": "Mã ISO",
        "country_name": "Tên quốc gia",
        "gdp_billion": "Tổng GDP (tỷ USD)",
        "population": "Dân số",
        "gdp_per_capita": "GDP bình quân (USD)",
        "unemployment_rate": "Tỷ lệ thất nghiệp (%)",
        "inflation_rate": "Tỷ lệ lạm phát (%)"
    })
    # Lọc bảng theo từ khóa tìm kiếm
    if search_term_excluded:
        display_excluded_df = display_excluded_df[
            display_excluded_df["Tên quốc gia"].str.lower().str.contains(search_term_excluded.lower(), na=False) |
            display_excluded_df["Mã ISO"].str.lower().str.contains(search_term_excluded.lower(), na=False)
        ]
    st.dataframe(display_excluded_df, use_container_width=True, height=400)
else:
    st.write("Không có dữ liệu bị loại.")

# Sidebar
st.sidebar.header("Thông tin quốc gia")
selected_country = st.sidebar.selectbox("Chọn quốc gia", valid_df["country_name"].sort_values())

# Lọc thông tin quốc gia đã chọn
country_data = merged_df[merged_df["country_name"] == selected_country].iloc[0]
lat, lon = country_data["latitude"], country_data["longitude"]

# Focus bản đồ vào quốc gia được chọn
if pd.notna(lat) and pd.notna(lon):
    fig.update_geos(center={"lat": lat, "lon": lon}, projection_scale=4)  # Zoom vừa phải
fig.update_layout(margin={"r":0, "t":30, "l":0, "b":0})

# Lấy thông tin chi tiết từ API
country_info = get_sample_country_info_api(country_data['code'])

# Hiển thị thông tin chi tiết
st.sidebar.subheader(f"🌐 {selected_country}")
if "error" not in country_info:
    st.sidebar.write(f"**Mã quốc gia (ISO3):** `{country_info['code']}`")
    st.sidebar.write(f"**Tên thông thường:** {country_info['common']}")
    st.sidebar.write(f"**Tên chính thức:** {country_info['official']}")
    st.sidebar.write(f"**Thủ đô:** {country_info['capital']}")
    st.sidebar.write(f"**Khu vực:** {country_info['region']}")
    st.sidebar.write(f"**Tiểu khu vực:** {country_info['subregion']}")
    st.sidebar.write(f"**Diện tích (km²):** {country_info['area']:.2f}")
    st.sidebar.write(f"**Dân số:** {country_info['population']:,}")
    st.sidebar.write(f"**Múi giờ:** {', '.join(country_info['timezones'])}")
    st.sidebar.write(f"**Tọa độ:** ({country_info['latitude']:.2f}, {country_info['longitude']:.2f})")
    st.sidebar.write(f"**Mức thu nhập:** {country_info['income_level']}")
    # Xử lý currencies
    currencies = country_info['currencies']
    currency_str = "N/A"
    if currencies:
        currency_list = [f"{k}: {v.get('name', 'N/A')} ({v.get('symbol', 'N/A')})" for k, v in currencies.items()]
        currency_str = ", ".join(currency_list)
    st.sidebar.write(f"**Tiền tệ:** {currency_str}")
    
    # Xử lý languages
    languages = country_info['languages']
    language_str = "N/A"
    if languages:
        language_list = [f"(**{k}**: {v})" for k, v in languages.items()]
        language_str = ", ".join(language_list) if language_list else "N/A"
    st.sidebar.write(f"**Ngôn ngữ:** {language_str}")
    
    # Xử lý borders
    borders = country_info['borders']
    border_str = ", ".join(borders) if borders else "Không có"
    st.sidebar.write(f"**Biên giới:** {border_str}")
else:
    st.sidebar.error(country_info['error'])

# Thêm phần thông tin từ AI với button
st.sidebar.subheader("🤖 Thông tin từ AI")
if st.sidebar.button("Tìm hiểu thêm về quốc gia này"):
    with st.sidebar:
        with st.spinner('Đang tải thông tin...'):
            ai_info = get_country_info(selected_country)
            st.write(ai_info)

st.markdown('<div id="data"></div>', unsafe_allow_html=True)
st.subheader("Toàn bộ dữ liệu 'gapminder' năm 2007")
st.dataframe(merged_df)