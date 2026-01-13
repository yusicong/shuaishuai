import os
import time
import shutil
import tempfile
import asyncio
import logging
from typing import Generator, Dict, Any, Union

try:
    from pdf2image import convert_from_path
    import numpy as np
    from PIL import Image
    HAS_PDF_TOOLS = True
except (ImportError, OSError):
    # 如果环境没有安装 poppler 或相关库，降级处理
    HAS_PDF_TOOLS = False

logger = logging.getLogger(__name__)

def analyze_pdf(file_path: str) -> str:
    """
    分析 PDF 文件类型（扫描件 vs 标准件）。
    
    原理：
    1. 将 PDF 第一页转换为图像。
    2. 分析图像的像素特征。扫描件通常会有噪点，且如果是纯图扫描，
       其灰度直方图或像素方差与数字生成的标准 PDF 不同。
    3. 这里使用一个简单的启发式规则：
       如果图像极其干净（大面积纯白背景），倾向于标准件；
       如果整页都是图片（扫描），则认为是扫描件。
       
    注意：这只是一个简单的示例实现。
    """
    if not HAS_PDF_TOOLS:
        return "无法分析(缺少依赖)"
        
    try:
        # 1. 转换第一页为图像
        # dpi=200 足够进行分析，太高会慢
        images = convert_from_path(file_path, first_page=1, last_page=1, dpi=200)
        if not images:
            return "空文件"
            
        img = images[0].convert('L') # 转为灰度图
        img_array = np.array(img)
        
        # 2. 简单图像分析
        # 计算标准差：扫描件通常因为噪点或复杂背景，标准差可能较高（不一定，视内容而定）
        # 这里使用一个更直观的方法：检测是否存在大面积纯色区域（标准PDF通常背景纯白）
        # 或者检查“文字边缘”是否锐利（数字生成的文字边缘锐利，扫描的有模糊）
        
        # 简化策略：计算非白色像素的比例。
        # 假设 255 是纯白。允许一点误差 > 250
        white_pixels = np.sum(img_array > 250)
        total_pixels = img_array.size
        white_ratio = white_pixels / total_pixels
        
        # 计算像素值的标准差
        std_dev = np.std(img_array)
        
        logger.info(f"PDF分析: 白色比例={white_ratio:.2f}, 标准差={std_dev:.2f}")
        
        # 启发式阈值（需要根据实际数据调优）
        # 扫描件往往不仅是文字，还有纸张底色，所以白色比例可能较低
        # 标准件通常是纯白背景，白色比例很高 (>0.8 或更高)
        if white_ratio > 0.90:
            return "普通PDF (Standard)"
        else:
            return "扫描件PDF (Scanned)"
            
    except Exception as e:
        logger.error(f"PDF分析出错: {e}")
        return f"分析失败: {str(e)}"

def process_non_pdf(file_path: str) -> str:
    """
    预留非 PDF 文件的处理逻辑。
    """
    return "非PDF文件 (暂未实现具体分析)"

async def file_processor_stream(file_path: str, file_name: str) -> Generator[Dict[str, Any], None, None]:
    """
    流式处理文件，生成处理步骤的事件。
    """
    try:
        # 步骤 1: 开始分析
        yield {"step": "start", "message": "开始处理文件...", "progress": 0}
        await asyncio.sleep(0.5) # 模拟耗时，让前端能看到进度变化
        
        file_ext = os.path.splitext(file_name)[1].lower()
        
        # 步骤 2: 识别文件类型
        yield {"step": "identifying", "message": f"识别文件类型: {file_ext}", "progress": 20}
        await asyncio.sleep(0.5)
        
        result_type = "未知"
        
        if file_ext == ".pdf":
            # 步骤 3: PDF 分析
            yield {"step": "analyzing_pdf", "message": "正在分析PDF类型 (图像转换中)...", "progress": 40}
            
            # 在异步函数中运行同步的 CPU 密集型任务
            loop = asyncio.get_running_loop()
            result_type = await loop.run_in_executor(None, analyze_pdf, file_path)
            
            yield {"step": "analyzing_pdf", "message": "PDF图像分析完成", "progress": 80}
            
        elif file_ext in [".doc", ".docx"]:
            # Word 处理预留
            yield {"step": "analyzing_word", "message": "检测到 Word 文档", "progress": 50}
            result_type = process_non_pdf(file_path)
            await asyncio.sleep(0.5)
        else:
            result_type = "不支持的文件格式"
        
        # 步骤 4: 完成
        yield {"step": "completed", "message": "处理完成", "progress": 100, "result": result_type}
        
    except Exception as e:
        logger.error(f"文件处理流程出错: {e}")
        yield {"step": "error", "message": str(e), "progress": 0}
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"清理临时文件: {file_path}")
            except OSError:
                pass
