import streamlit as st
import easyocr
import numpy as np
from PIL import Image, ImageOps

# 1. Cấu hình trang web
st.set_page_config(page_title="Đọc Công Tơ Điện & Nước", page_icon="⚡", layout="centered")

st.title("⚡ 💧 Quản Lý Chỉ Số Công Tơ")
st.caption("Chụp ảnh công tơ điện hoặc nước để tự động trích xuất số và xuất Excel.")

# 2. Khởi tạo EasyOCR (chỉ tải 1 lần)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()

# 3. Khởi tạo Session State
if "records" not in st.session_state:
    st.session_state.records = []

# --- KHU VỰC NHẬP DỮ LIỆU ---
st.subheader("1. Chụp ảnh & Chọn loại công tơ")

col1, col2 = st.columns(2)
with col1:
    meter_type = st.selectbox("Loại công tơ:", ["Điện", "Nước"])
with col2:
    location = st.text_input("Mã căn hộ / Vị trí:", placeholder="VD: Phòng 101")

# Nút chọn/chụp ảnh
img_file = st.file_uploader("Chụp hoặc chọn ảnh công tơ", type=["jpg", "jpeg", "png"])

def extract_numbers(image_np):
    results = reader.readtext(image_np)
    digits_found = []
    for bbox, text, prob in results:
        clean_text = ''.join(c for c in text if c.isdigit())
        if clean_text:
            digits_found.append(clean_text)
    if digits_found:
        best_match = max(digits_found, key=len)
        return best_match
    return ""

if img_file is not None:
    # Đọc ảnh và TỰ ĐỘNG SỬA GÓC XOAY từ iPhone (EXIF)
    image = Image.open(img_file)
    image = ImageOps.exif_transpose(image)
    
    # NÉN ẢNH để tránh ngốn RAM Streamlit Cloud & xử lý cực nhanh
    image.thumbnail((1024, 1024))
    
    # Chuyển sang NumPy array
    img_np = np.array(image)

    # Hiển thị ảnh đúng chiều
    st.image(image, caption="Ảnh công tơ đã xử lý chiều chuẩn", use_container_width=True)

    # Xử lý nhận diện
    with st.spinner("Đang nhận diện chỉ số..."):
        detected_value = extract_numbers(img_np)

    if detected_value:
        st.success(f"**Chỉ số đọc được:** {detected_value}")
    else:
        st.warning("Chưa đọc được rõ số, vui lòng chụp cận cảnh mặt số công tơ hơn.")
