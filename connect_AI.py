import google.generativeai as genai
import os
genai.configure(api_key="AIzaSyAm0K7ewFxMdOjFrJWgv6uuzHgB8UhEDzs")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
def list_available_models():
    try:
        models = genai.list_models()
        print("Các model có sẵn:")
        for model in models:
            print(f"- {model.name}")
            if hasattr(model, 'supported_generation_methods'):
                print(f"  Methods: {model.supported_generation_methods}")
        return [model.name for model in models]
    except Exception as e:
        print(f"Lỗi khi liệt kê model: {e}")
        return []
    
def get_country_info(country_name):
    model_names = [
        "models/gemini-2.5-flash",  # Model nhanh và hiệu quả
        "models/gemini-2.5-pro",    # Model mạnh hơn
        "models/gemini-flash-latest", # Model flash mới nhất
        "models/gemini-pro-latest",   # Model pro mới nhất
        "models/gemini-2.0-flash",    # Model flash ổn định
    ]
    
    for model_name in model_names:
        try:
            print(f"Đang thử model: {model_name}")
            model = genai.GenerativeModel(model_name)
            
            prompt = f"""
Hãy giới thiệu quốc gia {country_name} với các thông tin sau:
- Vị trí địa lý
- Diện tích
- Dân số và mật độ dân số  
- Thủ đô và ngôn ngữ chính
- Các đặc điểm nổi bật về văn hóa, kinh tế, du lịch

Hãy trình bày thông tin rõ ràng, có cấu trúc.Nhưng thời gian tìm hiểu trong vòng không quá 10s và thông tin là tiếng việt
"""
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Lỗi với {model_name}: {str(e)[:100]}...")
            continue
    
    return "Không thể tìm thấy model phù hợp"
