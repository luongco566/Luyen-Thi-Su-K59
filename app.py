import streamlit as st
import google.generativeai as genai
from google.protobuf.json_format import MessageToDict
import pandas as pd
import plotly.express as px
import datetime
import os

# --- CẤU HÌNH TRANG (Giao diện rộng) ---
st.set_page_config(page_title="Ultra Money Manager", page_icon="💎", layout="wide")

# --- CSS TÙY CHỈNH (Cho giống App xịn) ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; border-radius: 10px; padding: 15px; text-align: center;}
    .stButton>button {width: 100%; border-radius: 20px;}
</style>
""", unsafe_allow_html=True)

# --- KHAI BÁO CÔNG CỤ (TOOL) ---
expense_tool = {
    'function_declarations': [
        {
            'name': 'log_transaction',
            'description': 'Ghi lại giao dịch tài chính.',
            'parameters': {
                'type': 'OBJECT',
                'properties': {
                    'category': {'type': 'STRING', 'description': 'Danh mục (Ăn uống, Di chuyển, Mua sắm, Hóa đơn, Giải trí, Lương, Thưởng, Đầu tư, Khác)'},
                    'amount': {'type': 'INTEGER', 'description': 'Số tiền VND (VD: 50k là 50000)'},
                    'note': {'type': 'STRING', 'description': 'Nội dung chi tiết'},
                    'type': {'type': 'STRING', 'enum': ['Chi', 'Thu'], 'description': 'Xác định là khoản Chi hay Thu'}
                },
                'required': ['category', 'amount', 'type']
            }
        }
    ]
}

# --- QUẢN LÝ DỮ LIỆU (CSV) ---
CSV_FILE = 'so_chi_tieu.csv'

def load_data():
    if os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame(columns=['date', 'category', 'amount', 'note', 'type'])

def save_data(df):
    df.to_csv(CSV_FILE, index=False)

# --- SIDEBAR: CẤU HÌNH ---
with st.sidebar:
    st.header("🎛️ Trung tâm điều khiển")
    api_key = st.text_input("🔑 Google API Key", type="password")
    
    # List model theo yêu cầu của bác (Có cả bản 2.0 mới nhất)
    model_option = st.selectbox(
        "🧠 Chọn Brain (Model):",
        ["gemini-2.5-flash-exp", "gemini-2.5-pro", "gemini-2.5-pro", "gemini-2.0-pro"],
        index=0
    )
    
    st.divider()
    st.subheader("💾 Quản lý dữ liệu")
    
    # Nút tải dữ liệu về máy (Backup)
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "rb") as f:
            st.download_button("⬇️ Tải file Backup (.csv)", f, file_name="backup_chitieu.csv", mime="text/csv")
    
    # Nút upload dữ liệu cũ (Restore)
    uploaded_file = st.file_uploader("⬆️ Khôi phục dữ liệu cũ", type=['csv'])
    if uploaded_file is not None:
        try:
            df_new = pd.read_csv(uploaded_file)
            save_data(df_new)
            st.success("Đã khôi phục dữ liệu!")
            st.rerun()
        except:
            st.error("File lỗi rồi đại ca!")

# --- XỬ LÝ AI ---
def process_ai(text_input):
    if not api_key: return False, "Chưa nhập Key!"
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name=model_option, tools=[expense_tool])
        chat = model.start_chat(enable_automatic_function_calling=True)
        response = chat.send_message(text_input)
        
        # Bóc tách dữ liệu từ Function Call
        for part in response.candidates[0].content.parts:
            if part.function_call:
                fc = part.function_call
                return True, {
                    "category": fc.args.get("category", "Khác"),
                    "amount": int(fc.args.get("amount", 0)),
                    "note": fc.args.get("note", ""),
                    "type": fc.args.get("type", "Chi")
                }
        return False, "AI không nhận diện được giao dịch. Thử lại xem?"
    except Exception as e:
        return False, f"Lỗi Model {model_option}: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.title(f"💎 Quản Lý Tài Chính ({model_option})")

# 1. LOAD DỮ LIỆU
df = load_data()

# 2. KHU VỰC NHẬP LIỆU (Chat Style)
with st.container():
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        user_text = st.text_input("", placeholder="💬 VD: Mới nhận lương 20 củ, tối đi nhậu hết 500k...", label_visibility="collapsed")
    with col_btn:
        btn_send = st.button("Gửi 🚀", type="primary")

    if btn_send and user_text:
        with st.spinner("AI đang phân tích..."):
            success, result = process_ai(user_text)
            if success:
                new_row = {
                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    **result
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df) # Lưu ngay vào CSV
                st.toast(f"✅ Đã lưu: {result['note']}", icon="🎉")
                st.rerun()
            else:
                st.error(result)

st.divider()

# 3. DASHBOARD (HIỂN THỊ ĐẸP)
if not df.empty:
    # Tính toán chỉ số
    tong_thu = df[df['type'] == 'Thu']['amount'].sum()
    tong_chi = df[df['type'] == 'Chi']['amount'].sum()
    so_du = tong_thu - tong_chi
    
    # Hiển thị 3 số to đùng
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Tổng Thu", f"{tong_thu:,.0f} đ", delta="Thu nhập", delta_color="normal")
    c2.metric("💸 Tổng Chi", f"{tong_chi:,.0f} đ", delta="-Chi tiêu", delta_color="inverse")
    c3.metric("🏦 Số Dư", f"{so_du:,.0f} đ")
    
    st.markdown("---")
    
    # Hai cột biểu đồ
    chart1, chart2 = st.columns(2)
    
    with chart1:
        st.subheader("📊 Cơ cấu chi tiêu")
        if tong_chi > 0:
            df_chi = df[df['type'] == 'Chi']
            fig_pie = px.pie(df_chi, values='amount', names='category', hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Chưa tiêu gì cả!")

    with chart2:
        st.subheader("📈 Xu hướng dòng tiền")
        # Biểu đồ cột theo thời gian (Spectrogram tài chính :D)
        if not df.empty:
            fig_bar = px.bar(df, x='date', y='amount', color='type', barmode='group', 
                             color_discrete_map={'Chi': '#ff4b4b', 'Thu': '#00cc96'})
            st.plotly_chart(fig_bar, use_container_width=True)

    # Bảng dữ liệu chi tiết
    with st.expander("📜 Xem lịch sử giao dịch chi tiết", expanded=True):
        st.dataframe(df.sort_index(ascending=False), use_container_width=True, hide_index=True)

else:
    st.info("👋 Chào bạn! Hãy nhập giao dịch đầu tiên để kích hoạt Dashboard.")
