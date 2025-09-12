# 🤖 Chatbot AI với Prefect và LangChain

Một hệ thống chatbot AI đơn giản nhưng mạnh mẽ, được xây dựng với Prefect và LangChain.

## 🌟 Tính năng chính

- **Xử lý ngôn ngữ tự nhiên** với mô hình Gemini Pro
- **Quản lý luồng công việc** với Prefect
- **Tìm kiếm ngữ nghĩa** với cơ sở dữ liệu vector ChromaDB
- **Hệ thống công cụ mở rộng** dễ dàng tích hợp
- **Ghi log chi tiết** cho từng bước xử lý

## 🚀 Bắt đầu nhanh

### Yêu cầu hệ thống

- Python 3.10+
- API Key từ Google AI (miễn phí)
- Các thư viện trong `requirements.txt`

### Cài đặt

1. **Sao chép mã nguồn**
   ```bash
   git clone [đường-dẫn-repo]
   cd chatbot-ai
   ```

2. **Cài đặt các thư viện cần thiết**
   ```bash
   pip install -r requirements.txt
   ```

3. **Cấu hình biến môi trường**
   Tạo file `.env` và thêm API Key của bạn:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

4. **Chạy ứng dụng**
   ```bash
   python main.py
   ```

## 🛠 Cấu trúc thư mục

```
chatbot-ai/
├── flows/           # Chứa các luồng xử lý chính
│   ├── __init__.py
│   ├── chat_flow.py # Luồng xử lý chat chính
│   └── rag_flow.py  # Luồng xử lý tìm kiếm ngữ nghĩa
│
├── tasks/           # Các tác vụ riêng lẻ
│   ├── __init__.py
│   ├── llm_tasks.py    # Xử lý ngôn ngữ tự nhiên
│   ├── tool_tasks.py   # Quản lý các công cụ
│   └── vector_tasks.py # Làm việc với cơ sở dữ liệu vector
│
├── .env            # File cấu hình
├── main.py         # Điểm vào chương trình
└── requirements.txt # Danh sách thư viện
```

## 📝 Hướng dẫn sử dụng

### Chạy thử

```python
# Trong file main.py
from flows.chat_flow import chat_flow

async def test():
    response = await chat_flow("Xin chào, bạn có khỏe không?")
    print(response.noi_dung)
```

### Thêm công cụ mới

1. Mở file `tasks/tool_tasks.py`
2. Thêm tên và mô tả công cụ vào từ điển `CAC_CONG_CU`
3. Thêm logic xử lý trong hàm `thuc_thi_cong_cu`

### Lưu trữ dữ liệu

```python
from tasks.vector_tasks import luu_tai_lieu

# Lưu tài liệu mới
await luu_tai_lieu(
    "Nội dung tài liệu cần lưu trữ",
    {"nguon": "tên_nguồn", "ngay_tao": "2025-09-11"}
)
```

## 📄 Giấy phép

Dự án này được phân phối theo giấy phép MIT. Xem file `LICENSE` để biết thêm chi tiết.

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng tạo issue hoặc pull request nếu bạn muốn đóng góp cho dự án.
   ```
3. **Set your Google API key for Gemini:**
   - Get a free API key at: https://makersuite.google.com/app/apikey
   - Replace `"your-google-api-key-here"` in `app.py` with your actual API key
   - Or set environment variable: `export GOOGLE_API_KEY="your-key"`

## 🏃‍♂️ Running the Application

```bash
python app.py
```

The server will start on `https://nvduocfpt-chatbot-ai.hf.space/docs`

## 📖 API Usage

### Endpoints

- **POST /chat** - Main chat interface
- **GET /** - API information
- **GET /health** - Health check
- **GET /docs** - Interactive API documentation

### Example Request

```bash
curl -X POST "https://nvduocfpt-chatbot-ai.hf.space/docs" \
     -H "Content-Type: application/json" \
     -d '{"question": "Give me some health tips for better sleep"}'
```

### Example Response

```json
{
  "answer": "Health tip for sleep: Maintain 7-9 hours of sleep nightly. Create a consistent bedtime routine and avoid screens 1 hour before bed. This helps regulate your circadian rhythm and improves sleep quality.",
  "source": ["Health Tool"],
  "session_id": "uuid-generated-session-id"
}
```

## 🔧 Demo Tools

### 1. Blog Tool

- **Purpose**: Generate blog title suggestions and content ideas
- **Example**: "Give me blog ideas about AI" → Returns AI-related blog titles

### 2. Health Tool

- **Purpose**: Provide health tips and wellness advice
- **Categories**: Exercise, nutrition, sleep, stress, hydration
- **Example**: "How to manage stress?" → Returns stress management techniques

### 3. Hydroponics Tool

- **Purpose**: Hydroponic gardening guidance
- **Categories**: Nutrients, pH, lighting, water, beginner tips
- **Example**: "What pH should I use?" → Returns optimal pH ranges

### 4. Tips Tool

- **Purpose**: Quick tips on various topics
- **Categories**: Productivity, coding, learning, communication, finance
- **Example**: "Productivity tips" → Returns Pomodoro Technique advice

### 5. Fun Fact Tool

- **Purpose**: Share interesting facts and trivia
- **Example**: "Tell me a fun fact" → Returns random interesting fact

## 🧠 Memory Management

### Session Memory

- **Session-based**: Each conversation maintains context within the session
- **Implementation**: LangChain ConversationBufferMemory
- **Usage**: Remembers conversation flow and previous questions within the same session
- **Simplified**: Focused on current session only for better performance

## 🔍 RAG (Retrieval-Augmented Generation)

### ChromaDB Integration

- **Vector Storage**: Embedded knowledge base documents using HuggingFace embeddings
- **Similarity Search**: Retrieves relevant context for complex queries
- **Fallback Mechanism**: Used when tools don't provide sufficient information
- **Free Embeddings**: Uses sentence-transformers/all-MiniLM-L6-v2 model

### Knowledge Base

Pre-loaded with sample documents covering:

- Artificial Intelligence and technology
- Health and wellness information
- Sustainable living practices
- Learning and development tips

## 🏗️ Architecture

```
User Request → FastAPI → Intent Analysis → Tool Selection
                                            ↓
Memory Management ← Response Generation ← Tool Execution
                                            ↓
                                        RAG Enhancement
```

## 🔧 Customization

### Adding New Tools

1. Create a new method in the `DemoTools` class
2. Add the tool to the `setup_tools()` method in `AIAgent`
3. Update the intent analysis prompt with the new tool description

### Extending Knowledge Base

1. Add documents to the `setup_knowledge_base()` method in `ChromaDBManager`
2. Or implement document loading from files using LangChain document loaders

### Modifying Memory

- Adjust memory buffer sizes in `MemoryManager`
- Implement different memory strategies (summary, token-based, etc.)

## 🚨 Important Notes

1. **API Key Security**: Never commit your Google API key to version control
2. **Production Deployment**: Add proper authentication, rate limiting, and error handling
3. **Scaling**: Consider using Redis for session storage in production
4. **Monitoring**: Add logging and monitoring for production use

## 🧪 Testing

### Manual Testing

1. Start the server: `python app.py`
2. Visit `http://localhost:8000/docs` for interactive testing
3. Try different question types to test tool selection

### Example Test Queries

- "Give me blog ideas about technology"
- "How can I improve my sleep?"
- "What nutrients do hydroponic plants need?"
- "Share a fun fact"
- "Tips for better productivity"

## 📚 Dependencies

- **fastapi**: Web framework for building APIs
- **langchain**: LLM application framework
- **langchain-google-genai**: Google Gemini integration for LangChain
- **google-generativeai**: Google Gemini API client
- **chromadb**: Vector database for embeddings
- **sentence-transformers**: Free HuggingFace embeddings
- **uvicorn**: ASGI server for FastAPI
- **pydantic**: Data validation and serialization

## 🤝 Contributing

This is a demo system designed for learning and experimentation. Feel free to:

- Add new tools and capabilities
- Improve the RAG implementation
- Enhance memory management
- Add authentication and security features

## 📄 License

This project is provided as-is for educational and demonstration purposes.
