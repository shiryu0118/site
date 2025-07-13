import os
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    flash,
    redirect,
    url_for,
    get_flashed_messages,
)
from dotenv import load_dotenv
import requests
import requests_cache
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials
from sqlalchemy import create_engine, Table, Column, String, DateTime, MetaData
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# .envの読み込み
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev")

# BASE_URLの設定（未設定ならrequest.url_rootを使う）
def get_base_url():
    return os.environ.get("BASE_URL") or request.url_root

# requests-cache 1時間キャッシュ
requests_cache.install_cache("article_cache", expire_after=3600)

# --- 無効URLリスト取得 ---
def get_invalid_urls():
    with engine.connect() as conn:
        result = conn.execute(invalid_articles.select())
        return [row["url"] for row in result]

# --- Zenn記事検索 ---
def search_zenn(tool_name):
    url = f"https://zenn.dev/search?query={tool_name}"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    articles = []
    for a in soup.select('a[data-testid="ArticleListItem__link"]'):
        title_tag = a.select_one('[data-testid="ArticleListItem__title"]')
        if not title_tag:
            continue
        title = title_tag.text.strip()
        href = a["href"]
        articles.append({
            "url": f"https://zenn.dev{href}",
            "title": title,
            "tool_name": tool_name,
        })
        if len(articles) >= 10:
            break
    return articles

# --- Qiita記事検索 ---
def search_qiita(tool_name):
    url = f"https://qiita.com/search?q={tool_name}"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    articles = []
    for a in soup.select("a.searchResult_itemTitle"):
        title = a.text.strip()
        href = a["href"]
        articles.append({
            "url": f"https://qiita.com{href}",
            "title": title,
            "tool_name": tool_name,
        })
        if len(articles) >= 10:
            break
    return articles

# --- はてなブログ記事検索 ---
def search_hatena(tool_name):
    url = f"https://hatenablog.com/search?q={tool_name}"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    articles = []
    for a in soup.select("h2.entry-title a"):
        title = a.text.strip()
        href = a["href"]
        articles.append({
            "url": href,
            "title": title,
            "tool_name": tool_name,
        })
        if len(articles) >= 10:
            break
    return articles

# --- Google Sheets設定 ---
SHEET_ID = os.environ.get("GSHEET_ID")
SHEET_NAME = os.environ.get("SHEET_NAME", "Sheet1")
CREDENTIALS_FILE = os.environ.get("CREDENTIALS_JSON", "credentials.json")

# --- SQLite設定 ---
engine = create_engine("sqlite:///app.db")
metadata = MetaData()
invalid_articles = Table(
    "invalid_articles",
    metadata,
    Column("url", String, primary_key=True),
    Column("tool_name", String),
    Column("timestamp", DateTime),
)
metadata.create_all(engine)

@app.route("/")
def index():
    return render_template("index.html", BASE_URL=get_base_url())

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    tool_name = data.get("tool_name", "").strip()
    if not tool_name:
        flash("ツール名を入力してください", "danger")
        return jsonify([])
    try:
        articles = (
            search_zenn(tool_name) + search_qiita(tool_name) + search_hatena(tool_name)
        )
        invalid_urls = set(get_invalid_urls())
        seen_titles = set()
        results = []
        for a in articles:
            if a["url"] in invalid_urls:
                continue
            if a["title"] in seen_titles:
                continue
            seen_titles.add(a["title"])
            results.append(a)
            if len(results) >= 10:
                break
        return jsonify(results)
    except Exception as e:
        flash(f"検索中にエラーが発生しました: {e}", "danger")
        return jsonify([])

@app.route("/validate", methods=["POST"])
def validate():
    data = request.get_json()
    url = data.get("url")
    title = data.get("title")
    tool_name = data.get("tool_name")
    is_valid = data.get("is_valid")
    now = datetime.now()
    if not url or not tool_name:
        flash("パラメータ不足", "danger")
        return jsonify({"error": "パラメータ不足"}), 400
    try:
        if is_valid:
            creds = Credentials.from_service_account_file(
                CREDENTIALS_FILE,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ],
            )
            gc = gspread.authorize(creds)
            sh = gc.open_by_key(SHEET_ID)
            ws = sh.worksheet(SHEET_NAME)
            ws.append_row(
                [title, url, tool_name, now.strftime("%Y-%m-%d %H:%M:%S")]
            )
        else:
            with engine.begin() as conn:
                conn.execute(
                    invalid_articles.insert().values(
                        url=url, tool_name=tool_name, timestamp=now
                    )
                )
        return jsonify({"result": "ok"})
    except IntegrityError:
        flash("既に登録済みです", "danger")
        return jsonify({"error": "既に登録済みです"}), 400
    except Exception as e:
        flash(f"保存中にエラーが発生しました: {e}", "danger")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True) 