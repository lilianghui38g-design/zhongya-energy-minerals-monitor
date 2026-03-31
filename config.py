SOURCES = [
    # RSS（已验证可用）
    {"name": "Eurasianet", "url": "https://eurasianet.org/feed", "type": "rss"},
    {"name": "RFE/RL Central Asia", "url": "https://www.rferl.org/rss", "type": "rss"},
    {"name": "Carnegie Endowment", "url": "https://carnegieendowment.org/rss", "type": "rss"},
    {"name": "CFR", "url": "https://www.cfr.org/rss", "type": "rss"},
    {"name": "US State Department", "url": "https://www.state.gov/rss", "type": "rss"},
    {"name": "Atlantic Council", "url": "https://www.atlanticcouncil.org/feed/", "type": "rss"},
    {"name": "CSIS", "url": "https://www.csis.org/rss", "type": "rss"},
    {"name": "IRENA", "url": "https://www.irena.org/rss", "type": "rss"},
    # 更多 RSS 可继续添加...

    # 非 RSS（自定义抓取）
    {"name": "Caspian Policy Center", "url": "https://www.caspianpolicy.org/research", "type": "scrape", "selectors": {"list": "article", "title": "h2", "link": "a", "summary": "p"}},
    {"name": "Times of Central Asia", "url": "https://timesca.com/", "type": "scrape"},
    # 其他站点可后续扩展
]

KEYWORDS_US = ["US", "United States", "America", "Washington", "State Department", "Biden", "Trump", "C5+1", "Western"]
KEYWORDS_CA = ["Kazakhstan", "Kyrgyzstan", "Uzbekistan", "Tajikistan", "Turkmenistan", "Central Asia", "Middle Corridor", "Trans-Caspian"]
KEYWORDS_ENERGY = ["energy", "gas", "oil", "corridor", "pipeline", "electricity"]
KEYWORDS_MINERALS = ["minerals", "critical minerals", "uranium", "rare earth", "lithium", "copper"]
