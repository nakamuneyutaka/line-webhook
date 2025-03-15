from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import datetime
import requests
import schedule
import time
import json  # JSONデータのログ出力用

app = Flask(__name__)

from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)  # Flask アプリ作成

import requests
import json
from flask import Flask, jsonify

app = Flask(__name__)

import requests
import json
import datetime
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

# Flaskアプリの作成
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bamboo_plan.db'

# SQLAlchemyのインスタンスを1回だけ作成
db = SQLAlchemy(app)

# ユーザーデータのデータベースモデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100), nullable=False)
    business_hours = db.Column(db.String(100))
    address = db.Column(db.String(200))

# /callback エンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    return jsonify({"status": "success"}), 200

# アプリケーションコンテキスト内でデータベースを作成
with app.app_context():
    db.create_all()

# Flaskアプリを実行
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

INSTAGRAM_ACCESS_TOKEN = "EAAI84JL6mY0BO4ZBpj1XmKI99DSw0Yvrqf4S1CC7MChUvzo6Y8W6M8NtxAlRqEm9KZAr9Eo6OIZAZC0QbnM6pb7Jz7yBrEsf6nUbHsBLzPP3m2GEpJLzWXA5xtHX1iyEwqIcTMgztm1ZBFsZBwoNCvNZAXmuTmPcpIC7cnMq6z7MzZCanAQK1kdw2MXcOdiTmVdiYWZCTHF94i3mKslCTmcPsZBeZAgOfKfoz2yPwZDZD"  # ここに正しいアクセストークンを入れる
INSTAGRAM_GRAPH_API_URL = "https://graph.facebook.com/v22.0/17841459355663986/media"

@app.route("/instagram_fetch", methods=["GET"])
def fetch_instagram_data():
    response = requests.get(
        INSTAGRAM_GRAPH_API_URL,
        params={
            "fields": "id,caption,media_type,media_url,timestamp",
            "access_token": INSTAGRAM_ACCESS_TOKEN
        }
    )
    
    if response.status_code == 200:
        data = response.json().get("data", [])
        
        for item in data:
            post_id = item["id"]
            caption = item.get("caption", "")
            media_type = item["media_type"]
            media_url = item["media_url"]
            timestamp = datetime.datetime.strptime(item["timestamp"], "%Y-%m-%dT%H:%M:%S%z")

            # 既に存在しない場合のみ追加
            if not InstagramData.query.get(post_id):
                new_post = InstagramData(
                    id=post_id,
                    caption=caption,
                    media_type=media_type,
                    media_url=media_url,
                    timestamp=timestamp
                )
                db.session.add(new_post)
        
        db.session.commit()
        return jsonify({"message": "Instagram data saved successfully", "data": data})
    
    else:
        return jsonify({"error": "Failed to fetch Instagram data", "status": response.status_code})

# ✅ /callback エンドポイントを追加
@app.route("/callback", methods=["POST"])
def callback():
    return jsonify({"status": "success"}), 200

# Flaskアプリを実行
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bamboo_plan.db'
db = SQLAlchemy(app)

# アプリケーションコンテキスト内でデータベースを作成
with app.app_context():
    db.create_all()

# ユーザーデータのデータベースモデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100), nullable=False)
    business_hours = db.Column(db.String(100))
    address = db.Column(db.String(200))
    services = db.Column(db.Text)
    target_audience = db.Column(db.String(200))
    instagram_account = db.Column(db.String(100), unique=True, nullable=False)
    access_token = db.Column(db.String(255), nullable=False)
    sns_links = db.Column(db.Text)
    selling_points = db.Column(db.Text)
    posting_frequency = db.Column(db.Integer, default=3)
    last_post_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    line_user_id = db.Column(db.String(100), nullable=True)

# **🔹 Webhookエンドポイント（LINEのuserIdを取得）**
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook受信データ:", data)
    if 'events' in data and len(data['events']) > 0:
        user_id = data['events'][0]['source']['userId']
        print(f"取得した userId: {user_id}")

        # 該当ユーザーを検索（仮に最初のユーザーを対象とする）
        user = User.query.first()
        if user:
            user.line_user_id = user_id
            db.session.commit()
            print(f"User ID {user.id} に userId を保存しました。")

        return jsonify({"status": "success", "userId": user_id}), 200
    return jsonify({"status": "no events"}), 400

# **🔹 投稿リマインドAPI（LINE通知）**
@app.route('/reminder', methods=['GET'])
def send_reminder():
    users = User.query.all()
    reminders = []
    today = datetime.datetime.utcnow()

    for user in users:
        days_since_last_post = (today - user.last_post_date).days
        if days_since_last_post >= (7 / user.posting_frequency):
            message = f"\U0001F4E2 今日は投稿の日！ {user.business_name} さん、投稿をお忘れなく！\n\U0001F31F {user.selling_points} を紹介する投稿をしましょう！"
            success = send_line_notification(user, message)
            if success:
                user.last_post_date = today
                db.session.commit()
            reminders.append({
                'message': message,
                'link': 'https://www.instagram.com/create/story/'
            })
    return jsonify({'reminders': reminders}), 200

# **🔹 LINE通知用関数（ログを追加）**
def send_line_notification(user, message):
    if not user.line_user_id:
        print("❌ LINE通知失敗: userId が登録されていません。")
        return False
    
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer xCVmcmrmiJgBa+l4GuDQQ5QYVIe7JwEgf+963fqHpeO1tCfkugadBSKG/xOl5klBs4X08ZpGlC+jcoIHkOPePrSR7FTpZy0p0kzoZhLyqKHb65PDz+tWCsL/WopyEWtP6imdAIp3dSFAmgO8z4zXfwdB04t89/1O/w1cDnyilFU="  # ここを正しいトークンにする
    }
    data = {
        "to": user.line_user_id,
        "messages": [{"type": "text", "text": message}]
    }

    print("🚀 LINE通知送信中...")
    print("📩 送信データ:", json.dumps(data, indent=2))

    response = requests.post(url, headers=headers, json=data)
    
    print("📡 LINE APIレスポンス:", response.status_code, response.text)

    if response.status_code == 200:
        print("✅ LINE通知送信成功！")
        return True
    else:
        print("❌ LINE通知送信失敗:", response.text)
        return False

# **🔹 ユーザー登録API**
@app.route('/register', methods=['POST'])
def register_user():
    data = request.json
    new_user = User(
        business_name=data['business_name'],
        business_hours=data.get('business_hours', ''),
        address=data.get('address', ''),
        services=data.get('services', ''),
        target_audience=data.get('target_audience', ''),
        instagram_account=data['instagram_account'],
        access_token=data['access_token'],
        sns_links=data.get('sns_links', ''),
        selling_points=data.get('selling_points', ''),
        posting_frequency=data.get('posting_frequency', 3),
        line_user_id=data.get('line_user_id', '')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!', 'user_id': new_user.id}), 201

if __name__ == '__main__':
    app.run(debug=True)
