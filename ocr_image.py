import pytesseract
from PIL import Image

def extract_text_from_image(file_path="lich_hop.png"):
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img, lang="vie")  # OCR tiếng Việt
    return text

if __name__ == "__main__":
    print(extract_text_from_image())
