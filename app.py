import streamlit as st
import cv2
import numpy as np
import pandas as pd
import easyocr
from PIL import Image
import io
import re
from datetime import datetime

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="Đọc Công Tơ Điện & Nước", page_icon="⚡", layout="centered")

st.title("⚡ 💧 Quản Lý Chỉ Số Công Tơ")
st.caption("Chụp ảnh công tơ điện hoặc nước bằng iPhone để tự động trích xuất số và xuất Excel.")

# Khởi tạo EasyOCR (chỉ tải mô hình 1 lần)
@st.cache_resource
def load_ocr():
    # Khai báo ngôn ngữ đọc tiếng Anh (đọc chữ số)
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()

# Khởi tạo session state lưu lịch sử dữ liệu
if "records" not in st.session_state:
    st.session_state.records = []

# --- KHU VỰC NHẬP DỮ LIỆU ---
st.subheader("1. Chụp ảnh & Chọn loại công tơ")

col1, col2 = st.columns(2)
with col1:
    meter_type = st.selectbox("Loại công tơ:", ["Điện", "Nước"])
with col2:
    location = st.text_input("Mã căn hộ / Vị trí:", placeholder="VD: Phòng 101")

# Thành phần chụp ảnh (sẽ kích hoạt Camera Safari/Chrome trên iPhone)
img_file = st.file_uploader("Chụp hoặc chọn ảnh công tơ", type=["jpg", "jpeg", "png"])

def extract_numbers(image_np):
    """Trích xuất chuỗi chữ số từ hình ảnh bằng EasyOCR"""
    # Chuyển ảnh sang xám để xử lý tốt hơn
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    
    # Thực hiện OCR
    results = reader.readtext(gray)
    
    digits_found = []
    for (bbox, text, prob) in results:
        # Lọc lấy các ký tự là số
        clean_text = re.sub(r'[^\d]', '', text)
        if clean_text:
            digits_found.append(clean_text)
            
    # Ghép các chuỗi số tìm được (hoặc lấy chuỗi dài nhất)
    if digits_found:
        # Ưu tiên chuỗi số dài nhất tìm được trong ảnh
        best_match = max(digits_found, key=len)
        return best_match, results
    return "", []

if img_file is not None:
    # Đọc ảnh từ Streamlit
    image = Image.open(img_file)
    img_np = np.array(image)
    
    st.image(img_file, caption="Ảnh đã chọn", use_column_width=True)
    
    with st.spinner("Đang nhận diện chỉ số..."):
        detected_value, raw_results = extract_numbers(img_np)
    
    st.success("Đã xử lý xong!")
    
    # Cho phép người dùng kiểm tra và chỉnh sửa lại nếu OCR đọc nhầm
    final_value = st.text_input("Chỉ số nhận diện được (có thể sửa lại nếu sai):", value=detected_value)
    
    if st.button("➕ Lưu bản ghi", type="primary"):
        if final_value.strip() == "":
            st.warning("Vui lòng nhập chỉ số trước khi lưu.")
        else:
            new_entry = {
                "Thời gian": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Vị trí / Mã": location if location else "N/A",
                "Loại công tơ": meter_type,
                "Chỉ số": int(final_value) if final_value.isdigit() else final_value
            }
            st.session_state.records.append(new_entry)
            st.toast("Đã thêm bản ghi thành công!", icon="✅")
# --- KHU VỰC HIỂN THỊ VÀ XUẤT EXCEL ---
st.divider()
st.subheader("2. Danh sách dữ liệu đã ghi")

if st.session_state.records:
    df = pd.DataFrame(st.session_state.records)
    
    # Phân loại tab hiển thị
    tab_all, tab_dien, tab_nuoc = st.tabs(["Tất cả", "⚡ Điện", "💧 Nước"])
    
    with tab_all:
        st.dataframe(df, use_container_width=True)
    with tab_dien:
        df_dien = df[df["Loại công tơ"] == "Điện"]
        st.dataframe(df_dien, use_container_width=True)
    with tab_nuoc:
        df_nuoc = df[df["Loại công tơ"] == "Nước"]
        st.dataframe(df_nuoc, use_container_width=True)
        
    # Tạo file Excel có nhiều sheet (Phân loại Điện & Nước)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Tong_Hop', index=False)
        df[df["Loại công tơ"] == "Điện"].to_excel(writer, sheet_name='Cong_To_Dien', index=False)
        df[df["Loại công tơ"] == "Nước"].to_excel(writer, sheet_name='Cong_To_Nuoc', index=False)
    
    excel_data = output.getvalue()
    
    st.download_button(
        label="📥 Tải file Excel (Phân loại Điện & Nước)",
        data=excel_data,
        file_name=f"Chi_So_Cong_To_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
    
    if st.button("🗑️ Xóa toàn bộ dữ liệu tạm"):
        st.session_state.records = []
        st.rerun()
else:
    st.info("Chưa có dữ liệu nào được ghi. Hãy chụp ảnh để bắt đầu.")
