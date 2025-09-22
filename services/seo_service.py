import requests
from pytrends.request import TrendReq
import os
from dotenv import load_dotenv

# Load biến môi trường từ .env (nếu có)
load_dotenv()

class SEOContentPipeline:
    def __init__(self):
        """Khởi tạo pipeline với SerpAPI key cố định từ .env."""
        self.serpapi_key = os.getenv("SERPAPI_KEY")

        if not self.serpapi_key:
            raise ValueError("❌ SERPAPI_KEY chưa được cấu hình!")
        
    def fetch_keywords(self, keyword: str, geo: str = "VN"):
        """Lấy keyword liên quan từ Google Trends."""
        pytrends = TrendReq(hl="vi-VN", tz=420)
        pytrends.build_payload([keyword], timeframe="all", geo=geo)
        related = pytrends.related_queries()

        seo_keywords = []
        if keyword in related:
            top_df = related[keyword].get("top")
            if top_df is not None:
                seo_keywords = top_df.head(5)["query"].tolist()

        return seo_keywords

    def fetch_competitor_titles(self, keyword: str, location: str = "Vietnam"):
        """Lấy tiêu đề đối thủ từ Google SERP qua SerpAPI."""
        params = {
            "engine": "google",
            "q": keyword,
            "location": location,
            "api_key": self.serpapi_key,
        }
        res = requests.get("https://serpapi.com/search", params=params).json()
        return [r["title"] for r in res.get("organic_results", [])[:5]]

    def run(self, seed_keyword: str):
        """Pipeline đơn giản: Keyword → Competitors."""
        seo_keywords = self.fetch_keywords(seed_keyword)
        competitor_titles = self.fetch_competitor_titles(seed_keyword)

        return {
            "seed_keyword": seed_keyword,
            "seo_keywords": seo_keywords,
            "competitor_titles": competitor_titles,
        }
