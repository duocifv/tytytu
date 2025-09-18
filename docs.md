- Điều hành:
  Phân tích yêu cầu
  Thông dịch & chuẩn hóa
  Trung tâm
  Quản trị thương hiệu

- Sản xuất:
  Nghiên cứu & chiến lược
  Ý tưởng & Kịch bản
  Chuyên môn
  Nội dung & SEO
  Thiết kế
  Video

- Xuất bản & Phân phối:
  Xuất bản & Phân phối
  Quản lý Kênh
  Quảng cáo & Tối ưu
  Công nghệ & Tự động hóa
  KOL/Influencer & Partnerships

# manager_langgraph.py

import asyncio
from langgraph import Node, Context
from services.notion_service import NotionService

class BlogContext(Context):
"""Context chung cho tất cả node"""
def **init**(self):
super().**init**()
self.data = {}

# ---------------------------

# Node functions + Notion

# ---------------------------

async def analyze_requirements(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("📌 Phân tích yêu cầu...")
await asyncio.sleep(2)
data = {"Topic": "AI và tương lai công việc", "Audience": "Developer & PM"}
ctx.data.update(data)

    # Notion
    await notion.create_task(task_id)
    await notion.update_task(task_id, data)

async def interpret_and_standardize(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("📑 Thông dịch & chuẩn hóa...")
await asyncio.sleep(1)
guideline = {"tone": "Thân thiện", "length": "1000-1500 từ", "format": "H1,H2"}
ctx.data.update({"Guideline": guideline})
await notion.update_task(task_id, {"Guideline": guideline})

async def central_coordination(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("🧑‍💼 Trung tâm điều phối...")
await asyncio.sleep(1)
ctx.data.update({"Facts": "All data verified."})
await notion.update_task(task_id, {"Facts": "All data verified."})

async def brand_management(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("🏷️ Quản trị thương hiệu...")
await asyncio.sleep(1)
images = ["logo.png", "banner.png"]
channels = ["Fanpage", "LinkedIn"]
ctx.data.update({"Images": images, "Channels": channels})
await notion.update_task(task_id, {"Images": ", ".join(images), "Channels": ", ".join(channels)})

async def research_strategy(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("🔎 Nghiên cứu & chiến lược...")
await asyncio.sleep(2)
ctx.data.update({"Keywords": ["AI tương lai", "AI & công việc"]})
await notion.update_task(task_id, {"Keywords": ", ".join(["AI tương lai", "AI & công việc"])})

async def idea_scenario(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("💡 Ý tưởng & Kịch bản...")
await asyncio.sleep(2)
outline = ["H1: Giới thiệu AI tương lai", "H2: Ứng dụng AI & công việc"]
ctx.data.update({"Outline": outline})
await notion.update_task(task_id, {"Outline": "\n".join(outline)})

async def expertise(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("📚 Chuyên môn...")
await asyncio.sleep(1)
ctx.data.update({"Facts": "Data checked and verified."})
await notion.update_task(task_id, {"Facts": "Data checked and verified."})

async def content_seo(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("✍️ Nội dung & SEO...")
await asyncio.sleep(3)
ctx.data.update({"Content": "Nội dung bài viết chuẩn SEO..."})
await notion.update_task(task_id, {"Content": "Nội dung bài viết chuẩn SEO..."})

async def design(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("🎨 Thiết kế...")
await asyncio.sleep(2)
images = ["image1.png", "image2.png"]
ctx.data.update({"Images": images})
await notion.update_task(task_id, {"Images": ", ".join(images)})

async def video(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("🎬 Video...")
await asyncio.sleep(3)
ctx.data.update({"Video": "video_summary.mp4"})
await notion.update_task(task_id, {"Video": "video_summary.mp4"})

async def publishing_distribution(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("🚀 Xuất bản & phân phối...")
await asyncio.sleep(1)
ctx.data.update({"Status": "Đã xuất bản"})
await notion.update_task(task_id, {"Status": "Đã xuất bản"})

async def channel_management(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("📢 Quản lý kênh...")
await asyncio.sleep(1)
ctx.data.update({"Channels": ["Fanpage", "LinkedIn", "Twitter"]})
await notion.update_task(task_id, {"Channels": "Fanpage, LinkedIn, Twitter"})

async def advertising_optimization(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("📊 Quảng cáo & tối ưu...")
await asyncio.sleep(2)
ctx.data.update({"Ads": "Campaign 1 active"})
await notion.update_task(task_id, {"Ads": "Campaign 1 active"})

async def technology_automation(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("⚙️ Công nghệ & tự động hóa...")
await asyncio.sleep(1)
ctx.data.update({"Automation": "Scheduled"})
await notion.update_task(task_id, {"Automation": "Scheduled"})

async def influencer_partnerships(ctx: BlogContext, notion: NotionService, task_id="Blog Task 1"):
print("🤝 KOL/Influencer & partnerships...")
await asyncio.sleep(2)
ctx.data.update({"Influencer": "KOL ABC"})
await notion.update_task(task_id, {"Influencer": "KOL ABC"})

# ---------------------------

# Run workflow

# ---------------------------

async def run_blog_workflow(notion: NotionService):
ctx = BlogContext()

    # Nodes
    nodes = {
        "analyze_requirements": Node(lambda: analyze_requirements(ctx, notion)),
        "interpret_and_standardize": Node(lambda: interpret_and_standardize(ctx, notion)),
        "central_coordination": Node(lambda: central_coordination(ctx, notion)),
        "brand_management": Node(lambda: brand_management(ctx, notion)),
        "research_strategy": Node(lambda: research_strategy(ctx, notion)),
        "idea_scenario": Node(lambda: idea_scenario(ctx, notion)),
        "expertise": Node(lambda: expertise(ctx, notion)),
        "content_seo": Node(lambda: content_seo(ctx, notion)),
        "design": Node(lambda: design(ctx, notion)),
        "video": Node(lambda: video(ctx, notion)),
        "publishing_distribution": Node(lambda: publishing_distribution(ctx, notion)),
        "channel_management": Node(lambda: channel_management(ctx, notion)),
        "advertising_optimization": Node(lambda: advertising_optimization(ctx, notion)),
        "technology_automation": Node(lambda: technology_automation(ctx, notion)),
        "influencer_partnerships": Node(lambda: influencer_partnerships(ctx, notion))
    }

    # Điều hành: tuần tự
    await nodes["analyze_requirements"].run()
    await nodes["interpret_and_standardize"].run()
    await nodes["central_coordination"].run()
    await nodes["brand_management"].run()

    # Sản xuất: song song
    await asyncio.gather(
        nodes["research_strategy"].run(),
        nodes["idea_scenario"].run(),
        nodes["expertise"].run(),
        nodes["content_seo"].run(),
        nodes["design"].run(),
        nodes["video"].run()
    )

    # Xuất bản & phân phối: song song
    await asyncio.gather(
        nodes["publishing_distribution"].run(),
        nodes["channel_management"].run(),
        nodes["advertising_optimization"].run(),
        nodes["technology_automation"].run(),
        nodes["influencer_partnerships"].run()
    )

    print("✅ Workflow completed")
    print("Context Data:", ctx.data)

[User Input]
|
v
[Manager Node]
|
|---[Vector DB / Modal] ---> Nhận dạng ý định / context / kiến thức
|
|---[Node 1..100] + [Tool 1..100] ---> Chạy kết hợp theo logic tự động
|
v
[Aggregator] ---> Tổng hợp kết quả từ nhiều node/tool
|
v
[User Output]
------------------------
Cách Manager học và tự động hóa

Huấn luyện nội bộ (self-learning)

Mỗi node/tool tạo ra prompt hoặc template.

Manager lưu prompt này vào vector DB với context metadata.

Khi user gửi yêu cầu mới, Manager so sánh vector query với các prompt cũ → xác định node/tool phù hợp.

Quy tắc kết hợp

Manager có thể dùng:

Vector similarity: tìm node/tool liên quan nhất.

Workflow chaining: tự tạo pipeline node/tool dựa trên kết quả vector.

Memory / InMemorySaver: nhớ kết quả trước, tránh chạy lại không cần thiết.

Tự cập nhật

Khi Manager chạy xong workflow → lưu prompt + kết quả + phản hồi user vào vector DB.

Lần sau, Manager dùng kỹ thuật reinforcement để cải thiện lựa chọn node/tool.

------------------------

4️⃣ Các bước triển khai sơ bộ

Tạo 100 node & 100 tool

Mỗi node/tool là một function độc lập.

Có docstring + metadata → để Manager học vector.

Vector DB

Lưu docstring, prompt, kết quả node/tool.

Khi nhận query → tìm vector gần nhất → gợi ý node/tool.

Manager Node

Lấy input → query vector DB → quyết định workflow → chạy các node/tool → tổng hợp kết quả.

Memory

Lưu workflow + kết quả → dùng lại nếu query tương tự.

Tự huấn luyện

Lưu phản hồi user → cải thiện vector embedding → cải thiện routing node/tool.
