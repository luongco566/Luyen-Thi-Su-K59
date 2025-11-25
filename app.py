import streamlit as st
import google.generativeai as genai
import pandas as pd
import plotly.express as px
import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Quản Lý Chi Tiêu AI", page_icon="💰", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Cấu hình ví tiền")
    api_key = st.text_input("Nhập Google API Key", type="password")
    st.info("💡 Mẹo: Nhập liệu tự nhiên, ví dụ: 'Cafe sáng 25k', AI sẽ tự lo phần còn lại.")
    
    if st.button("🗑️ Xóa hết dữ liệu (Reset)"):
        st.session_state.expenses = []
        st.rerun()

# --- KHỞI TẠO DỮ LIỆU ---
if "expenses" not in st.session_state:
    st.session_state.expenses = []

# --- HÀM AI XỬ LÝ (DÙNG GEMINI PRO CHO ỔN ĐỊNH) ---
def parse_expense_with_ai(text_input):
    if not api_key:
        return None, None, "Chưa nhập API Key kìa đại ca!"
    
    try:
        genai.configure(api_key=api_key)
        # SỬA LẠI THÀNH PRO ĐỂ KHÔNG BỊ LỖI 404
        model = genai.GenerativeModel('gemini-pro') 
        
        prompt = f"""
        Nhiệm vụ: Phân tích câu nhập liệu chi tiêu thành dữ liệu.
        Input: "{text_input}"
        
        Yêu cầu Output: 
        - TUYỆT ĐỐI KHÔNG dùng Markdown (không bôi đậm, không in nghiêng).
        - Trả về đúng định dạng: DANH_MỤC|SỐ_TIỀN_SỐ|GHI_CHÚ
        - Danh mục chọn trong: Ăn uống, Di chuyển, Mua sắm, Giải trí, Hóa đơn, Khác.
        - Số tiền: Chỉ lấy số (VD: 30k -> 30000).
        
        Ví dụ chuẩn:
        Ăn uống|40000|Ăn phở
        Di chuyển|50000|Đổ xăng
        """
        response = model.generate_content(prompt)
        content = response.text.strip()
        
        # Xử lý nếu AI lỡ thêm dòng trống hoặc ký tự lạ
        if "|" not in content:
             return None, None, f"Lỗi định dạng AI trả về: {content}"

        category, amount, note = content.split('|')
        return category.strip(), int(amount), note.strip()
        
    except Exception as e:
        # TRẢ VỀ LỖI CHI TIẾT ĐỂ DEBUG
        return None, None, str(e)

# --- HÀM TƯ VẤN ---
def ask_financial_advisor():
    if not st.session_state.expenses:
        return "Ví trống trơn, chưa có gì để tư vấn!"
    
    df = pd.DataFrame(st.session_state.expenses)
    total = df['amount'].sum()
    summary = df.groupby('category')['amount'].sum().to_string()
    
    prompt = f"Bạn là chuyên gia tài chính. Tổng chi: {total}đ. Chi tiết: {summary}. Hãy nhận xét ngắn gọn, gắt gao về cách tiêu tiền này."
    model = genai.GenerativeModel('gemini-pro')
    return model.generate_content(prompt).text

# --- GIAO DIỆN CHÍNH ---
st.title("💰 Sổ Thu Chi Thông Minh (Bản Fix Lỗi)")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Nhập khoản chi mới")
    with st.form("expense_form", clear_on_submit=True):
        raw_text = st.text_input("Gõ tự nhiên (VD: Mua thẻ game 100k):")
        submitted = st.form_submit_button("Lưu khoản chi")
        
        if submitted and raw_text:
            with st.spinner("Đang phân tích (Dùng Gemini Pro)..."):
                cat, amt, error_msg = parse_expense_with_ai(raw_text)
                
                if cat:
                    new_expense = {
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "category": cat,
                        "amount": amt,
                        "note": error_msg # Ở đây biến thứ 3 là note
                    }
                    st.session_state.expenses.append(new_expense)
                    st.success(f"✅ Đã thêm: {error_msg} - {amt:,} đ ({cat})")
                    st.rerun() # Tự động reload để hiện biểu đồ ngay
                else:
                    # HIỆN LỖI CỤ THỂ RA MÀN HÌNH
                    st.error(f"❌ Có lỗi xảy ra: {error_msg}")

if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)
    st.divider()
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng chi tiêu", f"{df['amount'].sum():,} đ")
    m1.metric("Số giao dịch", len(df))
    
    with m2:
        fig_pie = px.pie(df, values='amount', names='category', title='Cơ cấu chi tiêu', hole=0.4)
        fig_pie.update_layout(height=300, margin=dict(t=30, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with m3:
        st.dataframe(df[['date', 'category', 'amount', 'note']], hide_index=True, height=250)

    st.divider()
    if st.button("Phân tích ví tiền"):
        with st.spinner("Đang soi ví..."):
            st.info(ask_financial_advisor())
else:
    st.info("Chưa có dữ liệu.")
