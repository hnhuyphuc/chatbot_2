from langdetect import detect, LangDetectException

def detect_language(text):
    """Phát hiện ngôn ngữ của một đoạn văn bản."""
    try:
        # Trả về mã ngôn ngữ (ví dụ: 'en', 'vi')
        return detect(text)
    except LangDetectException:
        # Mặc định là tiếng Anh nếu không phát hiện được
        return 'en'

def translate_text(text, target_language, client):
    """Dịch văn bản sang ngôn ngữ đích bằng OpenAI API."""
    prompt = f"Translate the following text to {target_language}: '{text}'"
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Lỗi trong quá trình dịch: {e}")
        return text # Trả về văn bản gốc nếu có lỗi