import streamlit as st
from dotenv import load_dotenv
from src.chatbot import Chatbot
from src.language_utils import detect_language, translate_text
from openai import OpenAI

# Tải biến môi trường
load_dotenv()

# Khởi tạo OpenAI client một lần để tái sử dụng
client = OpenAI()

# Thiết lập tiêu đề và icon cho trang
st.set_page_config(page_title="ISTQB Chatbot", page_icon="🤖")

# Cache resource để không phải tải lại model mỗi lần tương tác
@st.cache_resource
def load_chatbot():
    """Tải chatbot và cache lại để dùng cho các lần sau."""
    return Chatbot()

# --- Helper Function ---
def display_grouped_sources(sources_list):
    """
    Hàm hỗ trợ để nhóm và hiển thị nguồn tham khảo một cách tối ưu.
    """
    if not sources_list:
        return

    st.write("---")
    # st.subheader("Nguồn tham khảo:")
    
    # Gom các trang theo từng tên file
    grouped_sources = {}
    for source in sources_list:
        source_name = source.get('source', 'N/A')
        page_number = source.get('page')
        
        if source_name not in grouped_sources:
            # Sử dụng set để tự động loại bỏ các trang trùng lặp
            grouped_sources[source_name] = set()
        
        if isinstance(page_number, int):
            grouped_sources[source_name].add(page_number + 1)

    # Hiển thị các nguồn đã được gom nhóm
    for name, pages in grouped_sources.items():
        # Trường hợp nguồn là OpenAI hoặc không có trang cụ thể
        if "OpenAI" in name or not pages:
            st.markdown(f"- **Nguồn**: `{name}`")
        # Trường hợp nguồn từ giáo trình
        else:
            # Sắp xếp các trang và nối chúng lại
            pages_str = ", ".join(map(str, sorted(list(pages))))
            st.markdown(f"- **Nguồn**: `{name}`, **Trang**: {pages_str}")


# --- Main App ---
# Tải chatbot
bot = load_chatbot()

st.title("🤖 ISTQB Chatbot")
st.caption("Trợ lý AI giúp bạn truy xuất thông tin từ giáo trình ISTQB")

# Khởi tạo lịch sử chat nếu chưa có
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Xin chào! Bạn có câu hỏi nào về ISTQB không?"}
    ]

# Hiển thị các tin nhắn đã có trong lịch sử
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        # Hiển thị nguồn của các tin nhắn cũ nếu có
        if message["role"] == "assistant":
            display_grouped_sources(message.get("sources", []))

# Xử lý input mới từ người dùng
if prompt := st.chat_input("Hãy nhập câu hỏi của bạn..."):
    # Thêm tin nhắn của người dùng vào lịch sử và hiển thị ngay
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Xử lý và hiển thị câu trả lời của bot
    with st.chat_message("assistant"):
        with st.spinner("Đang suy nghĩ..."):
            # Phát hiện ngôn ngữ và dịch nếu cần
            original_lang = detect_language(prompt)
            english_prompt = prompt
            if original_lang == 'vi':
                english_prompt = translate_text(prompt, "English", client)

            # Lấy kết quả từ bot
            result = bot.answer(english_prompt)
            english_answer = result.get('answer', "Xin lỗi, đã có lỗi xảy ra.")
            sources = result.get('sources', [])

            # Dịch ngược câu trả lời về tiếng Việt nếu cần
            final_answer = english_answer
            if original_lang == 'vi':
                final_answer = translate_text(english_answer, "Vietnamese", client)
            
            # Hiển thị câu trả lời
            st.write(final_answer)
            
            # Hiển thị nguồn tham khảo đã được gom nhóm
            display_grouped_sources(sources)
            
            # Chuẩn bị và lưu tin nhắn hoàn chỉnh vào lịch sử
            assistant_message = {"role": "assistant", "content": final_answer}
            if sources:
                assistant_message["sources"] = sources
            st.session_state.messages.append(assistant_message)
