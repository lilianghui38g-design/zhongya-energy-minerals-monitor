# app.py （Render 生产优化版）
from flask import Flask, render_template, jsonify, request
import feedparser, requests, sqlite3, time
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import config
import os

app = Flask(__name__)
DB = 'news.db'
scheduler = BackgroundScheduler()

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS news 
                 (id INTEGER PRIMARY KEY, title TEXT, summary TEXT, url TEXT, 
                  source TEXT, date TEXT, category TEXT)''')
    conn.commit()
    conn.close()

def is_relevant(title, summary):
    text = (title + " " + summary).lower()
    has_us = any(kw.lower() in text for kw in config.KEYWORDS_US)
    has_ca = any(kw.lower() in text for kw in config.KEYWORDS_CA)
    return has_us and has_ca

def get_category(title, summary):
    text = (title + " " + summary).lower()
    if any(kw in text for kw in config.KEYWORDS_ENERGY):
        return "energy"
    if any(kw in text for kw in config.KEYWORDS_MINERALS):
        return "minerals"
    return "energy"

def scrape_all():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    for src in config.SOURCES:
        try:
            if src["type"] == "rss":
                feed = feedparser.parse(src["url"])
                for entry in feed.entries[:8]:
                    title = entry.title
                    summary = entry.get("summary", entry.get("description", ""))[:300]
                    if is_relevant(title, summary):
                        cat = get_category(title, summary)
                        c.execute("INSERT OR IGNORE INTO news VALUES (?,?,?,?,?,?,?)",
                                  (None, title, summary, entry.link, src["name"], 
                                   entry.get("published", datetime.now().strftime("%Y-%m-%d %H:%M")), cat))
            elif src["type"] == "scrape":
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(src["url"], headers=headers, timeout=15)
                soup = BeautifulSoup(r.text, 'html.parser')
                articles = soup.select("article")
                for art in articles[:6]:
                    title_tag = art.select_one("h2") or art.select_one("h1") or art.select_one(".title")
                    link_tag = art.select_one("a")
                    if title_tag and link_tag:
                        title = title_tag.get_text(strip=True)
                        link = link_tag.get("href")
                        if not link.startswith("http"):
                            link = src["url"].rstrip("/") + "/" + link.lstrip("/")
                        summary_tag = art.select_one("p")
                        summary = summary_tag.get_text(strip=True)[:300] if summary_tag else ""
                        if is_relevant(title, summary):
                            cat = get_category(title, summary)
                            c.execute("INSERT OR IGNORE INTO news VALUES (?,?,?,?,?,?,?)",
                                      (None, title, summary, link, src["name"], 
                                       datetime.now().strftime("%Y-%m-%d %H:%M"), cat))
        except Exception as e:
            print(f"抓取 {src.get('name', '未知')} 失败: {e}")
    conn.commit()
    conn.close()

# ==================== 启动时自动执行 ====================
init_db()
scrape_all()                    # 部署后立即抓取一次
scheduler.add_job(scrape_all, 'interval', minutes=30)
scheduler.start()

# ==================== 路由 ====================
@app.route('/')
def home():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM news ORDER BY date DESC LIMIT 12")
    news = c.fetchall()
    conn.close()
    return render_template('index.html', news=news)

@app.route('/api/news')
def api_news():
    category = request.args.get('category', 'all')
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    if category == 'energy':
        c.execute("SELECT * FROM news WHERE category='energy' ORDER BY date DESC LIMIT 20")
    elif category == 'minerals':
        c.execute("SELECT * FROM news WHERE category='minerals' ORDER BY date DESC LIMIT 20")
    else:
        c.execute("SELECT * FROM news ORDER BY date DESC LIMIT 30")
    data = [{"id":r[0],"title":r[1],"summary":r[2],"url":r[3],"source":r[4],"date":r[5],"category":r[6]} for r in c.fetchall()]
    conn.close()
    return jsonify(data)

@app.route('/sources')
def sources():
    return render_template('sources.html')

# 本地测试时才执行（Render 上不会执行）
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
