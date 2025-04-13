"""
图片数据库存储模块

这个模块提供了使用diskcache存储和检索图片base64编码数据的功能。
用于替代之前基于JSON文件的图片存储方式。
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import hashlib
from diskcache import Cache


class ImageStore:
    """图片存储数据库管理类，用于存储和检索图片的base64编码数据"""
    
    def __init__(self, db_path: str):
        """
        初始化图片存储数据库
        
        Args:
            db_path (str): diskcache数据库目录的路径
        """
        self.db_path = db_path
        self._init_db()
        self.cache = Cache(self.db_path)
    
    def _init_db(self) -> None:
        """初始化数据库目录（如果不存在）"""
        # 确保数据库目录存在
        os.makedirs(self.db_path, exist_ok=True)
    
    def save_image(self, key: str, base64_data: str) -> bool:
        """
        将图片的base64编码数据保存到数据库
        
        Args:
            key (str): 图片的唯一键名
            base64_data (str): 图片的base64编码数据
        
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            self.cache[key] = base64_data
            return True
        except Exception:
            return False
    
    def get_image(self, key: str) -> Optional[str]:
        """
        根据键名检索图片的base64编码数据
        
        Args:
            key (str): 图片的唯一键名
        
        Returns:
            Optional[str]: 图片的base64编码数据，如果不存在则返回None
        """
        return self.cache.get(key)
    
    def delete_image(self, key: str) -> bool:
        """
        根据键名删除图片的base64编码数据
        
        Args:
            key (str): 图片的唯一键名
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
        except Exception:
            return False
    
    def close(self) -> None:
        """
        关闭缓存连接
        """
        self.cache.close()


class PDFCache:
    """PDF解析结果缓存管理类"""
    
    def __init__(self, db_path: str):
        """
        初始化PDF缓存数据库
        
        Args:
            db_path (str): diskcache数据库目录的路径
        """
        self.db_path = db_path
        self._init_db()
        self.cache = Cache(self.db_path)
    
    def _init_db(self) -> None:
        """初始化数据库目录（如果不存在）"""
        # 确保数据库目录存在
        os.makedirs(self.db_path, exist_ok=True)
    
    def _get_url_hash(self, url: str) -> str:
        """
        计算URL的哈希值作为主键
        
        Args:
            url (str): PDF的URL
            
        Returns:
            str: URL的SHA256哈希值
        """
        return hashlib.sha256(url.encode()).hexdigest()
    
    def save_pdf(self, url: str, md_content: str) -> bool:
        """
        保存PDF解析结果到缓存
        
        Args:
            url (str): PDF的URL
            md_content (str): PDF转换的Markdown内容
            
        Returns:
            bool: 保存成功返回True，失败返回False
        """
        try:
            url_hash = self._get_url_hash(url)
            self.cache[url_hash] = {
                'url': url,
                'md_content': md_content
            }
            return True
        except Exception:
            return False
    
    def get_pdf(self, url: str) -> Optional[str]:
        """
        根据URL获取缓存的PDF Markdown内容
        
        Args:
            url (str): PDF的URL
            
        Returns:
            Optional[str]: PDF的Markdown内容，如果缓存不存在则返回None
        """
        url_hash = self._get_url_hash(url)
        data = self.cache.get(url_hash)
        return data['md_content'] if data else None
    
    def delete_pdf(self, url: str) -> bool:
        """
        删除特定URL的缓存
        
        Args:
            url (str): PDF的URL
            
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            url_hash = self._get_url_hash(url)
            if url_hash in self.cache:
                del self.cache[url_hash]
                return True
            return False
        except Exception:
            return False


def get_image_store(db_root_dir: str = None) -> ImageStore:
    """
    获取图片存储数据库实例（单一数据库）
    
    Args:
        db_root_dir (str, optional): 数据库根目录，如不指定则使用当前目录下的db目录
    
    Returns:
        ImageStore: 图片存储数据库实例
    """
    # 如果没有指定数据库根目录，则使用默认路径
    if db_root_dir is None:
        db_root_dir = os.path.join("./", "db")
    
    # 确保数据库目录存在
    os.makedirs(db_root_dir, exist_ok=True)
    
    # 使用固定的数据库目录名
    db_path = os.path.join(db_root_dir, "images_cache")
    
    # 返回ImageStore实例
    return ImageStore(db_path)


def get_pdf_cache(db_root_dir: str = None) -> PDFCache:
    """
    获取PDF缓存数据库实例
    
    Args:
        db_root_dir (str, optional): 数据库根目录，如不指定则使用当前目录下的db目录
    
    Returns:
        PDFCache: PDF缓存数据库实例
    """
    # 如果没有指定数据库根目录，则使用默认路径
    if db_root_dir is None:
        db_root_dir = os.path.join("./", "db")
    
    # 确保数据库目录存在
    os.makedirs(db_root_dir, exist_ok=True)
    
    # 使用固定的数据库目录名
    db_path = os.path.join(db_root_dir, "pdf_cache")
    
    # 返回PDFCache实例
    return PDFCache(db_path)
