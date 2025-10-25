from groq import Groq
import os
from data_processor import data_processor

# Cấu hình API key cho Groq
os.environ['GROQ_API_KEY'] = "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"

class AIAnalyzer:
    def __init__(self):
        self.client = Groq()
        self.model_names = [
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
        ]
        self.data_processor = data_processor
    
    def run_with_models(self, prompt):
        """Thử tất cả model cho đến khi thành công"""
        for model_name in self.model_names:
            try:
                print(f"  Dang su dung model: {model_name}")
                chat_completion = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model_name,
                    temperature=0.7,
                    max_tokens=2048,
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                print(f"  Loi voi {model_name}: {str(e)[:100]}...")
                continue
        return "Khong the tim thay model phu hop."
    
    def analyze_country_overview(self, country_name):
        """Phân tích tổng quan quốc gia với dữ liệu thực tế"""
        # Lấy mã quốc gia từ tên
        country_code = self.data_processor.get_country_code_by_name(country_name)
        if not country_code:
            return f"Không tìm thấy dữ liệu cho quốc gia: {country_name}"
        
        # Lấy và xử lý dữ liệu
        country_summary = self.data_processor.get_country_data_summary(country_code)
        if not country_summary:
            return f"Không có dữ liệu để phân tích cho {country_name}"
        
        data_context = self.data_processor.format_data_for_ai(country_summary)
        
        # Lấy thêm dữ liệu so sánh khu vực
        region_countries = self._get_region_countries(country_summary["country_info"].get("region"))
        
        prompt = f"""
DỮ LIỆU THỰC TẾ CỦA {country_name.upper()}:
{data_context}

DỮ LIỆU THAM KHẢO:
- Khu vực: {country_summary['country_info'].get('region', 'Chưa xác định')}
- Mức thu nhập: {country_summary['country_info'].get('income_level', 'Chưa xác định')}
- Các quốc gia cùng khu vực: {', '.join(region_countries[:5]) if region_countries else 'Không có dữ liệu'}

HÃY PHÂN TÍCH TỔNG QUAN QUỐC GIA {country_name.upper()}:

1. ĐẶC ĐIỂM NỔI BẬT:
   - Vị trí địa lý và đặc điểm tự nhiên
   - Quy mô dân số và cấu trúc nhân khẩu
   - Vị thế trong khu vực

2. TÌNH HÌNH KINH TẾ:
   - Quy mô nền kinh tế (GDP)
   - Thu nhập bình quân đầu người
   - Tình hình lạm phát và việc làm
   - Xuất nhập khẩu

3. PHÁT TRIỂN XÃ HỘI:
   - Chất lượng cuộc sống
   - Tần suất và sức khỏe
   - Giáo dục và đào tạo

4. MÔI TRƯỜNG VÀ BỀN VỮNG:
   - Phát thải khí hậu
   - Sử dụng năng lượng
   - Bảo tồn tài nguyên

5. ĐÁNH GIÁ TỔNG QUAN:
   - Điểm mạnh chính
   - Thách thức cần giải quyết
   - Cơ hội phát triển

YÊU CẦU:
- Phân tích dựa trên dữ liệu thực tế đã cung cấp
- So sánh với mức trung binh khu vực nếu có dữ liệu
- Chỉ rõ những điểm mạnh và hạn chế
- Trình bày rõ ràng, có cấu trúc
- Ngôn ngữ: Tiếng Việt
- Độ dài: 400-500 từ
"""
        return self.run_with_models(prompt)
    
    def analyze_economic_trends(self, country_name):
        """Phân tích xu hướng kinh tế"""
        country_code = self.data_processor.get_country_code_by_name(country_name)
        if not country_code:
            return f"Khong tim thay du lieu cho quoc gia: {country_name}"
        
        country_summary = self.data_processor.get_country_data_summary(country_code)
        if not country_summary:
            return f"Khong co du lieu de phan tich cho {country_name}"
        
        data_context = self.data_processor.format_data_for_ai(country_summary)
        
        # Lấy dữ liệu xu hướng GDP 10 năm
        gdp_trend = self.data_processor.get_indicator_trend(country_code, 'NY.GDP.MKTP.CD', 10)
        
        prompt = f"""
DỮ LIỆU KINH TẾ {country_name.upper()}:
{data_context}

XU HƯỚNG KINH TẾ 10 NĂM GẦN ĐÂY:
{self._format_trend_data(gdp_trend)}

HÃY PHÂN TÍCH XU HƯỚNG KINH TẾ:

1. TĂNG TRƯỞNG VA ỔN ĐỊNH:
   - Tốc độ tăng trưởng GDP qua các năm
   - Kiểm sóat lạm phát
   - Ổn định tỷ giá và tiền tệ

2. CƠ CẤU NGÀNH KINH TẾ:
   - Đóng góp của các ngành chủ lực
   - Chiến lược cơ cấu kinh tế
   - Ngành công nghiệp và dịch vụ

3. ĐẦU TƯ VÀ THƯƠNG MẠI:
   - Thu hút đầu tư nước ngòai
   - Cán cân thương mại
   - Hội nhập kinh tế quốc tế

4. CHÍNH SÁCH KINH TẾ:
   - Các chính sách tiền tệ và tài khóa
   - Khuyến khích đầu tư
   - Hỗ trợ phát triển

5. DỰ BÁO VÀ KHUYẾN NGHỊ:
   - Triển vọng ngắn hạn và dài hạn
   - Cơ hội và thách thức
   - Chính sách cần thiết

YÊU CẦU: Phân tích chuyên sâu, có số liệu minh họa, ngôn ngữ Tiếng Việt.
"""
        return self.run_with_models(prompt)
    
    def analyze_population_demographics(self, country_name):
        """Phân tích nhân khẩu học"""
        country_code = self.data_processor.get_country_code_by_name(country_name)
        if not country_code:
            return f"Khong tim thay du lieu cho quoc gia: {country_name}"
        
        country_summary = self.data_processor.get_country_data_summary(country_code)
        if not country_summary:
            return f"Khong co du lieu de phan tich cho {country_name}"
        
        data_context = self.data_processor.format_data_for_ai(country_summary)
        
        # Lấy dữ liệu xu hướng dân số
        pop_trend = self.data_processor.get_indicator_trend(country_code, 'SP.POP.TOTL', 10)
        
        prompt = f"""
DỮ LIỆU DÂN SỐ {country_name.upper()}:
{data_context}

XU HƯỚNG DÂN SỐ 10 NĂM GẦN ĐÂY:
{self._format_trend_data(pop_trend)}

HÃY PHÂN TÍCH NHÂN KHẨU HỌC:

1. QUY MÔ VÀ PHÂN BỐ:
   - Tổng dân số và mật độ
   - Phân bổ theo vùng miền
   - Tỷ lệ đô thị hóa

2. CƠ CẤU DÂN SỐ:
   - Phân bổ theo độ tuổi (tháp dân số)
   - Tỷ lệ giới tính
   - Cơ cấu dân tộc

3. BIẾN ĐỘNG DÂN SỐ:
   - Tỷ lệ sinh và tử
   - Di cư và di dân
   - Tuổi thọ trung bình

4. TÁC ĐỘNG KINH TẾ - XÃ HỘI:
   - Lực lương lao động
   - Già hóa dân số
   - Chính sách dân số

5. VẤN ĐỀ NỔI BẬT:
   - Cơ hội dân số vàng
   - Áp lực việc làm
   - Hệ thống an sinh

YÊU CẦU: Phân tích chi tiết, có ví dụ cụ thể, ngôn ngữ Tiếng Việt.
"""
        return self.run_with_models(prompt)
    
    def analyze_development_potential(self, country_name):
        """Phân tích tiềm năng phát triển"""
        country_code = self.data_processor.get_country_code_by_name(country_name)
        if not country_code:
            return f"Khong tim thay du lieu cho quoc gia: {country_name}"
        
        country_summary = self.data_processor.get_country_data_summary(country_code)
        if not country_summary:
            return f"Khong co du lieu de phan tich cho {country_name}"
        
        data_context = self.data_processor.format_data_for_ai(country_summary)
        
        # Lấy top countries trong khu vực để so sánh - THÊM KIỂM TRA LỖI
        top_gdp_countries = []
        try:
            top_gdp_countries = self.data_processor.get_top_countries('NY.GDP.MKTP.CD', 5)
        except Exception as e:
            print(f"Loi khi lay top countries: {e}")
        
        # Lấy thông tin khu vực để so sánh
        region = country_summary['country_info'].get('region', 'Unknown')
        region_countries = self._get_region_countries(region)
        
        prompt = f"""
    DỮ LIỆU PHÁT TRIỂN {country_name.upper()}:
    {data_context}

    SO SÁNH VỚI CÁC QUỐC GIA TRONG KHU VỰC:
    - Khu vực: {region}
    - Các quốc gia cùng khu vực: {', '.join(region_countries[:5]) if region_countries else 'Khong co du lieu'}

    {self._format_comparison_data(top_gdp_countries) if top_gdp_countries else 'Du lieu so sanh se duoc cap nhat sau'}

    HÃY PHÂN TÍCH TIỀM NĂNG PHÁT TRIỂN CỦA {country_name.upper()}:

    1. NĂNG LỰC CẠNH TRANH QUỐC GIA:
    - Vị thế kinh tế trong khu vực
    - Môi trường đầu tư và kinh doanh
    - Năng lực đổi mới sáng tạo

    2. PHÁT TRIỂN BỀN VỮNG:
    - Tình trạng phát triển kinh tế - xã hội
    - Bảo vệ môi trường và tài nguyên
    - Công bằng xã hôi và phúc lợi

    3. HỘI NHẬP QUỐC TẾ:
    - Vị thế trong khu vuc và thế giới
    - Quan hệ hợp tác quốc tế
    - Tham gia các hiệp định thương mại

    4. NGUỒN LỰC PHÁT TRIỂN:
    - Chất lương nhân lực và đào tạo
    - Tài nguyên thiên nhiên sẵn có
    - Hệ thống cơ sở hạ tầng

    5. TRIỂN VỌNG PHÁT TRIỂN 5 NĂM TỚI:
    - Kịch bản phát triển cơ bản
    - Kịch bản phát triển tối ưu
    - Kịch bản phát triển cẩn trọng

    YÊU CẦU:
    - Phân tích dựa trên dữ liệu thực tế đã cung cấp
    - Đánh giá khả năng cạnh tranh và phát triển
    - Đề xuất huớng phát triển chiến lược
    - Ngôn ngữ: Tiếng Việt
    - Đô dài: 400-500 từ
    """
        return self.run_with_models(prompt)
    
    def _get_region_countries(self, region):
        """Lấy danh sách quốc gia trong cùng khu vực"""
        if not region:
            return []
        all_countries = self.data_processor.db.get_all_countries()
        return [country['name'] for country in all_countries if country.get('region') == region]
    
    def _format_trend_data(self, trend_data):
        """Định dạng dữ liệu xu hướng"""
        if not trend_data:
            return "Khong co du lieu xu huong"
        
        formatted = []
        for item in trend_data[:5]:  # Lấy 5 năm gần nhất
            formatted.append(f"- {item['year']}: {item.get('value', 'N/A')} {item.get('unit', '')}")
        
        return "\n".join(formatted)
    
    def _format_comparison_data(self, comparison_data):
        """Định dạng dữ liệu so sánh"""
        if not comparison_data:
            return "Chua co du lieu so sanh voi cac quoc gia hang dau. Phan tich se dua tren du lieu hien co cua quoc gia."
        
        formatted = ["SO SANH VOI CAC QUOC GIA CO GDP CAO NHAT:"]
        for i, country in enumerate(comparison_data[:5], 1):
            country_name = country.get('country_name', 'N/A')
            value = country.get('value', 'N/A')
            unit = country.get('unit', '')
            year = country.get('year', 'N/A')
            formatted.append(f"{i}. {country_name}: {value} {unit} (nam {year})")
        
        return "\n".join(formatted)
    
    def comprehensive_analysis(self, country_name):
        """Phân tích toàn diện"""
        print(f"\nBat dau phan tich toan dien cho {country_name}...")
        
        analyses = {
            "Tổng quan quốc gia": self.analyze_country_overview(country_name),
            "Xu hướng kinh te": self.analyze_economic_trends(country_name),
            "Nhân khẩu hoc": self.analyze_population_demographics(country_name),
            "Tiềm năng phát triển": self.analyze_development_potential(country_name),
        }
        
        return analyses
    def analyze_single_indicator(self, analysis_prompt):
        """Phân tích chi tiết cho từng chỉ số riêng lẻ bằng AI thực"""
        try:
                # Thêm hướng dẫn cụ thể cho AI
                enhanced_prompt = f"""
        {analysis_prompt}

        HÃY PHÂN TÍCH CHUYÊN SÂU CHỈ SỐ NÀY:

        1. DIỄN GIẢI Ý NGHĨA:
        - Chỉ số này đo lường điều gì?
        - Tầm quan trọng trong nền kinh tế
        - Ngưỡng giá trị tốt/xấu

        2. PHÂN TÍCH XU HƯỚNG:
        - Đánh giá xu hướng {analysis_prompt.split('Xu hướng: ')[1].split('-')[0].strip()} 
        - So sánh giá trị hiện tại với trung bình và cực trị
        - Nhận định về tốc độ thay đổi

        3. TÁC ĐỘNG THỰC TẾ:
        - Ảnh hưởng đến người dân và doanh nghiệp
        - Tác động đến các chỉ số kinh tế khác
        - Ý nghĩa với nhà đầu tư

        4. DỰ BÁO VÀ KHUYẾN NGHỊ:
        - Triển vọng ngắn hạn
        - Khuyến nghị chính sách
        - Biện pháp quản lý rủi ro

        YÊU CẦU:
        - Phân tích dựa trên số liệu cụ thể đã cung cấp
        - Đưa ra nhận định khách quan
        - Ngôn ngữ tiếng Việt tự nhiên, chuyên môn
        - Ngắn gọn 50 - 100 từ nhưng đủ rõ ràng,có bố cục
        - Không cần trả lại bảng dữ liệu chỉ đưa thông số và phân tích
        - làm tròn các chỉ số .2f nếu quá dài
        """
                return self.run_with_models(enhanced_prompt)
        except Exception as e:
                return f"Lỗi khi phân tích chỉ số: {str(e)}"

    def analyze_overall_economy(self, analysis_prompt):
        """Phân tích tổng quan toàn bộ nền kinh tế bằng AI thực"""
        try:
            # Tạo prompt chi tiết cho phân tích tổng quan
            enhanced_prompt = f"""
    {analysis_prompt}

    HÃY PHÂN TÍCH TỔNG QUAN TOÀN DIỆN NỀN KINH TẾ:

    1. ĐÁNH GIÁ TỔNG THỂ:
    - Sức khỏe tổng thể của nền kinh tế
    - Mức độ ổn định và bền vững
    - Vị thế cạnh tranh trong khu vực

    2. PHÂN TÍCH ĐA CHỈ SỐ:
    - Mối tương quan giữa các chỉ số
    - Chỉ số nào đang dẫn dắt tăng trưởng?
    - Chỉ số nào cần cải thiện?

    3. PHÂN TÍCH ĐIỂM MẠNH - ĐIỂM YẾU:
    - ĐIỂM MẠNH CHÍNH (3-4 điểm)
    - ĐIỂM YẾU CẦN KHẮC PHỤC (3-4 điểm)
    - CƠ HỘI PHÁT TRIỂN
    - THÁCH THỨC TIỀM ẨN

    4. ĐÁNH GIÁ RỦI RO VÀ CƠ HỘI:
    - Rủi ro ngắn hạn cần theo dõi
    - Cơ hội tăng trưởng dài hạn
    - Yếu tố bên ngoài tác động

    5. KHUYẾN NGHỊ CHIẾN LƯỢC:
    - Ưu tiên chính sách trước mắt
    - Chiến lược phát triển trung hạn
    - Giải pháp cải cách cấu trúc

    YÊU CẦU:
    - Phân tích dựa trên dữ liệu thực tế từ tất cả chỉ số
    - Đưa ra nhận định định lượng khi có số liệu
    - So sánh tương đối giữa các chỉ số
    - Ngôn ngữ tiếng Việt chuyên nghiệp, rõ ràng
    - Kết luận có tính hành động cao
    - Ngắn gọn 50 - 100 từ nhưng đủ rõ ràng , có bố cục
    - Không cần trả lại bảng dữ liệu chỉ đưa thông số và phân tích
    - làm tròn các chỉ số .2f nếu quá dài
    """
            return self.run_with_models(enhanced_prompt)
        except Exception as e:
            return f"Lỗi khi phân tích tổng quan: {str(e)}"

ai_analyzer = AIAnalyzer()