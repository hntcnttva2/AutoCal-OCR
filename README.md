# AutoCal OCR

Trích xuất nội dung lịch từ PDF/ảnh bằng OCR + Gemini, tạo sự kiện Google Calendar tự động.

## Yêu cầu

- Python 3.11
- Google Gemini API key (`GEMINI_API_KEY`)
- Google Calendar API (Service Account hoặc OAuth)

## Cài đặt

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Cấu hình môi trường

Tạo file `.env` (tham khảo `env.example` nếu có):

```env
GEMINI_API_KEY=your_gemini_api_key
# Nếu dùng Service Account và muốn chỉ định lịch đích
GOOGLE_CALENDAR_ID=your_calendar_id@group.calendar.google.com
```

Đặt file `credentials.json` (Service Account) trong thư mục gốc dự án và chia sẻ lịch đích cho email Service Account.

## Chạy

```bash
python3 main.py
```

Kết quả in ra sẽ gồm `htmlLink`, `Event ID`, `status`, `organizer`, `creator`.

## Ghi chú

- Nếu mở link báo không thấy sự kiện: hãy chia sẻ lịch cho Service Account hoặc chuyển sang OAuth.
- Nếu attendees không phải email hợp lệ, hệ thống sẽ tự bỏ qua.
