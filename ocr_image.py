import ssl
import certifi

ssl._create_default_https_context = ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
import easyocr

def extract_text_from_image(file_path="lich_hop.png"):
    reader = easyocr.Reader(['vi'])  # 'vi' là tiếng Việt
    result = reader.readtext(file_path, detail=0)  # detail=0 chỉ lấy text
    text = "\n".join(result)
    return text

if __name__ == "__main__":
    print(extract_text_from_image())
