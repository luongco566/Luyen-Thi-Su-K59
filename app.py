import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import datetime

# --- CẤU HÌNH TRANG (Chuẩn Flagship) ---
st.set_page_config(page_title="Quản Lý Chi Tiêu AI", page_icon="💰", layout="wide")

# --- SIDEBAR: CẤU HÌNH ---
with st.sidebar:
    st.title("⚙️ Cấu hình ví tiền")
    api_key = st.text_input("Nhập Google API Key", type="password")
    st.info("💡 Mẹo: Nhập liệu tự nhiên, ví dụ: 'Cafe sáng 25k', AI sẽ tự lo phần còn lại.")
    
    # Nút reset dữ liệu
    if st.button("🗑️ Xóa hết dữ liệu (Reset)"):
        st.session_state.expenses = []
        st.rerun()

# --- KHỞI TẠO DỮ LIỆU (Session State) ---
if "expenses" not in st.session_state:
    st.session_state.expenses = []

# --- HÀM AI XỬ LÝ (TRÁI TIM CỦA APP) ---
def parse_expense_with_ai(text_input):
    if not api_key:
        return None, None, "Thiếu API Key"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash') # Dùng Flash cho nhanh
        
        # Prompt dạy AI cách hiểu tiếng Việt và tiền tệ
        prompt = f"""
        Nhiệm vụ: Phân tích câu nhập liệu chi tiêu thành dữ liệu có cấu trúc.
        Input: "{text_input}"
        
        Yêu cầu Output: Chỉ trả về 1 dòng duy nhất theo định dạng: DANH_MỤC|SỐ_TIỀN_SỐ|GHI_CHÚ
        - Danh mục chọn 1 trong: Ăn uống, Di chuyển, Mua sắm, Giải trí, Hóa đơn, Khác.
        - Số tiền: Chuyển về số nguyên (VD: 30k -> 30000).
        - Ghi chú: Giữ lại nội dung chính.
        
        Ví dụ: "Ăn phở 40k" -> Ăn uống|40000|Ăn phở
        Ví dụ: "Đổ xăng 50 ngàn" -> Di chuyển|50000|Đổ xăng
        """
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Tách dữ liệu
        category, amount, note = content.split('|')
        return category, int(amount), note
    except Exception as e:
        return None, None, str(e)

# --- HÀM TƯ VẤN TÀI CHÍNH ---
def ask_financial_advisor():
    if not st.session_state.expenses:
        return "Bạn chưa tiêu gì cả, ví còn nguyên!"
    
    df = pd.DataFrame(st.session_state.expenses)
    total = df['amount'].sum()
    summary = df.groupby('category')['amount'].sum().to_string()
    
    prompt = f"""
    Bạn là chuyên gia tài chính cá nhân gắt gao.
    Tổng chi tiêu: {total} VNĐ.
    Chi tiết:
    {summary}
    
    Hãy nhận xét ngắn gọn về cách tiêu tiền này. Cảnh báo nếu tiêu quá nhiều vào trà sữa hay game.
    """
    model = genai.GenerativeModel('gemini-pro')
    return model.generate_content(prompt).text

# --- GIAO DIỆN CHÍNH ---
st.title("💰 Sổ Thu Chi Thông Minh (AI Powered)")

# KHU VỰC 1: NHẬP LIỆU NHANH
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Nhập khoản chi mới")
    with st.form("expense_form", clear_on_submit=True):
        raw_text = st.text_input("Gõ tự nhiên (VD: Mua thẻ game 100k):")
        submitted = st.form_submit_button("Lưu khoản chi")
        
        if submitted and raw_text:
            with st.spinner("AI đang phân tích..."):
                cat, amt, note = parse_expense_with_ai(raw_text)
                if cat:
                    new_expense = {
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "category": cat,
                        "amount": amt,
                        "note": note
                    }
                    st.session_state.expenses.append(new_expense)
                    st.success(f"✅ Đã thêm: {note} - {amt:,} đ ({cat})")
                else:
                    st.error("Lỗi AI hoặc nhập liệu chưa rõ. Hãy thử lại!")

# KHU VỰC 2: HIỂN THỊ DỮ LIỆU
if st.session_state.expenses:
    # Tạo DataFrame để xử lý dữ liệu
    df = pd.DataFrame(st.session_state.expenses)
    
    st.divider()
    
    # Dashboard hoành tráng
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng chi tiêu", f"{df['amount'].sum():,} đ")
    m1.metric("Số giao dịch", len(df))
    
    # Biểu đồ tròn (Spectrogram tài chính :D)
    with m2:
        fig_pie = px.pie(df, values='amount', names='category', title='Cơ cấu chi tiêu', hole=0.4)
        fig_pie.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)
        
    # Lịch sử chi tiết
    with m3:
        st.dataframe(df[['date', 'category', 'amount', 'note']], hide_index=True, height=250)

    # KHU VỰC 3: AI TƯ VẤN
    st.divider()
    st.subheader("🕵️ Ý kiến chuyên gia (AI)")
    if st.button("Phân tích ví tiền của tôi"):
        with st.spinner("Đang soi ví..."):
            advice = ask_financial_advisor()
            st.info(advice)

else:
    st.info("Chưa có dữ liệu. Hãy nhập khoản chi đầu tiên đi bạn tôi!")
