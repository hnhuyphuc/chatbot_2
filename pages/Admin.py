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
    # Khởi tạo kết nối tới Supabase
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Lỗi: Vui lòng cung cấp SUPABASE_URL và SUPABASE_KEY trong file .env")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

# --- Các hàm xử lý dữ liệu ---
def get_pending_documents():
    """Lấy tất cả các tài liệu có trạng thái 'pending'."""
    try:
        response = supabase.table('documents').select('id, content, metadata').eq('metadata->>status', 'pending').order('id').execute()
        return response.data
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu: {e}")
        return []

def approve_document(doc_id):
    # Cập nhật trạng thái của tài liệu thành 'approved'
    try:
        current_data = supabase.table('documents').select('metadata').eq('id', doc_id).single().execute().data
        if current_data:
            metadata = current_data['metadata']
            metadata['status'] = 'approved'
            supabase.table('documents').update({'metadata': metadata}).eq('id', doc_id).execute()
    except Exception as e:
        st.error(f"Lỗi khi duyệt: {e}")

def reject_document(doc_id):
    # Xóa một tài liệu khỏi cơ sở dữ liệu
    try:
        supabase.table('documents').delete().eq('id', doc_id).execute()
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
                st.rerun()
            else:
                st.error("Mật khẩu không chính xác")

# --- Giao diện chính sau khi đăng nhập ---
def admin_dashboard():
    # Hiển thị giao diện quản trị sau khi đã đăng nhập
    
    st.header("Các câu trả lời đang chờ duyệt")
    
    if 'admin_page_number' not in st.session_state:
        st.session_state.admin_page_number = 0

    pending_docs = get_pending_documents()

    if not pending_docs:
        st.info("Hiện không có câu trả lời nào đang chờ duyệt.")
        return

    # --- Logic Phân trang ---
    ITEMS_PER_PAGE = 5
    total_items = len(pending_docs)
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    if st.session_state.admin_page_number >= total_pages and total_pages > 0:
        st.session_state.admin_page_number = 0

    start_index = st.session_state.admin_page_number * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    paginated_docs = pending_docs[start_index:end_index]

    for doc in paginated_docs:
        doc_id = doc.get('id')
        content = doc.get('content', 'N/A')
        
        with st.container():
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"**ID:** `{doc_id}`")
            with col2:
                if st.button("✅ Duyệt", key=f"approve_{doc_id}", use_container_width=True):
                    st.session_state.confirm_action = {"type": "approve", "id": doc_id}
                    st.rerun()
            with col3:
                if st.button("❌ Xóa", key=f"reject_{doc_id}", use_container_width=True):
                    st.session_state.confirm_action = {"type": "reject", "id": doc_id}
                    st.rerun()

            st.text_area("Nội dung:", value=content, height=150, disabled=True, key=f"content_{doc_id}")
            st.divider()

    # --- Điều khiển Phân trang ---
    if total_pages > 1:
        st.write("")
        pag_col1, pag_col2, pag_col3 = st.columns([2, 3, 2])
        with pag_col1:
            if st.button("⬅️ Trang trước", use_container_width=True, disabled=(st.session_state.admin_page_number == 0)):
                st.session_state.admin_page_number -= 1
                st.rerun()
        with pag_col2:
            st.markdown(f"<div style='text-align: center; margin-top: 0.5rem;'>Trang {st.session_state.admin_page_number + 1} / {total_pages}</div>", unsafe_allow_html=True)
        with pag_col3:
            if st.button("Trang sau ➡️", use_container_width=True, disabled=(st.session_state.admin_page_number + 1 >= total_pages)):
                st.session_state.admin_page_number += 1
                st.rerun()

# --- Xử lý Dialog Xác nhận ---
if 'confirm_action' in st.session_state:
    action = st.session_state.confirm_action
    action_type = action['type']
    doc_id = action['id']

    if action_type == "approve":
        @st.dialog("Xác nhận duyệt")
        def approve_dialog():
            st.write(f"Bạn có chắc muốn **duyệt** kiến thức với ID: `{doc_id}` không?")
            col1, col2 = st.columns(2)
            if col1.button("✅ Có, duyệt ngay", use_container_width=True):
                approve_document(doc_id)
                st.toast(f"Đã duyệt thành công ID: {doc_id}", icon="✅")
                del st.session_state.confirm_action
                st.rerun()
            if col2.button("Hủy bỏ", use_container_width=True):
                del st.session_state.confirm_action
                st.rerun()
        approve_dialog()

    elif action_type == "reject":
        @st.dialog("⚠️ Xác nhận xóa")
        def reject_dialog():
            st.write(f"Bạn có chắc muốn **xóa** kiến thức với ID: `{doc_id}` không? Hành động này không thể hoàn tác.")
            col1, col2 = st.columns(2)
            if col1.button("❌ Có, xóa ngay", type="primary", use_container_width=True):
                reject_document(doc_id)
                st.toast(f"Đã xóa thành công ID: {doc_id}", icon="🗑️")
                del st.session_state.confirm_action
                st.rerun()
            if col2.button("Hủy bỏ", use_container_width=True):
                del st.session_state.confirm_action
                st.rerun()
        reject_dialog()

# --- Chạy ứng dụng ---
if not st.session_state['logged_in']:
    login_form()
else:
    admin_dashboard()
