import streamlit as st
import google.generativeai as genai

# --- CẤU HÌNH ---
st.set_page_config(page_title="AI Sư Phạm Sử", layout="wide")

# --- SIDEBAR: NHẬP API KEY & TÀI LIỆU ---
with st.sidebar:
    st.title("Cấu hình phòng thi")
    api_key = st.text_input("Nhập Google API Key", type="password")
    
    # Khu vực nạp kiến thức (Context)
    st.subheader("Nạp kiến thức (Giáo trình/Tài liệu)")
    uploaded_file = st.file_uploader("Chọn file TXT", type=['txt'])
    
    context = ""
    if uploaded_file is not None:
        context = uploaded_file.read().decode("utf-8")
        st.success(f"Đã học xong tài liệu: {uploaded_file.name}")
    else:
        st.info("Chưa có tài liệu. AI sẽ dùng kiến thức phổ thông.")

# --- HÀM XỬ LÝ AI ---
def ask_gemini(prompt):
    if not api_key:
        return "⚠️ Hãy nhập API Key ở cột bên trái trước!"
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Lỗi kết nối: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.title("📝 Luyện Thi Vấn Đáp & Tự Luận - Sử K59")

tab1, tab2 = st.tabs(["Luyện Tự Luận (Essay)", "Luyện Vấn Đáp (Chat)"])

# TAB 1: TỰ LUẬN
with tab1:
    st.markdown("### Đề bài: Phân tích sự kiện/giai đoạn lịch sử")
    question = st.text_input("Nhập câu hỏi ôn tập của bạn:")
    student_answer = st.text_area("Bài làm của bạn:", height=250)
    
    if st.button("Chấm điểm ngay"):
        if not question or not student_answer:
            st.warning("Vui lòng nhập đủ câu hỏi và câu trả lời.")
        else:
            with st.spinner("Giáo sư AI đang chấm bài..."):
                # Prompt kỹ thuật cao: Yêu cầu AI chấm dựa trên Context đã upload
                prompt_grading = f"""
                Bạn là Giáo sư Lịch sử. Hãy chấm bài dựa trên tài liệu sau (nếu có):
                ---
                TÀI LIỆU GỐC: {context}
                ---
                Câu hỏi: {question}
                Bài làm sinh viên: {student_answer}
                
                Yêu cầu output:
                1. Điểm số (Thang 10).
                2. Nhận xét chi tiết: Đúng ý nào, thiếu ý nào so với Tài liệu gốc.
                3. Sửa lại bài văn cho hay hơn, văn phong học thuật.
                """
                result = ask_gemini(prompt_grading)
                st.markdown(result)

# TAB 2: VẤN ĐÁP
with tab2:
    st.markdown("### Phòng thi vấn đáp trực tiếp")
    
    if "history" not in st.session_state:
        st.session_state.history = []

    # Hiển thị chat
    for msg in st.session_state.history:
        role = "Bạn" if msg['role'] == 'user' else "Giáo sư"
        st.chat_message(msg['role']).write(msg['content'])

    # Nhập câu trả lời
    user_input = st.chat_input("Trả lời hoặc hỏi lại giáo sư...")
    
    if user_input:
        # Hiện câu của user
        st.session_state.history.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)
        
        with st.spinner("..."):
            # Prompt đóng vai
            prompt_chat = f"""
            Tài liệu gốc: {context}
            Lịch sử chat: {st.session_state.history}
            User vừa nói: {user_input}
            
            Hãy đóng vai giáo sư khó tính. Nếu sinh viên trả lời sai hoặc thiếu, hãy hỏi vặn lại (drill down). 
            Nếu trả lời tốt, hãy chuyển sang chủ đề khác liên quan.
            """
            reply = ask_gemini(prompt_chat)
            
            st.session_state.history.append({"role": "assistant", "content": reply})
            st.chat_message("assistant").write(reply)