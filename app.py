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
    st.info("💡 Mẹo: Nhập 'Cafe 25k', 'Xăng 50k'...")
    
    if st.button("🗑️ Reset dữ liệu"):
        st.session_state.expenses = []
        st.rerun()

# --- KHỞI TẠO DỮ LIỆU ---
if "expenses" not in st.session_state:
    st.session_state.expenses = []

# --- HÀM TỰ ĐỘNG TÌM MODEL SỐNG (AUTO-SWITCH) ---
def generate_with_fallback(prompt):
    # Danh sách các tên model có thể dùng được
    candidate_models = [
        'gemini-1.5-flash',
        'gemini-1.5-pro',
        'gemini-1.0-pro',
        'gemini-pro',
        'models/gemini-1.5-flash-latest'
    ]
    
    last_error = ""
    
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text # Nếu chạy được thì trả về luôn
        except Exception as e:
            # Nếu lỗi thì thử cái tiếp theo
            last_error = str(e)
            continue
            
    # Nếu thử hết mà vẫn lỗi thì đầu hàng
    raise Exception(f"Đã thử tất cả model nhưng đều thất bại. Lỗi cuối cùng: {last_error}")

# --- HÀM XỬ LÝ CHÍNH ---
def parse_expense_with_ai(text_input):
    if not api_key:
        return None, None, "Chưa nhập API Key!"
    
    try:
        genai.configure(api_key=api_key)
        
        prompt = f"""
        Nhiệm vụ: Phân tích chi tiêu.
        Input: "{text_input}"
        Output format: DANH_MỤC|SỐ_TIỀN_SỐ|GHI_CHÚ
        Danh mục: Ăn uống, Di chuyển, Mua sắm, Giải trí, Hóa đơn, Khác.
        Số tiền: Số nguyên (VD: 30k -> 30000).
        
        Ví dụ: "Ăn sáng 30k" -> Ăn uống|30000|Ăn sáng
        """
        
        # Gọi hàm "vạn năng" ở trên
        content = generate_with_fallback(prompt).strip()
        
        if "|" not in content:
             return None, None, f"AI trả về sai định dạng: {content}"

        category, amount, note = content.split('|')
        return category.strip(), int(amount), note.strip()
        
    except Exception as e:
        return None, None, str(e)

# --- HÀM TƯ VẤN ---
def ask_financial_advisor():
    if not st.session_state.expenses:
        return "Ví trống!"
    
    df = pd.DataFrame(st.session_state.expenses)
    summary = df.groupby('category')['amount'].sum().to_string()
    prompt = f"Bạn là chuyên gia tài chính. Tổng hợp chi tiêu: {summary}. Hãy nhận xét gắt gao."
    
    try:
        genai.configure(api_key=api_key)
        return generate_with_fallback(prompt)
    except Exception as e:
        return f"Lỗi tư vấn: {str(e)}"

# --- GIAO DIỆN ---
st.title("💰 Sổ Thu Chi (Bản Tự Động Fix Lỗi)")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📝 Nhập chi tiêu")
    with st.form("expense_form", clear_on_submit=True):
        raw_text = st.text_input("Nhập khoản chi:")
        submitted = st.form_submit_button("Lưu")
        
        if submitted and raw_text:
            with st.spinner("AI đang tìm model phù hợp..."):
                cat, amt, error_msg = parse_expense_with_ai(raw_text)
                
                if cat:
                    st.session_state.expenses.append({
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "category": cat,
                        "amount": amt,
                        "note": error_msg
                    })
                    st.success(f"✅ Đã lưu: {error_msg} - {amt:,}đ")
                    st.rerun()
                else:
                    st.error(f"❌ Lỗi: {error_msg}")

if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)
    st.divider()
    
    m1, m2 = st.columns(2)
    with m1:
        st.metric("Tổng chi", f"{df['amount'].sum():,} đ")
        fig = px.pie(df, values='amount', names='category', hole=0.4)
        fig.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
    with m2:
        st.dataframe(df[['date', 'category', 'amount', 'note']], hide_index=True, height=300)

    if st.button("Phân tích ví"):
        st.info(ask_financial_advisor())
