import streamlit as st
import plotly.express as px
import pandas as pd
import time
from api_utils import (
    get_country_data, get_country_info_api, get_sample_country_info_api,
    get_db_countries, valid_iso3_codes, indicator_mapping, geo_regions, get_country_data_by_iso3
)
from sidebar_info import render_sidebar
from data_processor import data_processor
from ai_analyzer import ai_analyzer

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
st.divider()

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
# SIDEBAR
# =========================
selected_country, iso3_code = render_sidebar(merged_df)

# =========================
# TRANG CHÍNH
# =========================
# Chỉ chạy khi đã chọn quốc gia
if selected_country:
    # Kiểm tra nếu quốc gia thay đổi
    if "last_country" not in st.session_state or st.session_state.last_country != selected_country:
        st.session_state.last_country = selected_country
        with st.spinner("🤖 Đang tải thông tin ..."):
            ai_info = ai_analyzer.analyze_country_overview(selected_country)
            st.session_state.ai_info = ai_info
    
    st.write(st.session_state.get("ai_info", ""))

    country_data = get_country_data_by_iso3(iso3_code=iso3_code)
    
    # Lưu trữ thông tin về các biểu đồ đã vẽ
    chart_data_list = []

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
        
        # Lưu thông tin biểu đồ để phân tích
        chart_info = {
            "indicator_name": indicator_name,
            "indicator_code": indicator_code,
            "data": df,
            "country_name": country_data['country_name'],
            "trend": "tăng" if len(df) > 1 and df['value'].iloc[-1] > df['value'].iloc[0] else "giảm",
            "latest_value": df['value'].iloc[-1] if not df.empty else None,
            "latest_year": df['year'].iloc[-1] if not df.empty else None,
            "min_value": df['value'].min() if not df.empty else None,
            "max_value": df['value'].max() if not df.empty else None,
            "average_value": df['value'].mean() if not df.empty else None
        }
        chart_data_list.append(chart_info)
        
        # =========================
        # PHÂN TÍCH AI CHO TỪNG BIỂU ĐỒ
        # =========================
        with st.expander(f"Phân tích: {indicator_name}", expanded=False):
            with st.spinner(f"Đang phân tích {indicator_name}..."):
                try:
                    # Tạo prompt phân tích cho từng chỉ số
                    indicator_prompt = f"""
                    Phân tích chỉ số {indicator_name} của {selected_country}:
                    - Giá trị hiện tại: {chart_info['latest_value']}
                    - Năm: {chart_info['latest_year']}
                    - Xu hướng: {chart_info['trend']}
                    - Giá trị thấp nhất: {chart_info['min_value']}
                    - Giá trị cao nhất: {chart_info['max_value']}
                    - Giá trị trung bình: {chart_info['average_value']:.2f}
                    
                    Dữ liệu qua các năm:
                    {df.to_string(index=False)}
                    
                    Hãy phân tích:
                    1. Ý nghĩa của chỉ số này
                    2. Xu hướng phát triển
                    3. Tác động đến nền kinh tế
                    4. So sánh với các năm trước
                    """
                    
                    # Gọi AI phân tích từng chỉ số
                    indicator_analysis = ai_analyzer.analyze_single_indicator(indicator_prompt)
                    st.write("### 📋 Phân tích chi tiết")
                    st.write(indicator_analysis)
                    
                    # HIỆN THỊ THỐNG KÊ THAY VÌ BẢNG ĐẦY ĐỦ
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(
                            label="Giá trị hiện tại",
                            value=f"{chart_info['latest_value']:,.2f}",
                            delta=f"{chart_info['trend']}"
                        )
                    with col2:
                        change_pct = ((df['value'].iloc[-1] - df['value'].iloc[0]) / df['value'].iloc[0] * 100) if df['value'].iloc[0] != 0 else 0
                        st.metric(
                            label="Thay đổi tổng",
                            value=f"{change_pct:.2f}%",
                            delta_color="normal"
                        )
                    with col3:
                        st.metric(
                            label="Thời kỳ",
                            value=f"{df['year'].min()}-{df['year'].max()}"
                        )
                    with col4:
                        st.metric(
                            label="Số năm dữ liệu",
                            value=f"{len(df)} năm"
                        )
                    
                    # THÊM TÙY CHỌN XEM DỮ LIỆU ĐẦY ĐỦ NẾU CẦN
                    with st.expander("📊 Xem dữ liệu chi tiết (tùy chọn)"):
                        st.dataframe(df, use_container_width=True)
                        
                except Exception as e:
                    st.error(f"Lỗi khi phân tích {indicator_name}: {str(e)}")

    # =========================
    # PHÂN TÍCH AI TỔNG QUAN TẤT CẢ BIỂU ĐỒ
    # =========================
    if chart_data_list:
        with st.expander("🤖 AI Phân tích tổng quan tất cả chỉ số", expanded=False):
            st.subheader("📈 Phân tích tổng quan kinh tế")
            
            with st.spinner("AI đang phân tích tổng hợp tất cả chỉ số..."):
                try:
                    # Tạo bảng tổng hợp dữ liệu
                    summary_data = []
                    for chart in chart_data_list:
                        if not chart['data'].empty:
                            df = chart['data']
                            change_pct = ((df['value'].iloc[-1] - df['value'].iloc[0]) / df['value'].iloc[0] * 100) if df['value'].iloc[0] != 0 else 0
                            summary_data.append({
                                'Chỉ số': chart['indicator_name'],
                                'Giá trị gần nhất': f"{chart['latest_value']:,.2f}",
                                'Năm': chart['latest_year'],
                                'Xu hướng': chart['trend'],
                                'Thay đổi (%)': f"{change_pct:.2f}%",
                                'Cao nhất': f"{chart['max_value']:,.2f}",
                                'Thấp nhất': f"{chart['min_value']:,.2f}"
                            })
                    
                    # Hiển thị bảng tổng hợp
                    if summary_data:
                        st.write("### 📊 Tổng hợp tất cả chỉ số")
                        summary_df = pd.DataFrame(summary_data)
                        st.dataframe(summary_df, use_container_width=True)
                        
                        # Phân tích tổng quan bằng AI
                        overall_prompt = f"""
                        Phân tích tổng quan nền kinh tế {selected_country} dựa trên {len(chart_data_list)} chỉ số:
                        
                        """
                        
                        for chart in chart_data_list:
                            df = chart['data']
                            change_pct = ((df['value'].iloc[-1] - df['value'].iloc[0]) / df['value'].iloc[0] * 100) if df['value'].iloc[0] != 0 else 0
                            overall_prompt += f"""
                            - {chart['indicator_name']}: {chart['latest_value']} ({chart['latest_year']}), xu hướng {chart['trend']} ({change_pct:.2f}%)
                            """
                        
                        overall_prompt += """
                        Hãy đưa ra đánh giá tổng quan về:
                        1. Tình hình kinh tế hiện tại
                        2. Mức độ ổn định và tăng trưởng
                        3. Các lĩnh vực mạnh/yếu
                        4. Triển vọng phát triển
                        """
                        
                        # Gọi AI phân tích tổng quan
                        overall_analysis = ai_analyzer.analyze_overall_economy(overall_prompt)
                        st.write("### 🧠 Phân tích tổng quan kinh tế")
                        st.write(overall_analysis)
                        
                except Exception as e:
                    st.error(f"Lỗi khi phân tích tổng quan: {str(e)}")

    # =========================
    # PHẦN THÔNG TIN TỪ AI (SIDEBAR)
    # =========================
    
    # Hiển thị trực tiếp phần phân tích nâng cao
    with st.expander(f"Phân tích nâng cao: {selected_country}", expanded=False):
        st.header(f"Báo cáo phân tích nâng cao cho {selected_country}")
        st.caption("Các phân tích này được mô phỏng tự động từ AI (không ảnh hưởng đến dữ liệu chính).")

        # Danh sách các chức năng mở rộng
        functions = {
            "Phân tích xu hướng kinh tế": ai_analyzer.analyze_economic_trends,
            "Phân tích nhân khẩu học": ai_analyzer.analyze_population_demographics,
            "Đánh giá tiềm năng phát triển": ai_analyzer.analyze_development_potential,
        }

        for title, analysis_function in functions.items():
            with st.expander(f"{title}"):
                with st.spinner(f"Đang xử lý {title.lower()}..."):
                    try:
                        content = analysis_function(selected_country)
                        st.write(content)
                    except Exception as e:
                        st.error(f"Lỗi khi phân tích: {str(e)}")
                    time.sleep(1)

        st.success("Hoàn tất phân tích mở rộng!")
else:
    st.sidebar.warning("Không có dữ liệu quốc gia trong database")
    st.info("⬅️ Hãy chọn một quốc gia ở thanh bên để xem dữ liệu chi tiết.")