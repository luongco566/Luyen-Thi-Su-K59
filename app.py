import streamlit as st
import google.generativeai as genai
import os

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(
    page_title="AI Luyện Thi Sử K59",
    page_icon="🎓",
    layout="wide"
)

# --- CSS TÙY CHỈNH CHO ĐẸP ---
st.markdown("""
<style>
    .stTextArea textarea {font-size: 16px !important;}
    .stChatMessage {border: 1px solid #e0e0e0; border-radius: 10px; padding: 10px; margin-bottom: 10px;}
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CÀI ĐẶT ---
with st.sidebar:
    st.title("⚙️ Cấu hình phòng thi")
    
    # Nhập API Key
    api_key = st.text_input("Nhập Google API Key mới", type="password", help="Key cũ bị lộ rồi, hãy tạo key mới nhé!")
    
    st.divider()
    
    # Nạp tài liệu ôn thi
    st.subheader("📚 Tài liệu ôn tập")
    uploaded_file = st.file_uploader("Upload giáo trình (File TXT)", type=['txt'])
    
    context_text = ""
    if uploaded_file is not None:
        context_text = uploaded_file.read().decode("utf-8")
        st.success(f"Đã nạp: {uploaded_file.name}")
        with st.expander("Xem nội dung tài liệu"):
            st.text(context_text[:500] + "...")
    else:
        st.info("Chưa có tài liệu. AI sẽ dùng kiến thức Lịch Sử phổ thông.")

    st.divider()
    difficulty = st.selectbox("Chọn độ khó:", ["Dễ (Ôn bài)", "Trung bình", "Khó (Thi thật)"])

# --- HÀM XỬ LÝ AI (CÓ BẮT LỖI) ---
def get_gemini_response(prompt_text):
    if not api_key:
        return "⚠️ Vui lòng nhập API Key ở cột bên trái để bắt đầu."
    
    try:
        genai.configure(api_key=api_key)
        # Sử dụng model Flash (Nhanh và đọc được nhiều tài liệu)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        # Nếu lỗi 404, thử fallback về model cũ hơn
        if "404" in str(e):
            return "⚠️ Lỗi phiên bản: Bạn cần cập nhật file requirements.txt trên GitHub thành 'google-generativeai>=0.7.2' để dùng model mới nhất."
        return f"Lỗi kết nối: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.title("🎓 Ứng Dụng Luyện Thi Sử K59")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 Luyện Tự Luận", "🗣️ Luyện Vấn Đáp"])

# === TAB 1: TỰ LUẬN ===
with tab1:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Đề bài")
        user_question = st.text_input("Nhập câu hỏi hoặc chủ đề cần phân tích:", placeholder="Ví dụ: Phân tích ý nghĩa Hội nghị thành lập Đảng...")
        st.subheader("Bài làm của bạn")
        user_answer = st.text_area("Viết câu trả lời tại đây:", height=300, placeholder="Bắt đầu viết...")
        
        btn_grade = st.button("🖊️ Chấm điểm ngay", type="primary")

    with col2:
        st.subheader("Kết quả chấm thi")
        if btn_grade:
            if not user_answer:
                st.warning("Hãy viết bài làm trước khi chấm!")
            else:
                with st.spinner("Giáo sư đang đọc bài kỹ lưỡng..."):
                    prompt = f"""
                    Vai trò: Giảng viên Lịch sử trường ĐH Sư phạm (Độ khó: {difficulty}).
                    Tài liệu tham khảo bắt buộc: {context_text}
                    
                    Yêu cầu chấm thi:
                    1. Đánh giá bài làm sinh viên dựa trên câu hỏi: "{user_question}".
                    2. Chấm điểm thang 10.
                    3. Liệt kê các TỪ KHÓA (Keywords) lịch sử quan trọng mà sinh viên còn thiếu.
                    4. Nhận xét ưu điểm/nhược điểm tư duy.
                    5. Viết lại một đoạn văn mẫu chuẩn học thuật dựa trên ý của sinh viên.
                    
                    Bài làm của sinh viên:
                    {user_answer}
                    """
                    result = get_gemini_response(prompt)
                    st.markdown(result)

# === TAB 2: VẤN ĐÁP ===
with tab2:
    st.subheader("Phòng thi Vấn đáp (Oral Exam)")
    
    # Quản lý lịch sử chat
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Chào em, mời em giới thiệu về chủ đề muốn thi vấn đáp hôm nay?"}
        ]

    # Hiển thị hội thoại cũ
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Ô nhập liệu chat
    if prompt := st.chat_input("Nhập câu trả lời của bạn..."):
        # Hiển thị câu user
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Xử lý AI trả lời
        with st.chat_message("assistant"):
            with st.spinner("Giáo sư đang suy nghĩ..."):
                chat_prompt = f"""
                Bạn là giáo sư Sử học đang thi vấn đáp sinh viên.
                Tài liệu giáo trình: {context_text}
                Lịch sử hội thoại: {st.session_state.messages}
                Câu trả lời mới nhất của sinh viên: "{prompt}"
                
                Nhiệm vụ:
                - Nếu sinh viên trả lời sai/thiếu: Hãy hỏi vặn lại (drill down) vào chi tiết đó.
                - Nếu trả lời tốt: Khen ngợi ngắn gọn và chuyển sang câu hỏi khác liên quan logic.
                - Giữ thái độ: {difficulty}.
                """
                response = get_gemini_response(chat_prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
