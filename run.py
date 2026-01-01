import uvicorn
import os

if __name__ == "__main__":
    print("🎨 启动像素风转化器...")
    print("📍 本地访问地址: http://localhost:8000")
    print("📍 网络访问地址: http://0.0.0.0:8000")
    print("⚡ 按 Ctrl+C 停止服务")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )