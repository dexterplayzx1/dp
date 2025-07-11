import streamlit as st
import cv2
import numpy as np
from PIL import Image
import tempfile
import os

st.set_page_config(page_title="Auto PDF Splitter", layout="centered")
st.markdown("# 📄 Auto PDF Splitter")
st.markdown("Upload a long screenshot with visible page borders. The app will split it into clean A4 pages and generate a PDF.")

# Upload image
uploaded_file = st.file_uploader("📤 Upload image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    with st.spinner("🔍 Detecting pages and generating PDF..."):
        # Save uploaded image to temp
        temp_dir = tempfile.mkdtemp()
        image_path = os.path.join(temp_dir, uploaded_file.name)
        with open(image_path, "wb") as f:
            f.write(uploaded_file.read())

        # Load image
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        edged = cv2.Canny(blurred, 30, 150)

        # Detect contours
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bounding_boxes = [cv2.boundingRect(c) for c in contours]
        bounding_boxes = sorted(bounding_boxes, key=lambda b: b[1])

        output_dir = os.path.join(temp_dir, "pages")
        os.makedirs(output_dir, exist_ok=True)
        pages = []

        for i, (x, y, w, h) in enumerate(bounding_boxes):
            if w > 400 and h > 400:
                cropped = img[y:y+h, x:x+w]
                output_path = os.path.join(output_dir, f"page_{i+1}.png")
                cv2.imwrite(output_path, cropped)
                pages.append(output_path)

        if not pages:
            st.error("❌ No proper bordered pages detected. Please try a cleaner image.")
        else:
            # Convert to A4 PDF
            a4_size = (1240, 1754)
            pdf_pages = []
            for p in pages:
                im = Image.open(p).convert("RGB")
                im.thumbnail(a4_size, Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", a4_size, (255, 255, 255))
                offset = ((a4_size[0] - im.width) // 2, (a4_size[1] - im.height) // 2)
                canvas.paste(im, offset)
                pdf_pages.append(canvas)

            final_pdf_path = os.path.join(temp_dir, "output.pdf")
            pdf_pages[0].save(final_pdf_path, save_all=True, append_images=pdf_pages[1:])

            st.success(f"✅ Done! {len(pages)} pages generated.")
            with open(final_pdf_path, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name="split_output.pdf", mime="application/pdf")

            # Show previews
            st.markdown("### 👇 Preview Pages")
            for p in pdf_pages:
                st.image(p)

st.markdown("---")
st.markdown("Built with ❤️ by Adithya 😎")

