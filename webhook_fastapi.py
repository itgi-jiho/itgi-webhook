from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = FastAPI()

import os
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Google Sheets 인증
json_keyfile_path = "service_account.json"
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
client = gspread.authorize(creds)
sheet = client.open("rental-gpt-log").worksheet("log_all")

class WebhookRequest(BaseModel):
    phone: str
    message: str
    product: str

@app.post("/webhook")
def webhook(req: WebhookRequest):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 🔁 GPT 응답 생성
    gpt_prompt = f"렌탈 제품 상담 도우미입니다.\n\n[고객 메시지]\n{req.message}\n\n[답변]"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 친절한 렌탈 상담 도우미입니다."},
            {"role": "user", "content": gpt_prompt}
        ]
    )
    gpt_reply = response.choices[0].message.content.strip()

    # 🔁 Google Sheet 기록
    row = [now, req.phone, req.product, req.message, gpt_reply, "상담중", "", "", "GPT응답완료"]
    sheet.append_row(row)

    return {
        "result": "success",
        "timestamp": now,
        "gpt_response": gpt_reply
    }

@app.get("/ping")
def ping():
    return {"status": "pong"}
