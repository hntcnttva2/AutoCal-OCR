import os
import json
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
from ocr_pdf import extract_text_from_pdf
from ocr_image import extract_text_from_image

load_dotenv()

# ===== 1️⃣ Cấu hình Google Calendar =====
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = service_account.Credentials.from_service_account_file(
    "credentials.json", scopes=SCOPES
)
calendar_service = build("calendar", "v3", credentials=creds)
calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# ===== 2️⃣ Cấu hình Gemini AI =====
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")

# ===== 3️⃣ Hàm trích xuất JSON từ text trả về bởi Gemini =====
def extract_json(text: str):
    try:
        return json.loads(text)  # Thử parse trực tiếp
    except:
        pass
    # Nếu Gemini trả JSON trong code block ```json ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except:
            pass
    # Nếu JSON kèm text khác, dò bất kỳ chuỗi {...}
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            return None
    return None

# ===== 4️⃣ Hàm xử lý file gửi từ Telegram =====
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 4.1️⃣ Tải file từ Telegram về server
    file = await context.bot.get_file(update.message.document.file_id)
    file_path = f"temp_{update.message.document.file_name}"
    await file.download_to_drive(file_path)

    # 4.2️⃣ OCR: trích xuất text từ PDF hoặc hình ảnh
    if file_path.lower().endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    else:
        text = extract_text_from_image(file_path)

    os.remove(file_path)  # Xóa file tạm

    # 4.3️⃣ Gửi text OCR đến Gemini để trích xuất JSON sự kiện
    prompt = f"""
    Bạn là trợ lý AI. Đây là nội dung OCR/PDF:
    {text}

    Hãy trích xuất sự kiện dưới dạng JSON:
    {{
      "title": "Tên sự kiện",
      "date": "YYYY-MM-DD",
      "time": "HH:MM",
      "location": "Địa điểm (nếu có)",
      "attendees": ["email1", "email2"]
    }}
    """
    response = model.generate_content(prompt)
    event_data = extract_json(response.text) or {}
    if not event_data:
        await update.message.reply_text("Không lấy được dữ liệu sự kiện từ Gemini.")
        return

    # 4.4️⃣ Tạo sự kiện Google Calendar
    start_dt = datetime.fromisoformat(f"{event_data['date']}T{event_data['time']}:00+07:00")
    end_dt = start_dt + timedelta(hours=1)
    email_regex = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    attendees = [{"email": mail} for mail in event_data.get("attendees", []) 
                 if isinstance(mail, str) and email_regex.match(mail)]

    event = {
        "summary": event_data["title"],
        "location": event_data.get("location", ""),
        "description": "Sự kiện được tạo tự động từ OCR + Gemini",
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Ho_Chi_Minh"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Ho_Chi_Minh"},
        **({"attendees": attendees} if attendees else {})
    }

    created = calendar_service.events().insert(calendarId=calendar_id, body=event, sendUpdates="all").execute()

    # 4.5️⃣ Gửi link sự kiện về Telegram
    await update.message.reply_text(f"Sự kiện đã tạo: {created.get('htmlLink')}")

# ===== 5️⃣ Main: khởi động bot Telegram =====
app = ApplicationBuilder().token(os.getenv("TELEGRAM_TOKEN")).build()
# 5.1️⃣ Thêm handler để nhận tất cả file gửi tới bot
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

print("Bot đang chạy...")
app.run_polling()
