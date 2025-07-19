import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# --- Cấu hình và Kết nối ---

# Tải biến môi trường
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

# Hàm để kết nối tới Supabase, cache lại để không phải kết nối nhiều lần
@st.cache_resource
def init_connection():
    """Khởi tạo kết nối tới Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Lỗi: Vui lòng cung cấp SUPABASE_URL và SUPABASE_KEY trong file .env")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- Các hàm xử lý dữ liệu ---

def get_pending_documents():
    """Lấy tất cả các tài liệu có trạng thái 'pending'."""
    try:
        response = supabase.table('documents').select('id, content, metadata').eq('metadata->>status', 'pending').execute()
        return response.data
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu: {e}")
        return []

def approve_document(doc_id):
    """Cập nhật trạng thái của tài liệu thành 'approved'."""
    try:
        # Lấy metadata hiện tại
        current_data = supabase.table('documents').select('metadata').eq('id', doc_id).single().execute().data
        if current_data:
            metadata = current_data['metadata']
            metadata['status'] = 'approved'
            # Cập nhật lại metadata
            supabase.table('documents').update({'metadata': metadata}).eq('id', doc_id).execute()
            st.success(f"Đã duyệt thành công ID: {doc_id}")
    except Exception as e:
        st.error(f"Lỗi khi duyệt: {e}")

def reject_document(doc_id):
    """Xóa một tài liệu khỏi cơ sở dữ liệu."""
    try:
        supabase.table('documents').delete().eq('id', doc_id).execute()
        st.success(f"Đã xóa thành công ID: {doc_id}")
    except Exception as e:
        st.error(f"Lỗi khi xóa: {e}")

# --- Giao diện trang Admin ---

st.set_page_config(page_title="Admin - Duyệt câu trả lời", layout="wide")
st.title("👨‍💼 Trang quản trị - Duyệt kiến thức mới")

# --- Logic Đăng nhập ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login_form():
    """Hiển thị form đăng nhập."""
    st.header("Đăng nhập")
    with st.form("login_form"):
        password = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập")
        if submitted:
            if password == ADMIN_PASSWORD:
                st.session_state['logged_in'] = True
                st.rerun() # Chạy lại trang để vào giao diện chính
            else:
                st.error("Mật khẩu không chính xác")

# --- Giao diện chính sau khi đăng nhập ---
def admin_dashboard():
    """Hiển thị giao diện quản trị sau khi đã đăng nhập."""
    st.header("Các câu trả lời đang chờ duyệt")
    
    pending_docs = get_pending_documents()

    if not pending_docs:
        st.info("Hiện không có câu trả lời nào đang chờ duyệt.")
        return

    for doc in pending_docs:
        doc_id = doc.get('id')
        content = doc.get('content', 'N/A')
        
        with st.expander(f"**ID:** `{doc_id}`"):
            st.text_area("Nội dung:", value=content, height=150, disabled=True, key=f"content_{doc_id}")
            
            col1, col2, _, _ = st.columns(4)
            with col1:
                if st.button("✅ Duyệt", key=f"approve_{doc_id}", use_container_width=True):
                    approve_document(doc_id)
                    st.rerun() # Tải lại trang để cập nhật danh sách
            with col2:
                if st.button("❌ Xóa", key=f"reject_{doc_id}", type="primary", use_container_width=True):
                    reject_document(doc_id)
                    st.rerun() # Tải lại trang để cập nhật danh sách

# --- Chạy ứng dụng ---
if not st.session_state['logged_in']:
    login_form()
else:
    admin_dashboard()
