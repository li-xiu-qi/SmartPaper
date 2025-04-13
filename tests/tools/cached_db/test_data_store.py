import os
import pytest
from pathlib import Path
import hashlib

from src.tools.cached_db.data_store import (
    ImageStore, 
    PDFCache, 
    get_image_store, 
    get_pdf_cache
)

# 测试数据
TEST_IMAGE_KEY = "test_image"
TEST_IMAGE_DATA = "base64encodedimagedata"
TEST_PDF_URL = "https://example.com/test.pdf"
TEST_PDF_CONTENT = "# Markdown Content\nThis is a test PDF content"


@pytest.fixture
def temp_db_path(tmpdir):
    """创建临时数据库目录"""
    db_path = tmpdir.mkdir("test_db")
    return str(db_path)


class TestImageStore:
    
    def test_init(self, temp_db_path):
        """测试初始化和数据库目录创建"""
        store = ImageStore(temp_db_path)
        assert os.path.exists(temp_db_path)
        store.close()
    
    def test_save_image(self, temp_db_path):
        """测试保存图片数据"""
        store = ImageStore(temp_db_path)
        result = store.save_image(TEST_IMAGE_KEY, TEST_IMAGE_DATA)
        assert result is True
        store.close()
    
    def test_get_image(self, temp_db_path):
        """测试获取图片数据"""
        store = ImageStore(temp_db_path)
        store.save_image(TEST_IMAGE_KEY, TEST_IMAGE_DATA)
        
        # 测试获取存在的图片
        image_data = store.get_image(TEST_IMAGE_KEY)
        assert image_data == TEST_IMAGE_DATA
        
        # 测试获取不存在的图片
        nonexistent_data = store.get_image("nonexistent_key")
        assert nonexistent_data is None
        
        store.close()
    
    def test_delete_image(self, temp_db_path):
        """测试删除图片数据"""
        store = ImageStore(temp_db_path)
        store.save_image(TEST_IMAGE_KEY, TEST_IMAGE_DATA)
        
        # 测试删除存在的图片
        result = store.delete_image(TEST_IMAGE_KEY)
        assert result is True
        assert store.get_image(TEST_IMAGE_KEY) is None
        
        # 测试删除不存在的图片
        result = store.delete_image("nonexistent_key")
        assert result is False
        
        store.close()


class TestPDFCache:
    
    def test_init(self, temp_db_path):
        """测试初始化和数据库目录创建"""
        cache = PDFCache(temp_db_path)
        assert os.path.exists(temp_db_path)
        cache.cache.close()
    
    def test_url_hash(self, temp_db_path):
        """测试URL哈希计算"""
        cache = PDFCache(temp_db_path)
        url_hash = cache._get_url_hash(TEST_PDF_URL)
        expected_hash = hashlib.sha256(TEST_PDF_URL.encode()).hexdigest()
        assert url_hash == expected_hash
        cache.cache.close()
    
    def test_save_pdf(self, temp_db_path):
        """测试保存PDF解析结果"""
        cache = PDFCache(temp_db_path)
        result = cache.save_pdf(TEST_PDF_URL, TEST_PDF_CONTENT)
        assert result is True
        cache.cache.close()
    
    def test_get_pdf(self, temp_db_path):
        """测试获取PDF解析结果"""
        cache = PDFCache(temp_db_path)
        cache.save_pdf(TEST_PDF_URL, TEST_PDF_CONTENT)
        
        # 测试获取存在的PDF
        pdf_content = cache.get_pdf(TEST_PDF_URL)
        assert pdf_content == TEST_PDF_CONTENT
        
        # 测试获取不存在的PDF
        nonexistent_content = cache.get_pdf("https://example.com/nonexistent.pdf")
        assert nonexistent_content is None
        
        cache.cache.close()
    
    def test_delete_pdf(self, temp_db_path):
        """测试删除PDF缓存"""
        cache = PDFCache(temp_db_path)
        cache.save_pdf(TEST_PDF_URL, TEST_PDF_CONTENT)
        
        # 测试删除存在的PDF
        result = cache.delete_pdf(TEST_PDF_URL)
        assert result is True
        assert cache.get_pdf(TEST_PDF_URL) is None
        
        # 测试删除不存在的PDF
        result = cache.delete_pdf("https://example.com/nonexistent.pdf")
        assert result is False
        
        cache.cache.close()


def test_get_image_store(tmpdir):
    """测试图片存储数据库工厂函数"""
    db_root = str(tmpdir.mkdir("image_db_root"))
    
    # 测试指定路径
    store1 = get_image_store(db_root)
    assert isinstance(store1, ImageStore)
    assert os.path.exists(os.path.join(db_root, "images_cache"))
    store1.close()
    
    # 测试默认路径
    # 注意：这会在当前工作目录创建db文件夹，可能不适合CI环境
    # 所以这里临时修改工作目录到临时目录
    original_dir = os.getcwd()
    temp_dir = str(tmpdir.mkdir("default_test"))
    os.chdir(temp_dir)
    
    try:
        store2 = get_image_store()
        assert isinstance(store2, ImageStore)
        assert os.path.exists(os.path.join(temp_dir, "db", "images_cache"))
        store2.close()
    finally:
        os.chdir(original_dir)


def test_get_pdf_cache(tmpdir):
    """测试PDF缓存数据库工厂函数"""
    db_root = str(tmpdir.mkdir("pdf_db_root"))
    
    # 测试指定路径
    cache1 = get_pdf_cache(db_root)
    assert isinstance(cache1, PDFCache)
    assert os.path.exists(os.path.join(db_root, "pdf_cache"))
    cache1.cache.close()
    
    # 测试默认路径
    # 注意：这会在当前工作目录创建db文件夹，可能不适合CI环境
    # 所以这里临时修改工作目录到临时目录
    original_dir = os.getcwd()
    temp_dir = str(tmpdir.mkdir("default_test_pdf"))
    os.chdir(temp_dir)
    
    try:
        cache2 = get_pdf_cache()
        assert isinstance(cache2, PDFCache)
        assert os.path.exists(os.path.join(temp_dir, "db", "pdf_cache"))
        cache2.cache.close()
    finally:
        os.chdir(original_dir)
