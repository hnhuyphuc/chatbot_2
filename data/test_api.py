import os
from openai import OpenAI
from dotenv import load_dotenv

def check_openai_api():
    """
    Kiểm tra kết nối và xác thực với OpenAI API.
    """
    print("Đang kiểm tra API key của OpenAI...")
    
    # 1. Tải API key từ file .env
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ LỖI: Không tìm thấy OPENAI_API_KEY trong file .env.")
        return

    # 2. Khởi tạo client
    try:
        client = OpenAI(api_key=api_key)
        
        # 3. Thực hiện một yêu cầu API đơn giản
        print("Đang gửi yêu cầu đến OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello world"}
            ]
        )
        
        # 4. In kết quả
        print("\n✅ THÀNH CÔNG! API key của bạn hợp lệ và hoạt động tốt.")
        print(f"   Phản hồi từ model: {response.choices[0].message.content}")

    except Exception as e:
        print("\n❌ LỖI: Không thể kết nối hoặc xác thực với OpenAI.")
        print("   Vui lòng kiểm tra lại API key trong file .env và kết nối mạng.")
        print(f"\n   Chi tiết lỗi:\n   {e}")

if __name__ == "__main__":
    check_openai_api()