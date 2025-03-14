from flask import Flask, request, jsonify
import sqlite3
import os
import json
import requests

app = Flask(__name__)

# LINEのアクセストークン（環境変数から取得）
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")

# データベースのパス
db_path = "/mnt/data/instagram_data.db"

# LINEのWebhookエンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()
    
    # イベントが存在するか確認
    if "events" not in body:
        return "No events", 400
    
    for event in body["events"]:
        if event["type"] == "message" and "text" in event["message"]:
            user_message = event["message"]["text"]
            reply_token = event["replyToken"]
            
            if user_message.startswith("登録"):  # メッセージが「登録」から始まる場合
                response = save_user_data(user_message)
                reply_to_line(reply_token, response)
                
    return "OK", 200

# ユーザー情報をデータベースに保存
def save_user_data(message):
    try:
        # 「登録|屋号|営業時間|定休日|住所|提供サービス|ターゲット|Instagram|SNSリンク|売り出し|投稿頻度」形式を解析
        parts = message.split("|")
        if len(parts) != 11:
            return "⚠️ 登録フォーマットが間違っています！正しい形式で入力してください。"
        
        _, business_name, business_hours, regular_holiday, address, services, target_audience, instagram_account, sns_links, sales_point, posting_frequency = parts
        
        # データベースに保存
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user_info (
                business_name, business_hours, regular_holiday, address, services, target_audience,
                instagram_account, sns_links, sales_point, posting_frequency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (business_name, business_hours, regular_holiday, address, services, target_audience,
              instagram_account, sns_links, sales_point, int(posting_frequency)))
        conn.commit()
        conn.close()
        
        return "✅ 登録が完了しました！"
    except Exception as e:
        return f"⚠️ エラーが発生しました: {str(e)}"

# LINEに返信
def reply_to_line(reply_token, text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    data = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post(url, headers=headers, data=json.dumps(data))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
