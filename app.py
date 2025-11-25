import streamlit as st
import google.generativeai as genai
from google.protobuf.json_format import MessageToDict
import pandas as pd
import plotly.express as px
import datetime

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="Sổ Thu Chi (Function Calling)", page_icon="💳", layout="wide")

# --- 1. ĐỊNH NGHĨA CÔNG CỤ (THE TOOL) ---
# Đây là cái "khuôn" bạn dạy cho AI biết cách nhập liệu
expense_tool = {
    'function_declarations': [
        {
            'name': 'log_transaction',
            'description': 'Ghi lại một khoản chi tiêu hoặc thu nhập của người dùng vào sổ cái.',
            'parameters': {
                'type': 'OBJECT',
                'properties': {
                    'category': {
                        'type': 'STRING',
                        'description': 'Danh mục chi tiêu (VD: Ăn uống, Di chuyển, Mua sắm, Hóa đơn, Giải trí, Khác)'
                    },
                    'amount': {
                        'type': 'INTEGER',
                        'description': 'Số tiền (VND). Nếu là 30k thì là 30000.'
                    },
                    'note': {
                        'type': 'STRING',
                        'description': 'Ghi chú chi tiết về khoản chi'
                    },
                    'type': {
                        'type': 'STRING',
                        'description': 'Loại giao dịch: "Chi" hoặc "Thu"',
                        'enum': ['Chi', 'Thu']
                    }
                },
                'required': ['category', 'amount', 'type']
            }
        }
    ]
}

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Cấu hình (Pro Mode)")
    api_key = st.text_input("Nhập Google API Key", type="password")
    
    # Chọn Model (Hỗ trợ các đời mới nhất)
    model_option = st.selectbox(
        "Chọn Model:",
        ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.0-pro"]
    )
    
    st.info("💡 Cách nhập: 'Vừa đóng tiền mạng 250k', 'Ăn bún chả 40k'...")
    
    if st.button("🗑️ Reset dữ liệu"):
        st.session_state.expenses = []
        st.rerun()

if "expenses" not in st.session_state:
    st.session_state.expenses = []

# --- HÀM XỬ LÝ FUNCTION CALLING (TRÁI TIM) ---
def process_input_with_function_call(user_input):
    if not api_key:
        return False, "Chưa nhập API Key!"

    try:
        genai.configure(api_key=api_key)
        
        # Khởi tạo model với TOOLS (Công cụ)
        model = genai.GenerativeModel(
            model_name=model_option,
            tools=[expense_tool] # <--- Đưa "khuôn" cho AI cầm
        )
        
        # Chat với AI, bật chế độ tự động gọi hàm
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        # Gửi tin nhắn. Vì enable_automatic_function_calling=True, 
        # thư viện sẽ tự xử lý việc gọi hàm, nhưng ta cần bắt lấy dữ liệu.
        # Tuy nhiên, để kiểm soát tốt hơn trên Streamlit, ta sẽ dùng cách gọi trực tiếp:
        
        response = model.generate_content(user_input)
        
        # Kiểm tra xem AI có "gọi hàm" không?
        if hasattr(response, 'candidates') and response.candidates:
            part = response.candidates[0].content.parts[0]
            
            # Nếu AI trả về Function Call (Đúng ý đồ)
            if part.function_call:
                # Chuyển đổi dữ liệu từ Protobuf sang Dict chuẩn Python
                fc_args = part.function_call.args
                data = dict(fc_args)
                
                # Trả về dữ liệu sạch đẹp
                return True, {
                    "category": data.get("category", "Khác"),
                    "amount": int(data.get("amount", 0)),
                    "note": data.get("note", ""),
                    "type": data.get("type", "Chi")
                }
            else:
                # Nếu AI trả về text thường (Do nhập linh tinh không phải tiền nong)
                return False, f"AI không hiểu đây là khoản chi. Nó bảo: {part.text}"
        
        return False, "Không nhận được phản hồi từ AI."

    except Exception as e:
        return False, f"Lỗi kỹ thuật: {str(e)}"

# --- GIAO DIỆN CHÍNH ---
st.title("💳 Ví AI (Công nghệ Function Calling)")

# INPUT
with st.form("input_form", clear_on_submit=True):
    col_in1, col_in2 = st.columns([3, 1])
    with col_in1:
        text_input = st.text_input("Nhập giao dịch (VD: Lương về 10 củ, Mua trà sữa 50k)")
    with col_in2:
        submitted = st.form_submit_button("Ghi Sổ 🚀")

if submitted and text_input:
    with st.spinner(f"Đang gọi hàm trên {model_option}..."):
        success, result = process_input_with_function_call(text_input)
        
        if success:
            # Thêm vào danh sách
            st.session_state.expenses.append({
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                **result # Bung dữ liệu từ JSON ra
            })
            st.success(f"✅ Đã ghi: {result['note']} | {result['amount']:,} đ | {result['category']}")
        else:
            st.warning(result)

# HIỂN THỊ DỮ LIỆU
if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)
    
    st.divider()
    
    # Tính toán
    total_chi = df[df['type'] == 'Chi']['amount'].sum()
    total_thu = df[df['type'] == 'Thu']['amount'].sum()
    balance = total_thu - total_chi
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Tổng Thu", f"{total_thu:,} đ", delta_color="normal")
    k2.metric("Tổng Chi", f"{total_chi:,} đ", delta_color="inverse")
    k3.metric("Số Dư", f"{balance:,} đ")
    
    # Biểu đồ & Bảng
    c1, c2 = st.columns([1, 1])
    
    with c1:
        if total_chi > 0:
            df_chi = df[df['type'] == 'Chi']
            fig = px.pie(df_chi, values='amount', names='category', title='Phân bổ chi tiêu', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Chưa tiêu đồng nào!")
            
    with c2:
        st.dataframe(df, hide_index=True, use_container_width=True)

else:
    st.info("Hãy nhập khoản chi đầu tiên để test công nghệ mới!")

