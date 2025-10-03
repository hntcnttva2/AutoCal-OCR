import json
import re
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from google.oauth2 import service_account
from googleapiclient.discovery import build
# from ocr_pdf import extract_text_from_pdf
from ocr_image import extract_text_from_image

load_dotenv()

# ===== 1. OCR =====
# text = extract_text_from_pdf("lich_hop.pdf")
text = extract_text_from_image("lich_hop.png")

# ===== 2. Gemini trích xuất =====
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")  

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

def extract_json(text: str):
    """Lấy JSON từ text, kể cả khi có ```json ... ```"""
    try:
        return json.loads(text)
    except:
        pass
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except:
            pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except:
            return None
    return None

event_data = extract_json(response.text) or {}
if not event_data:
    raise ValueError("Không lấy được dữ liệu sự kiện từ Gemini.")

# ===== 3. Google Calendar =====
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = service_account.Credentials.from_service_account_file(
    "credentials.json", scopes=SCOPES
)
service = build("calendar", "v3", credentials=creds)
calendar_id = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Thời gian sự kiện
start_dt = datetime.fromisoformat(f"{event_data['date']}T{event_data['time']}:00+07:00")
end_dt = start_dt + timedelta(hours=1)

# Lọc email hợp lệ
email_regex = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
attendees = [{"email": mail} for mail in event_data.get("attendees", []) if isinstance(mail, str) and email_regex.match(mail)]

event = {
    "summary": event_data["title"],
    "location": event_data.get("location", ""),
    "description": "Sự kiện được tạo tự động từ OCR + Gemini",
    "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Ho_Chi_Minh"},
    "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Ho_Chi_Minh"},
    **({"attendees": attendees} if attendees else {})
}

created = service.events().insert(calendarId=calendar_id, body=event, sendUpdates="all").execute()
print(json.dumps({
    "htmlLink": created.get("htmlLink"),
    "id": created.get("id"),
    "status": created.get("status"),
    "organizer": (created.get("organizer") or {}).get("email"),
    "creator": (created.get("creator") or {}).get("email"),
    "summary": created.get("summary"),
    "location": created.get("location"),
    "start": created.get("start"),
    "end": created.get("end"),
    "attendees": created.get("attendees", [])
}, ensure_ascii=False, indent=2))
print("Sự kiện đã tạo:", created.get("htmlLink"))
