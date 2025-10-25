from database_manager import db_manager
import pandas as pd

class DataProcessor:
    def __init__(self):
        self.db = db_manager
    
    def get_country_data_summary(self, country_code):
        """Tổng hợp dữ liệu của một quốc gia"""
        print(f"Thu thap du lieu cho {country_code}...")
        
        # Lấy thông tin quốc gia
        country_info = self.db.get_country_by_code(country_code)
        if not country_info:
            return None
        
        # Lấy tất cả indicators
        all_indicators = self.db.get_all_indicators()
        
        # Lấy dữ liệu mới nhất cho các chỉ số quan trọng
        economic_data = self._get_economic_data(country_code)
        population_data = self._get_population_data(country_code)
        environment_data = self._get_environment_data(country_code)
        social_data = self._get_social_data(country_code)
        
        summary = {
            "country_info": country_info,
            "total_indicators": len(all_indicators),
            "economic_indicators": economic_data,
            "population_indicators": population_data,
            "environment_indicators": environment_data,
            "social_indicators": social_data,
            "available_years": self.db.get_available_years()
        }
        
        return summary
    
    def _get_economic_data(self, country_code):
        """Lấy dữ liệu kinh tế"""
        economic_indicators = [
            'NY.GDP.MKTP.CD',  # GDP
            'NY.GDP.PCAP.CD',  # GDP per capita
            'FP.CPI.TOTL.ZG',  # Inflation
            'SL.UEM.TOTL.ZS',  # Unemployment
            'NE.EXP.GNFS.CD',  # Exports
            'NE.IMP.GNFS.CD'   # Imports
        ]
        
        economic_data = []
        for indicator_code in economic_indicators:
            data = self.db.get_latest_country_data(country_code, indicator_code)
            if data:
                economic_data.append(data)
        
        return economic_data
    
    def _get_population_data(self, country_code):
        """Lấy dữ liệu dân số"""
        population_indicators = [
            'SP.POP.TOTL',      # Total population
            'SP.POP.GROW',      # Population growth
            'SP.DYN.LE00.IN',   # Life expectancy
            'SP.DYN.CBRT.IN',   # Birth rate
            'SP.DYN.CDRT.IN'    # Death rate
        ]
        
        population_data = []
        for indicator_code in population_indicators:
            data = self.db.get_latest_country_data(country_code, indicator_code)
            if data:
                population_data.append(data)
        
        return population_data
    
    def _get_environment_data(self, country_code):
        """Lấy dữ liệu môi trường"""
        environment_indicators = [
            'EN.ATM.CO2E.PC',   # CO2 emissions per capita
            'AG.LND.FRST.ZS',   # Forest area
            'ER.H2O.FWTL.ZS',   # Renewable water resources
            'EG.USE.ELEC.KH.PC' # Electric power consumption
        ]
        
        environment_data = []
        for indicator_code in environment_indicators:
            data = self.db.get_latest_country_data(country_code, indicator_code)
            if data:
                environment_data.append(data)
        
        return environment_data
    
    def _get_social_data(self, country_code):
        """Lấy dữ liệu xã hội"""
        social_indicators = [
            'SE.XPD.TOTL.GD.ZS', # Education expenditure
            'SH.XPD.CHEX.GD.ZS', # Health expenditure
            'SE.ADT.LITR.ZS',    # Literacy rate
            'SH.STA.MMRT',       # Maternal mortality
            'SH.DYN.MORT'        # Mortality rate
        ]
        
        social_data = []
        for indicator_code in social_indicators:
            data = self.db.get_latest_country_data(country_code, indicator_code)
            if data:
                social_data.append(data)
        
        return social_data
    
    def format_data_for_ai(self, country_summary):
        """Định dạng dữ liệu cho AI dễ xử lý"""
        if not country_summary:
            return "Khong co du lieu cho quoc gia nay"
        
        country_name = country_summary["country_info"]["name"]
        
        # Tạo chuỗi dữ liệu có cấu trúc
        data_context = f"DU LIEU THUC TE - {country_name.upper()}\n"
        data_context += "=" * 50 + "\n"
        
        # Thông tin quốc gia
        country_info = country_summary["country_info"]
        data_context += f"Ma quoc gia: {country_info['iso_code']} ({country_info['iso2_code']})\n"
        data_context += f"Khu vuc: {country_info.get('region', 'Khong co du lieu')}\n"
        data_context += f"Muc thu nhap: {country_info.get('income_level', 'Khong co du lieu')}\n"
        data_context += f"Toa do: {country_info.get('latitude', '')}, {country_info.get('longitude', '')}\n\n"
        
        # Thêm chỉ số kinh tế
        if country_summary["economic_indicators"]:
            data_context += "CHI SO KINH TE:\n"
            for indicator in country_summary["economic_indicators"]:
                data_context += f"- {indicator['indicator_name']}: {indicator['value']} {indicator.get('unit', '')} ({indicator['year']})\n"
        
        # Thêm chỉ số dân số
        if country_summary["population_indicators"]:
            data_context += "\nCHI SO DAN SO:\n"
            for indicator in country_summary["population_indicators"]:
                data_context += f"- {indicator['indicator_name']}: {indicator['value']} {indicator.get('unit', '')} ({indicator['year']})\n"
        
        # Thêm chỉ số môi trường
        if country_summary["environment_indicators"]:
            data_context += "\nCHI SO MOI TRUONG:\n"
            for indicator in country_summary["environment_indicators"]:
                data_context += f"- {indicator['indicator_name']}: {indicator['value']} {indicator.get('unit', '')} ({indicator['year']})\n"
        
        # Thêm chỉ số xã hội
        if country_summary["social_indicators"]:
            data_context += "\nCHI SO XA HOI:\n"
            for indicator in country_summary["social_indicators"]:
                data_context += f"- {indicator['indicator_name']}: {indicator['value']} {indicator.get('unit', '')} ({indicator['year']})\n"
        
        data_context += f"\nTong so chi so co san: {country_summary['total_indicators']}"
        data_context += f"\nPham vi nam du lieu: {min(country_summary['available_years'])} - {max(country_summary['available_years'])}"
        
        return data_context
    
    def check_country_availability(self, country_name):
        """Kiểm tra xem quốc gia có trong database không"""
        available_countries = self.db.get_all_countries()
        country_names = [country['name'].lower() for country in available_countries]
        return country_name.lower() in country_names
    
    def get_country_suggestions(self, partial_name):
        """Gợi ý tên quốc gia dựa trên input"""
        available_countries = self.db.get_all_countries()
        suggestions = [country for country in available_countries 
                      if partial_name.lower() in country['name'].lower()]
        return suggestions[:10]  # Giới hạn 10 kết quả
    
    def get_country_code_by_name(self, country_name):
        """Lấy mã quốc gia từ tên"""
        available_countries = self.db.get_all_countries()
        for country in available_countries:
            if country['name'].lower() == country_name.lower():
                return country['iso_code']
        return None
    
    def show_database_overview(self):
        """Hiển thị tổng quan database"""
        stats = self.db.get_database_stats()
        
        print("\n" + "="*60)
        print("TONG QUAN DATABASE")
        print("="*60)
        print(f"Tong so quoc gia: {stats['total_countries']}")
        print(f"Tong so chi so: {stats['total_indicators']}")
        print(f"Tong so ban ghi du lieu: {stats['total_data_records']}")
        
        if 'year_range' in stats:
            print(f"Pham vi nam: {stats['year_range']['min']} - {stats['year_range']['max']}")
        
        if 'categories' in stats:
            print(f"Phan loai chi so: {', '.join(stats['categories'])}")
        
        if 'regions' in stats:
            print(f"Khu vuc: {', '.join(stats['regions'])}")
        
        print("\nDanh sach quoc gia co san:")
        countries = self.db.get_all_countries()
        for i, country in enumerate(countries[:15], 1):
            print(f"  {i:2d}. {country['name']} ({country['iso_code']})")
        
        if len(countries) > 15:
            print(f"  ... va {len(countries) - 15} quoc gia khac")
        print("="*60)
    
    def get_comparison_data(self, country_codes, indicator_code, year=None):
        """Lấy dữ liệu so sánh nhiều quốc gia"""
        return self.db.get_multiple_countries_data(country_codes, indicator_code, year)
    
    def get_indicator_trend(self, country_code, indicator_code, years_back=10):
        """Lấy xu hướng của chỉ số qua các năm"""
        return self.db.get_indicator_trend(country_code, indicator_code, years_back)
    
    def get_top_countries(self, indicator_code, limit=10, year=None):
        """Lấy top countries theo chỉ số"""
        return self.db.get_top_countries_by_indicator(indicator_code, limit, year)
    
    def get_latest_map_data(self, indicator_code):
        """Lấy dữ liệu cho bản đồ"""
        return self.db.get_latest_data_all_countries(indicator_code)

# Singleton instance
data_processor = DataProcessor()