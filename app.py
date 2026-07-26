import streamlit as st
import easyocr
import numpy as np
import cv2
from PIL import Image, ImageOps

# 1. Cấu hình trang web
st.set_page_config(page_title="Đọc Công Tơ Điện", page_icon="⚡", layout="centered")

st.title("⚡ Quản Lý Chỉ Số Công Tơ Điện")
st.caption("Chụp ảnh công tơ điện để tự động nhận diện dãy số và tự động thêm đơn vị kWh.")

# 2. Khởi tạo EasyOCR
@st.cache_resource
def load_ocr():
    # allowlist chỉ cho phép đọc chữ số và chữ kWh
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()

# 3. Hàm tiền xử lý ảnh tăng cường độ rõ của số
def preprocess_image(image_np):
    # Chuyển sang ảnh xám
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    
    # Tăng tương phản bằng CLAHE
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    return enhanced

# 4. Hàm trích xuất dãy số chính xác theo tọa độ từ trái sang phải
def extract_meter_reading(image_np):
    # Tiền xử lý ảnh
    processed_img = preprocess_image(image_np)
    
    # Cho EasyOCR nhận diện với cấu hình ưu tiên chữ số
    results = reader.readtext(processed_img, allowlist='0123456789kWhkWh ')
    
    digits_with_pos = []
    
    for (bbox, text, prob) in results:
        # Lấy tọa độ X trung bình để sắp xếp từ trái sang phải
        x_min = bbox[0][0]
        clean_text = ''.join(c for c in text if c.isdigit())
        if clean_text and prob > 0.15: # Lọc bỏ nhiễu
            digits_with_pos.append((x_min, clean_text))
            
    # Nếu đọc bằng ảnh nâng cao không ra, đọc thử trên ảnh gốc
    if not digits_with_pos:
        results_raw = reader.readtext(image_np)
        for (bbox, text, prob) in results_raw:
            x_min = bbox[0][0]
            clean_text = ''.join(c for c in text if c.isdigit())
            if clean_text:
                digits_with_pos.append((x_min, clean_text))

    if not digits_with_pos:
        return None

    # Sắp xếp chuỗi số từ trái qua phải dựa vào tọa độ X
    digits_with_pos.sort(key=lambda item: item[0])
    
    # Ghép tất cả các số lại với nhau
    full_digits = ''.join([item[1] for item in digits_with_pos])
    
    return full_digits

# --- GIAO DIỆN CHÍNH ---
img_file = st.file_uploader("Chụp hoặc chọn ảnh công tơ điện", type=["jpg", "jpeg", "png"])

if img_file is not None:
    image = Image.open(img_file)
    image = ImageOps.exif_transpose(image) # Sửa góc xoay iPhone
    image.thumbnail((1200, 1200)) # Nén kích thước phù hợp
    
    img_np = np.array(image)

    st.image(image, caption="Ảnh đã tải lên", use_container_width=True)

    with st.spinner("Đang xử lý và đọc chỉ số trong khung đỏ..."):
        raw_number = extract_meter_reading(img_np)

    if raw_number:
        # Tự động gắn đơn vị kWh ở cuối
        formatted_result = f"{raw_number} kWh"
        
        st.success("✅ **Đã nhận diện thành công!**")
        st.markdown(f"### Chỉ số công tơ: **`{formatted_result}`**")
    else:
        st.error("❌ Không thể đọc được dãy số. Vui lòng chụp rõ và gần hơn vào khung hiển thị số.")
