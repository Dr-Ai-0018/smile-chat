"""
图片路由 - 图片上传和识别
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pathlib import Path
import shutil

from routers.user import get_current_user
from services.ai_service import AIService

router = APIRouter()
ai_service = AIService()

UPLOAD_DIR = Path(__file__).parent.parent / "uploads" / "latest"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user)
):
    """上传图片（仅保留最新一张）"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只能上传图片文件")
    
    # 删除旧图片
    for old_file in UPLOAD_DIR.glob(f"{user_id}.*"):
        old_file.unlink()
    
    # 保存新图片
    file_ext = file.filename.split(".")[-1]
    file_path = UPLOAD_DIR / f"{user_id}.{file_ext}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"image_url": f"/uploads/latest/{user_id}.{file_ext}", "message": "图片上传成功"}

@router.post("/recognize")
async def recognize_image(user_id: int = Depends(get_current_user)):
    """识别用户最新上传的图片"""
    # 查找用户最新图片
    image_files = list(UPLOAD_DIR.glob(f"{user_id}.*"))
    
    if not image_files:
        raise HTTPException(status_code=404, detail="未找到图片")
    
    image_path = image_files[0]
    
    try:
        result = await ai_service.recognize_image(str(image_path))
        return {"description": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片识别失败: {str(e)}")
