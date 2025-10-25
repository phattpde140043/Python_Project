import sqlite3
from typing import List, Dict, Optional, Tuple, Any
import os

class DatabaseManager:
    def __init__(self, db_path: str = "worldbank.db"):
        # Nếu không có đường dẫn khác được cung cấp, sử dụng worldbank.db làm mặc định
        self.db_path = db_path
        self.conn = None
        self._init_connection()
    
    def _init_connection(self):
        """Khởi tạo kết nối database"""
        try:
            # Kiểm tra xem file database có tồn tại không
            if not os.path.exists(self.db_path):
                print(f"Canh bao: File database '{self.db_path}' khong ton tai. Se tao database moi khi co truy van.")
            
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Để trả về dict-like objects
            print(f"Da ket noi den database: {self.db_path}")
        except Exception as e:
            print(f"Loi ket noi database: {e}")
            raise
    
    def execute_query(self, sql: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Thực thi query và trả về kết quả dạng list of dict"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params or ())
            
            if sql.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                self.conn.commit()
                return []
                
        except Exception as e:
            print(f"Loi query: {e}")
            print(f"SQL: {sql}")
            return []
    
    def test_connection(self) -> bool:
        """Kiểm tra kết nối database"""
        try:
            result = self.execute_query("SELECT 1 as test;")
            return len(result) > 0
        except Exception:
            return False
    
    # ===== COUNTRIES =====
    def get_all_countries(self) -> List[Dict[str, Any]]:
        """Lấy danh sách tất cả quốc gia"""
        sql = """
        SELECT iso_code, iso2_code, name, region, income_level, latitude, longitude 
        FROM countries 
        ORDER BY name;
        """
        return self.execute_query(sql)
    
    def get_country_by_code(self, iso_code: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin quốc gia theo mã ISO3"""
        sql = """
        SELECT iso_code, iso2_code, name, region, income_level, latitude, longitude 
        FROM countries 
        WHERE iso_code = ?;
        """
        results = self.execute_query(sql, (iso_code,))
        return results[0] if results else None
    
    def get_country_by_iso2(self, iso2_code: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin quốc gia theo mã ISO2"""
        sql = """
        SELECT iso_code, iso2_code, name, region, income_level, latitude, longitude 
        FROM countries 
        WHERE iso2_code = ?;
        """
        results = self.execute_query(sql, (iso2_code,))
        return results[0] if results else None
    
    # ===== INDICATORS =====
    def get_all_indicators(self) -> List[Dict[str, Any]]:
        """Lấy danh sách tất cả chỉ số"""
        sql = """
        SELECT code, name, unit, description, category 
        FROM indicators 
        ORDER BY category, name;
        """
        return self.execute_query(sql)
    
    def get_indicator_by_code(self, indicator_code: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chỉ số theo mã"""
        sql = """
        SELECT code, name, unit, description, category 
        FROM indicators 
        WHERE code = ?;
        """
        results = self.execute_query(sql, (indicator_code,))
        return results[0] if results else None
    
    def get_indicators_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Lấy danh sách chỉ số theo category"""
        sql = """
        SELECT code, name, unit, description, category 
        FROM indicators 
        WHERE category = ? 
        ORDER BY name;
        """
        return self.execute_query(sql, (category,))
    
    # ===== COUNTRY DATA =====
    def get_country_data(self, country_code: str, indicator_code: str) -> List[Dict[str, Any]]:
        """Lấy dữ liệu theo quốc gia và chỉ số"""
        sql = """
        SELECT cd.country_code, cd.indicator_code, cd.year, cd.value, cd.last_updated,
               c.name as country_name, i.name as indicator_name, i.unit
        FROM country_data cd
        JOIN countries c ON cd.country_code = c.iso_code
        JOIN indicators i ON cd.indicator_code = i.code
        WHERE cd.country_code = ? AND cd.indicator_code = ?
        ORDER BY cd.year DESC;
        """
        return self.execute_query(sql, (country_code, indicator_code))
    
    def get_latest_country_data(self, country_code: str, indicator_code: str) -> Optional[Dict[str, Any]]:
        """Lấy dữ liệu mới nhất của một chỉ số cho quốc gia"""
        sql = """
        SELECT cd.country_code, cd.indicator_code, cd.year, cd.value, cd.last_updated,
               c.name as country_name, i.name as indicator_name, i.unit
        FROM country_data cd
        JOIN countries c ON cd.country_code = c.iso_code
        JOIN indicators i ON cd.indicator_code = i.code
        WHERE cd.country_code = ? AND cd.indicator_code = ?
        ORDER BY cd.year DESC 
        LIMIT 1;
        """
        results = self.execute_query(sql, (country_code, indicator_code))
        return results[0] if results else None
    
    def get_latest_data_all_countries(self, indicator_code: str) -> List[Dict[str, Any]]:
        """Lấy dữ liệu mới nhất cho tất cả quốc gia (cho bản đồ)"""
        sql = """
        WITH LatestData AS (
            SELECT 
                country_code,
                MAX(year) as latest_year
            FROM country_data 
            WHERE indicator_code = ? AND value IS NOT NULL
            GROUP BY country_code
        )
        SELECT 
            cd.country_code,
            cd.year,
            cd.value,
            c.name as country_name,
            c.region,
            c.income_level,
            c.latitude,
            c.longitude,
            i.unit
        FROM country_data cd
        JOIN LatestData ld ON cd.country_code = ld.country_code AND cd.year = ld.latest_year
        JOIN countries c ON cd.country_code = c.iso_code
        JOIN indicators i ON cd.indicator_code = i.code
        WHERE cd.indicator_code = ? AND cd.value IS NOT NULL
        ORDER BY cd.value DESC;
        """
        return self.execute_query(sql, (indicator_code, indicator_code))
    
    def get_top_countries_by_indicator(self, indicator_code: str, limit: int = 10, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Lấy top countries theo chỉ số"""
        if year:
            sql = """
            SELECT 
                cd.country_code,
                cd.year,
                cd.value,
                c.name as country_name,
                c.region,
                i.unit
            FROM country_data cd
            JOIN countries c ON cd.country_code = c.iso_code
            JOIN indicators i ON cd.indicator_code = i.code
            WHERE cd.indicator_code = ? AND cd.year = ? AND cd.value IS NOT NULL
            ORDER BY cd.value DESC
            LIMIT ?;
            """
            params = (indicator_code, year, limit)
        else:
            # Lấy năm mới nhất cho mỗi quốc gia
            sql = """
            WITH LatestData AS (
                SELECT 
                    country_code,
                    MAX(year) as latest_year
                FROM country_data 
                WHERE indicator_code = ? AND value IS NOT NULL
                GROUP BY country_code
            )
            SELECT 
                cd.country_code,
                cd.year,
                cd.value,
                c.name as country_name,
                c.region,
                i.unit
            FROM country_data cd
            JOIN LatestData ld ON cd.country_code = ld.country_code AND cd.year = ld.latest_year
            JOIN countries c ON cd.country_code = c.iso_code
            JOIN indicators i ON cd.indicator_code = i.code
            WHERE cd.indicator_code = ? AND cd.value IS NOT NULL
            ORDER BY cd.value DESC
            LIMIT ?;
            """
            params = (indicator_code, indicator_code, limit)
        
        return self.execute_query(sql, params)
    
    def get_indicator_trend(self, country_code: str, indicator_code: str, years_back: int = 10) -> List[Dict[str, Any]]:
        """Lấy xu hướng của chỉ số qua các năm"""
        sql = """
        SELECT 
            cd.year, 
            cd.value,
            i.unit
        FROM country_data cd
        JOIN indicators i ON cd.indicator_code = i.code
        WHERE cd.country_code = ? AND cd.indicator_code = ?
        ORDER BY cd.year DESC
        LIMIT ?;
        """
        return self.execute_query(sql, (country_code, indicator_code, years_back))
    
    def get_multiple_countries_data(self, country_codes: List[str], indicator_code: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """Lấy dữ liệu so sánh nhiều quốc gia"""
        placeholders = ','.join(['?' for _ in country_codes])
        
        if year:
            sql = f"""
            SELECT 
                cd.country_code,
                cd.year,
                cd.value,
                c.name as country_name,
                c.region,
                i.unit
            FROM country_data cd
            JOIN countries c ON cd.country_code = c.iso_code
            JOIN indicators i ON cd.indicator_code = i.code
            WHERE cd.country_code IN ({placeholders}) 
            AND cd.indicator_code = ? 
            AND cd.year = ?
            AND cd.value IS NOT NULL
            ORDER BY cd.value DESC;
            """
            params = tuple(country_codes) + (indicator_code, year)
        else:
            # Lấy năm mới nhất cho mỗi quốc gia
            sql = f"""
            WITH LatestData AS (
                SELECT 
                    country_code,
                    MAX(year) as latest_year
                FROM country_data 
                WHERE country_code IN ({placeholders}) 
                AND indicator_code = ? 
                AND value IS NOT NULL
                GROUP BY country_code
            )
            SELECT 
                cd.country_code,
                cd.year,
                cd.value,
                c.name as country_name,
                c.region,
                i.unit
            FROM country_data cd
            JOIN LatestData ld ON cd.country_code = ld.country_code AND cd.year = ld.latest_year
            JOIN countries c ON cd.country_code = c.iso_code
            JOIN indicators i ON cd.indicator_code = i.code
            WHERE cd.indicator_code = ?
            ORDER BY cd.value DESC;
            """
            params = tuple(country_codes) + (indicator_code, indicator_code)
        
        return self.execute_query(sql, params)
    
    # ===== DATABASE METADATA =====
    def get_database_stats(self) -> Dict[str, Any]:
        """Lấy thống kê tổng quan về database"""
        stats = {}
        
        # Số lượng quốc gia
        result = self.execute_query("SELECT COUNT(*) as count FROM countries;")
        stats['total_countries'] = result[0]['count'] if result else 0
        
        # Số lượng chỉ số
        result = self.execute_query("SELECT COUNT(*) as count FROM indicators;")
        stats['total_indicators'] = result[0]['count'] if result else 0
        
        # Số lượng bản ghi dữ liệu
        result = self.execute_query("SELECT COUNT(*) as count FROM country_data;")
        stats['total_data_records'] = result[0]['count'] if result else 0
        
        # Năm có dữ liệu
        result = self.execute_query("SELECT MIN(year) as min_year, MAX(year) as max_year FROM country_data;")
        if result and result[0]:
            stats['year_range'] = {
                'min': result[0]['min_year'],
                'max': result[0]['max_year']
            }
        
        # Categories có sẵn
        result = self.execute_query("SELECT DISTINCT category FROM indicators WHERE category IS NOT NULL;")
        stats['categories'] = [row['category'] for row in result] if result else []
        
        # Regions có sẵn
        result = self.execute_query("SELECT DISTINCT region FROM countries WHERE region IS NOT NULL;")
        stats['regions'] = [row['region'] for row in result] if result else []
        
        return stats
    
    def get_available_years(self, indicator_code: Optional[str] = None) -> List[int]:
        """Lấy danh sách năm có dữ liệu"""
        if indicator_code:
            sql = "SELECT DISTINCT year FROM country_data WHERE indicator_code = ? ORDER BY year DESC;"
            results = self.execute_query(sql, (indicator_code,))
        else:
            sql = "SELECT DISTINCT year FROM country_data ORDER BY year DESC;"
            results = self.execute_query(sql)
        
        return [row['year'] for row in results] if results else []
    
    def close_connection(self):
        """Đóng kết nối database"""
        if self.conn:
            self.conn.close()
            print("Đã đóng kết nối database")

# Factory function với database mặc định là worldbank.db
def create_database_manager(db_path: str = "worldbank.db"):
    return DatabaseManager(db_path)

# Tạo instance mặc định để sử dụng trực tiếp
db_manager = create_database_manager()