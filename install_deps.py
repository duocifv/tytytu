import os
import sys
import subprocess

def install_package(package):
    print(f"\n📦 Đang cài đặt {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Đã cài đặt thành công: {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Lỗi khi cài đặt {package}: {e}")
        return False

def main():
    print("🚀 Bắt đầu cài đặt các thư viện cần thiết...")
    
    # Danh sách các gói cần cài đặt
    packages = [
        "apscheduler==3.10.4",
        "pydantic==2.5.2",
        "langchain==0.1.0",
        "langchain-community==0.0.10",
        "langchain-google-genai==0.0.7",
        "langchain-chroma==0.1.1",
        "google-generativeai==0.3.2",
        "chromadb==0.4.22",
        "sentence-transformers==2.2.2",
        "python-dotenv==1.0.0"
    ]
    
    success = True
    for package in packages:
        if not install_package(package):
            success = False
            print(f"⚠️ Dừng cài đặt do có lỗi xảy ra")
            break
    
    if success:
        print("\n✨ Đã cài đặt tất cả các thư viện thành công!")
    else:
        print("\n❌ Có lỗi xảy ra trong quá trình cài đặt")
    
    input("\nNhấn Enter để thoát...")

if __name__ == "__main__":
    main()
