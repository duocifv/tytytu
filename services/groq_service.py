import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("Thiếu GROQ_API_KEY trong file .env")

client = Groq(api_key=groq_api_key)

def chat_groq(prompt: str, model: str = "openai/gpt-oss-120b", temperature: float = 0.7):
    """
    Gọi Groq GPT-OSS-120B và trả về toàn bộ kết quả JSON string một lần.
    Không dùng generator nữa.
    """
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_completion_tokens=8192,
        top_p=1,
        reasoning_effort="medium",
        stream=False,  # Luôn False để trả về 1 lần
    )

    # Trả về string hoàn chỉnh (JSON/Plain text)
    return completion.choices[0].message.content
