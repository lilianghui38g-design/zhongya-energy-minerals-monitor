# app.py （Render 稳定简化版 - 无数据库、无 config）
from flask import Flask, render_template, jsonify, request
import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

app = Flask(__name__)

# ==================== 数据存储（内存版，避免 Render 文件系统问题） ====================
news_list = []  # 全局列表，存储所有新闻

# ==================== 来源列表（已内置，无需 config.py） ====================
SOURCES = [
    {"name": "Eurasianet", "url": "https://eurasianet.org/feed", "type": "rss"},
    {"name": "Carnegie", "url": "https://carnegieendowment.org/rss", "type": "rss"},
    {"name": "CFR", "url": "https://www.cfr.org/rss", "type": "rss"},
    {"name": "US State Dept", "url": "https://www.state.gov/rss", "type": "rss"},
    {"name": "Atlantic Council", "url": "https://www.atlanticcouncil.org/feed/", "type": "rss"},
    {"name": "CSIS", "url": "https://www.csis.org/rss", "type": "rss"},
    {"name": "Caspian Policy Center", "url": "https://www.caspianpolicy.org/research", "type": "scrape"},
    {"name": "Times of Central Asia", "url": "https://timesca.com/", "type": "scrape"},
]

KEYWORDS_US = ["US", "United States", "America", "Washington", "State Department", "C5+1"]
KEYWORDS_CA = ["Kazakhstan", "Kyrgyzstan", "Uzbekistan", "Tajikistan", "Turkmenistan", "Central Asia", "Middle Corridor"]
KEYWORDS_ENERGY = ["energy", "gas", "oil", "corridor", "pipeline"]
KEYWORDS_MINERALS = ["minerals", "critical minerals", "uranium", "rare earth", "lithium"]

def is_relevant(title, summary):
    text = (title + " " + summary).lower()
    return any(kw.lower() in text for kw in KEYWORDS_US) and any(kw.lower() in text for kw in KEYWORDS_CA)

def get_category(title, summary):
    text = (title + " " + summary).lower()
    if any(kw in text for kw in KEYWORDS_ENERGY):
        return "energy"
    if any(kw in text for kw in KEYWORDS_MINERALS):
        return "minerals"
    return "energy"

def scrape_all():
    global news_list
    new_items = []
    for src in SOURCES:
        try:
            if src["type"] == "rss":
                feed = feedparser.parse(src["url"])
                for entry in feed.entries[:6]:
                    title = entry.title
                    summary = entry.get("summary", entry.get("description", ""))[:300]
                    if is_relevant(title, summary):
                        cat = get_category(title, summary)
                        new_items.append({
                            "title": title,
                            "summary": summary,
                            "url": entry.link,
                            "source": src["name"],
                            "date": entry.get("published", datetime.now().strftime("%Y-%m-%d %H:%M")),
                            "category": cat
                        })
            else:  # scrape
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(src["url"], headers=headers, timeout=15)
                soup = BeautifulSoup(r.text, 'html.parser')
                articles = soup.select("article")[:6]
                for art in articles:
                    title_tag = art.select_one("h2, h1, .title")
                    link_tag = art.select_one("a")
                    if title_tag and link_tag:
                        title = title_tag.get_text(strip=True)
                        link = link_tag.get("href")
                        if not link.startswith("http"):
                            link = src["url"].rstrip("/") + "/" + link.lstrip("/")
                        summary = (art.select_one("p").get_text(strip=True)[:300] if art.select_one("p") else "")
                        if is_relevant(title, summary):
                            cat = get_category(title, summary)
                            new_items.append({
                                "title": title,
                                "summary": summary,
                                "url": link,
                                "source": src["name"],
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "category": cat
                            })
        except Exception as e:
            print(f"⚠️ 抓取 {src['name']} 失败: {e}")  # 会显示在 Render Logs
    # 合并最新数据（去重）
    news_list = new_items + news_list
    news_list = news_list[:50]  # 只保留最新50条

# ==================== 启动时立即抓取 ====================
scrape_all()

# ==================== 路由 ====================
@app.route('/')
def home():
    return render_template('index.html', news=news_list)

@app.route('/api/news')
def api_news():
    category = request.args.get('category', 'all')
    if category == 'energy':
        data = [n for n in news_list if n["category"] == "energy"][:20]
    elif category == 'minerals':
        data = [n for n in news_list if n["category"] == "minerals"][:20]
    else:
        data = news_list[:30]
    return jsonify(data)

@app.route('/sources')
def sources():
    return render_template('sources.html')

# 测试路由（访问 /debug 看是否正常）
@app.route('/debug')
def debug():
    return {"status": "ok", "news_count": len(news_list), "message": "网站正常运行！"}

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
