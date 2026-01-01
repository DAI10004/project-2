from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import os
import uuid
import tempfile
from typing import Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="像素风转化器", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建必要的目录
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)
os.makedirs("static", exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


def pixelate_image(image, pixel_size=8, method="average"):
    """像素化图像"""
    height, width = image.shape[:2]
    
    # 计算缩放后的尺寸
    new_width = max(1, width // pixel_size)
    new_height = max(1, height // pixel_size)
    
    # 缩放图像
    if method == "average":
        # 使用最近邻插值进行下采样
        small_image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        # 放大回原尺寸
        pixelated = cv2.resize(small_image, (width, height), interpolation=cv2.INTER_NEAREST)
    elif method == "gaussian":
        # 高斯模糊 + 下采样
        blurred = cv2.GaussianBlur(image, (pixel_size + 1, pixel_size + 1), 0)
        small_image = cv2.resize(blurred, (new_width, new_height), interpolation=cv2.INTER_AREA)
        pixelated = cv2.resize(small_image, (width, height), interpolation=cv2.INTER_CUBIC)
    
    return pixelated


def quantize_colors(image, num_colors=16):
    """颜色量化"""
    # 转换到LAB色彩空间进行更好的量化
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lab_flat = lab.reshape((-1, 3))
    
    # 使用K-means聚类
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(lab_flat.astype(np.float32), num_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    
    # 将标签转换回图像
    quantized_lab = centers[labels.flatten()]
    quantized_lab = quantized_lab.reshape(image.shape)
    
    # 转换回BGR色彩空间
    quantized = cv2.cvtColor(quantized_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
    
    return quantized


def apply_dithering(image):
    """应用抖动算法"""
    result = image.copy().astype(np.float32)
    height, width = result.shape[:2]
    
    # Floyd-Steinberg抖动算法
    for y in range(height - 1):
        for x in range(width - 1):
            old_pixel = result[y, x].copy()
            new_pixel = np.round(old_pixel / 32) * 32  # 量化到8级
            result[y, x] = new_pixel
            
            error = old_pixel - new_pixel
            
            # 传播误差
            if x + 1 < width:
                result[y, x + 1] += error * 7 / 16
            if y + 1 < height:
                result[y + 1, x] += error * 5 / 16
            if x + 1 < width and y + 1 < height:
                result[y + 1, x + 1] += error * 1 / 16
            if x - 1 >= 0 and y + 1 < height:
                result[y + 1, x - 1] += error * 3 / 16
    
    return np.clip(result, 0, 255).astype(np.uint8)


@app.post("/api/pixelate")
async def pixelate_image_api(
    file: UploadFile = File(...),
    pixel_size: int = 8,
    method: str = "average",
    num_colors: Optional[int] = None,
    dither: bool = False
):
    """像素化图像API"""
    try:
        # 验证文件类型
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="只支持图像文件")
        
        # 读取图像
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise HTTPException(status_code=400, detail="无法读取图像文件")
        
        # 像素化
        if method in ["average", "gaussian"]:
            pixelated = pixelate_image(image, pixel_size, method)
        else:
            pixelated = image
        
        # 颜色量化
        if num_colors and num_colors > 0:
            pixelated = quantize_colors(pixelated, num_colors)
        
        # 应用抖动
        if dither:
            pixelated = apply_dithering(pixelated)
        
        # 保存输出图像
        output_filename = f"{uuid.uuid4().hex}.png"
        output_path = f"outputs/{output_filename}"
        cv2.imwrite(output_path, pixelated)
        
        logger.info(f"处理完成: {output_filename}")
        
        return {
            "success": True,
            "output_url": f"/api/download/{output_filename}",
            "filename": output_filename
        }
        
    except Exception as e:
        logger.error(f"处理图像时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.get("/api/download/{filename}")
async def download_image(filename: str):
    """下载处理后的图像"""
    file_path = f"outputs/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="image/png", filename=filename)
    else:
        raise HTTPException(status_code=404, detail="文件不存在")


@app.get("/")
async def read_root():
    """首页"""
    return FileResponse("static/index.html")


def process_local_images(upload_dir="uploads", output_dir="outputs", pixel_size=8, method="average", num_colors=16, dither=False):
    """批量处理本地图片文件"""
    import glob
    
    # 获取所有支持的图片格式
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.webp']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(upload_dir, ext)))
        image_files.extend(glob.glob(os.path.join(upload_dir, ext.upper())))
    
    print(f"找到 {len(image_files)} 张图片文件")
    
    for i, image_path in enumerate(image_files, 1):
        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                print(f"无法读取图片: {image_path}")
                continue
            
            print(f"处理第 {i}/{len(image_files)} 张图片: {os.path.basename(image_path)}")
            
            # 像素化
            if method in ["average", "gaussian"]:
                pixelated = pixelate_image(image, pixel_size, method)
            else:
                pixelated = image
            
            # 颜色量化
            if num_colors and num_colors > 0:
                pixelated = quantize_colors(pixelated, num_colors)
            
            # 应用抖动
            if dither:
                pixelated = apply_dithering(pixelated)
            
            # 保存输出图片
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            output_filename = f"{name}_pixelated{ext}"
            output_path = os.path.join(output_dir, output_filename)
            cv2.imwrite(output_path, pixelated)
            
            print(f"保存像素化图片: {output_filename}")
            
        except Exception as e:
            print(f"处理图片 {image_path} 时出错: {str(e)}")
    
    print("批量处理完成！")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "process":
        # 命令行模式：批量处理本地图片
        process_local_images()
    else:
        # Web服务器模式
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)