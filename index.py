import streamlit as st
import plotly.express as px
import pandas as pd
import requests

st.set_page_config(page_title="World Map Interactive", layout="wide")

df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/2014_world_gdp_with_codes.csv")
# Gọi API
url = "https://restcountries.com/v3.1/all?fields=name,latlng,cca3"
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
# Parse JSON
data = response.json()
# Chuyển sang DataFrame
records = []
for country in data:
    if "name" in country and "latlng" in country:
        name = country["name"]["common"]
        lat, lon = country["latlng"]
        code= country["cca3"]
        records.append({
            "country": name,
            "latitude": lat,
            "longitude": lon,
            "code": code
        })
df_2 = pd.DataFrame(records)
# Chuẩn hóa tên cột về cùng kiểu
df.rename(columns={"CODE": "code", "COUNTRY": "country_name", "GDP (BILLIONS)": "gdp_billion"}, inplace=True)
# Merge theo mã quốc gia ISO3
merged_df = pd.merge(df, df_2, on="code", how="left")


fig = px.choropleth(merged_df, locations="code", color="gdp_billion",
                    hover_name="country_name",
                    color_continuous_scale=px.colors.sequential.Plasma,
                    title="World GDP in 2014",projection="natural earth")

st.plotly_chart(fig, use_container_width=True)

st.sidebar.header("Thông tin quốc gia")
# Tạo selectbox lấy danh sách quốc gia từ df
selected_country = st.sidebar.selectbox("Chọn quốc gia", df["country_name"].sort_values())

# Lọc thông tin quốc gia đã chọn
country_data = merged_df[merged_df["country_name"] == selected_country].iloc[0]
lat, lon = country_data["latitude"], country_data["longitude"]


# Focus bản đồ vào quốc gia được chọn
if pd.notna(lat) and pd.notna(lon):
    fig.update_geos(center={"lat": lat, "lon": lon}, projection_scale=4)  # zoom vừa phải
fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})

# Hiển thị thông tin chi tiết
st.sidebar.subheader(f"🌐 {selected_country}")
st.sidebar.write(f"**Mã quốc gia (ISO3):** `{country_data['code']}`")
st.sidebar.write(f"**GDP (tỷ USD):** {country_data['gdp_billion']:.2f}")
st.sidebar.write(f"**Tọa độ:** ({lat:.2f}, {lon:.2f})")

st.subheader("Toàn bộ dữ liệu 'gapminder' năm 2007")
st.dataframe(merged_df)