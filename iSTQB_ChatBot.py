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
    
    grouped_sources = {}
    for source in sources_list:
        source_name = source.get('source', 'N/A')
        page_number = source.get('page')
        
        if source_name not in grouped_sources:
            grouped_sources[source_name] = set()
        
        if isinstance(page_number, int):
            grouped_sources[source_name].add(page_number + 1)

    for name, pages in grouped_sources.items():
        if "OpenAI" in name or not pages:
            st.markdown(f"**Nguồn**: `{name}`")
        else:
            pages_str = ", ".join(map(str, sorted(list(pages))))
            st.markdown(f"**Nguồn**: `{name}` - **Trang**: {pages_str}")

# --- Main App ---
bot = load_chatbot()

st.title("🤖 ISTQB Chatbot")
st.caption("Trợ lý AI giúp bạn truy xuất thông tin từ giáo trình ISTQB")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Xin chào! Bạn có câu hỏi nào về ISTQB không?"}
    ]

# Hiển thị các tin nhắn đã có trong lịch sử
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message["role"] == "assistant":
            display_grouped_sources(message.get("sources", []))

# Xử lý input mới từ người dùng
if prompt := st.chat_input("Hãy nhập câu hỏi của bạn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        # Dịch prompt sang tiếng Anh
        original_lang = detect_language(prompt)
        english_prompt = prompt
        if original_lang == 'vi':
            english_prompt = translate_text(prompt, "English", client)

        # --- LOGIC MỚI: TƯƠNG TÁC THEO TỪNG BƯỚC ---
        final_result = None
        
        # 1. Tìm trong giáo trình trước
        with st.spinner("Đang tìm trong giáo trình..."):
            syllabus_result = bot.search_in_syllabus(english_prompt)

        if syllabus_result:
            # Nếu tìm thấy, đây là kết quả cuối cùng
            final_result = syllabus_result
        else:
            # 2. Nếu không tìm thấy, thông báo và tìm bằng OpenAI
            placeholder = st.empty()
            placeholder.write("Giáo trình chưa có thông tin này. Xin hãy đợi tôi hỏi OpenAI...")
            
            with st.spinner("Đang liên hệ với OpenAI..."):
                openai_result = bot.search_with_openai_and_learn(english_prompt)
            
            final_result = openai_result
            placeholder.empty() # Xóa thông báo tạm thời

        # 3. Xử lý và hiển thị kết quả cuối cùng
        english_answer = final_result.get('answer', "Xin lỗi, đã có lỗi xảy ra.")
        sources = final_result.get('sources', [])

        # Dịch ngược câu trả lời nếu cần
        final_answer = english_answer
        if original_lang == 'vi' and english_answer:
            final_answer = translate_text(english_answer, "Vietnamese", client)
        
        st.write(final_answer)
        
        # Hiển thị nguồn tham khảo đã được gom nhóm
        display_grouped_sources(sources)
        
        # Lưu tin nhắn hoàn chỉnh vào lịch sử
        assistant_message = {"role": "assistant", "content": final_answer}
        if sources:
            assistant_message["sources"] = sources
        st.session_state.messages.append(assistant_message)
