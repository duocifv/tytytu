from services.seo_service import SEOContentPipeline

if __name__ == "__main__":
    pipeline = SEOContentPipeline()
    result = pipeline.run("Sức khỏe")

    print("\n📌 Final Output:")
    print("🔑 Seed Keyword:", result["seed_keyword"])
    print("📊 SEO Keywords:", ", ".join(result["seo_keywords"]))
    print("🏆 Competitor Titles:")
    for i, title in enumerate(result["competitor_titles"], 1):
        print(f"   {i}. {title}")
