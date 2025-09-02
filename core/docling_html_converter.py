import os
import uuid
import tempfile
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Union
from urllib.parse import urlparse
import re

from docling.document_converter import DocumentConverter
from minio import Minio
from minio.error import S3Error


class DoclingHtmlToMarkdownConverter:
    """
    使用 Docling 将 HTML 内容转换为 Markdown 的核心类
    支持从 URL 获取 HTML 内容，提取图片并上传到 MinIO 对象存储
    """
    
    def __init__(
        self,
        minio_endpoint: Optional[str] = None,
        minio_access_key: Optional[str] = None,
        minio_secret_key: Optional[str] = None,
        minio_bucket: Optional[str] = None,
        minio_secure: bool = True,
        image_url_prefix: Optional[str] = None,
        enable_image_processing: bool = False,
        use_original_image_urls: bool = True
    ):
        """
        初始化转换器
        
        Args:
            minio_endpoint (str, optional): MinIO 服务端点，如 'localhost:9000'
            minio_access_key (str, optional): MinIO 访问密钥
            minio_secret_key (str, optional): MinIO 密钥
            minio_bucket (str, optional): 存储桶名称
            minio_secure (bool): 是否使用 HTTPS，默认 True
            image_url_prefix (str, optional): 图片 URL 前缀，如果为 None 则使用 MinIO 默认 URL
            enable_image_processing (bool): 是否启用图片处理功能，默认 False
            use_original_image_urls (bool): 是否使用原始图片链接，默认 True（推荐用于 HTML）
        """
        self.enable_image_processing = enable_image_processing
        self.use_original_image_urls = use_original_image_urls
        self.minio_client: Optional[Minio] = None
        
        # 只有在启用图片处理时才初始化 MinIO 相关配置
        if self.enable_image_processing:
            if not all([minio_endpoint, minio_access_key, minio_secret_key, minio_bucket]):
                raise ValueError("启用图片处理时必须提供完整的 MinIO 配置参数")
            
            # 确保参数不为 None 后再赋值
            self.minio_endpoint: str = minio_endpoint  # type: ignore
            self.minio_access_key: str = minio_access_key  # type: ignore
            self.minio_secret_key: str = minio_secret_key  # type: ignore
            self.minio_bucket: str = minio_bucket  # type: ignore
            self.minio_secure = minio_secure
            self.image_url_prefix = image_url_prefix
            
            # 初始化 MinIO 客户端
            self.minio_client = Minio(
                endpoint=self.minio_endpoint,
                access_key=self.minio_access_key,
                secret_key=self.minio_secret_key,
                secure=minio_secure
            )
            
            # 确保存储桶存在
            self._ensure_bucket_exists()
        
        # 初始化 Docling 转换器
        self.docling_converter = DocumentConverter()
    
    def _ensure_bucket_exists(self):
        """确保 MinIO 存储桶存在"""
        if not self.minio_client:
            return
            
        try:
            if not self.minio_client.bucket_exists(self.minio_bucket):
                self.minio_client.make_bucket(self.minio_bucket)
                print(f"✅ 创建存储桶: {self.minio_bucket}")
            else:
                print(f"✅ 存储桶已存在: {self.minio_bucket}")
        except S3Error as e:
            print(f"❌ MinIO 存储桶操作失败: {e}")
            raise
    
    def _fetch_html_from_url(self, html_url: str) -> str:
        """
        从 URL 获取 HTML 内容
        
        Args:
            html_url (str): HTML 页面的 URL
            
        Returns:
            str: HTML 内容
            
        Raises:
            requests.RequestException: 获取失败
        """
        try:
            print(f"🔄 正在获取 HTML 内容: {html_url}")
            
            # 设置请求头，模拟浏览器访问
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # 发送 GET 请求获取 HTML 内容
            response = requests.get(html_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 自动检测编码
            response.encoding = response.apparent_encoding or 'utf-8'
            
            html_content = response.text
            print(f"✅ HTML 内容获取完成: {len(html_content)} 字符")
            return html_content
            
        except requests.RequestException as e:
            print(f"❌ HTML 内容获取失败: {e}")
            raise
    
    def _save_html_to_temp_file(self, html_content: str, temp_dir: str) -> str:
        """
        将 HTML 内容保存到临时文件
        
        Args:
            html_content (str): HTML 内容
            temp_dir (str): 临时目录路径
            
        Returns:
            str: 临时 HTML 文件路径
        """
        try:
            # 生成临时文件名
            temp_filename = f"temp_html_{uuid.uuid4().hex[:8]}.html"
            temp_file_path = os.path.join(temp_dir, temp_filename)
            
            # 保存 HTML 内容到文件
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"💾 HTML 内容已保存到临时文件: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            print(f"❌ 保存 HTML 临时文件失败: {e}")
            raise
    
    def _upload_image_to_minio(self, image_path: str, object_name: str) -> str:
        """
        上传图片到 MinIO
        
        Args:
            image_path (str): 本地图片路径
            object_name (str): MinIO 对象名称
            
        Returns:
            str: 图片的访问 URL
            
        Raises:
            S3Error: 上传失败
        """
        if not self.minio_client:
            raise RuntimeError("MinIO 客户端未初始化，请启用图片处理功能")
            
        try:
            # 上传文件到 MinIO
            self.minio_client.fput_object(
                bucket_name=self.minio_bucket,
                object_name=object_name,
                file_path=image_path
            )
            
            # 生成访问 URL
            if self.image_url_prefix:
                image_url = f"{self.image_url_prefix}/{self.minio_bucket}/{object_name}"
            else:
                # 使用 MinIO 默认 URL 格式
                protocol = "https" if self.minio_secure else "http"
                image_url = f"{protocol}://{self.minio_endpoint}/{self.minio_bucket}/{object_name}"
            
            print(f"✅ 图片上传成功: {object_name} -> {image_url}")
            return image_url
            
        except S3Error as e:
            print(f"❌ 图片上传失败: {e}")
            raise
    
    def _extract_and_upload_images(self, doc, temp_dir: str, doc_id: str) -> Dict[str, Dict[str, str]]:
        """
        从文档中提取图片并上传到 MinIO
        
        Args:
            doc: Docling 文档对象
            temp_dir (str): 临时目录
            doc_id (str): 文档 ID
            
        Returns:
            Dict[str, Dict[str, str]]: 图片路径映射表 {原始路径: {'url': MinIO URL, 'caption': 题注}}
        """
        if not self.enable_image_processing:
            print("🖼️ 图片处理功能已禁用，跳过图片提取")
            return {}
        
        image_mapping = {}
        
        try:
            # 从文档中提取图片
            if hasattr(doc, 'pictures') and doc.pictures:
                print(f"🖼️ 发现 {len(doc.pictures)} 张图片")
                
                for i, picture in enumerate(doc.pictures):
                    try:
                        print(f"🔄 处理图片 {i+1}/{len(doc.pictures)}")
                        
                        # 检查图片对象的属性，用于调试
                        print(f"   图片对象类型: {type(picture)}")
                        if hasattr(picture, '__dict__'):
                            print(f"   图片对象属性: {list(picture.__dict__.keys())}")
                        
                        # 尝试获取图片数据
                        image_data = None
                        image_url_from_html = None
                        
                        # 方法1: 尝试使用 Docling 标准方法获取图片数据
                        if hasattr(picture, 'get_image') and callable(picture.get_image):
                            try:
                                image_data = picture.get_image(doc)
                                if image_data is not None:
                                    print(f"   📷 通过 get_image(doc) 获取图片数据: {type(image_data)}")
                                else:
                                    print(f"   ⚠️ get_image(doc) 返回 None")
                            except Exception as e:
                                print(f"   ⚠️ get_image(doc) 失败: {e}")
                        
                        # 方法2: 尝试从图片对象获取原始 URL
                        if image_data is None:
                            # 检查是否有 src 或 uri 属性
                            for attr_name in ['src', 'uri', 'url', 'href', 'path']:
                                if hasattr(picture, attr_name):
                                    attr_value = getattr(picture, attr_name)
                                    if attr_value and isinstance(attr_value, str):
                                        image_url_from_html = attr_value
                                        print(f"   🔗 找到图片URL ({attr_name}): {image_url_from_html}")
                                        break
                            
                            # 如果找到了URL，尝试下载图片
                            if image_url_from_html:
                                try:
                                    image_data = self._download_image_from_url(image_url_from_html)
                                    if image_data:
                                        print(f"   📷 从URL下载图片成功: {len(image_data)} 字节")
                                    else:
                                        print(f"   ⚠️ 从URL下载图片失败")
                                except Exception as e:
                                    print(f"   ❌ 下载图片时出错: {e}")
                        
                        # 方法3: 尝试其他可能的方法获取图片数据
                        if image_data is None:
                            if hasattr(picture, 'image') and picture.image:
                                image_ref = picture.image
                                if hasattr(image_ref, 'get_image') and callable(image_ref.get_image):
                                    try:
                                        image_data = image_ref.get_image()
                                        if image_data:
                                            print(f"   📷 通过 ImageRef.get_image() 获取数据: {type(image_data)}")
                                    except Exception as e:
                                        print(f"   ⚠️ ImageRef.get_image() 失败: {e}")
                        
                        # 如果还是获取不到数据，跳过此图片
                        if image_data is None:
                            print(f"   ⚠️ 无法获取图片 {i} 的数据，跳过")
                            continue
                        
                        # 确保图片数据是字节类型
                        if not isinstance(image_data, bytes):
                            # 如果是 PIL 图片对象，转换为字节
                            try:
                                import io
                                from PIL import Image
                                
                                if hasattr(image_data, 'save'):  # PIL Image 对象
                                    # 获取图片格式
                                    img_format = getattr(image_data, 'format', 'PNG')
                                    if img_format is None:
                                        img_format = 'PNG'
                                    
                                    # 转换为字节
                                    buffer = io.BytesIO()
                                    image_data.save(buffer, format=img_format)
                                    image_data = buffer.getvalue()
                                    
                                    print(f"   📷 PIL 图片转换为字节: {len(image_data)} 字节 (格式: {img_format})")
                                else:
                                    print(f"   ⚠️ 未知的图片数据类型: {type(image_data)}")
                                    continue
                                    
                            except Exception as e:
                                print(f"   ❌ PIL 图片转换失败: {e}")
                                continue
                        
                        # 生成图片文件名
                        image_ext = self._detect_image_format(image_data)
                        image_filename = f"{doc_id}_image_{i:03d}.{image_ext}"
                        image_path = os.path.join(temp_dir, image_filename)
                        
                        # 保存图片到临时文件
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"   💾 保存图片: {image_filename} ({len(image_data)} 字节)")
                        
                        # 上传到 MinIO
                        minio_object_name = f"images/{doc_id}/{image_filename}"
                        image_url = self._upload_image_to_minio(image_path, minio_object_name)
                        
                        # 记录映射关系
                        original_ref = f"image_{i}"
                        if hasattr(picture, 'prov') and picture.prov:
                            original_ref = str(picture.prov)
                        elif hasattr(picture, 'id') and picture.id:
                            original_ref = str(picture.id)
                        
                        image_mapping[original_ref] = {
                            'url': image_url,
                            'caption': f'图片 {i+1}'  # 简单的默认题注
                        }
                        
                        print(f"   ✅ 图片映射: {original_ref} -> {image_url}")
                        
                    except Exception as e:
                        print(f"   ❌ 处理图片 {i} 时出错: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
            else:
                print("📷 HTML 文档中没有找到图片")
        
        except Exception as e:
            print(f"❌ 提取图片时出错: {e}")
            import traceback
            traceback.print_exc()
        
        return image_mapping
    def _extract_and_process_html_images(self, doc, html_content: str, base_url: str) -> Dict[str, str]:
        """专门用于 HTML 的图片处理方法 - 支持原始链接或下载上传"""
        image_mapping = {}
        
        if not doc.pictures:
            print("📷 没有发现图片")
            return image_mapping
        
        print(f"🖼️ 发现 {len(doc.pictures)} 张图片")
        
        # 从 HTML 源码中提取图片 URL
        image_urls = self._extract_image_urls_from_html(html_content, base_url)
        
        if self.use_original_image_urls:
            # 模式1: 使用原始图片链接（推荐用于 HTML）
            print("🔗 使用原始图片链接模式")
            for i, picture in enumerate(doc.pictures):
                if i < len(image_urls):
                    original_url = image_urls[i]
                    image_mapping[f"image_{i}"] = original_url
                    print(f"✅ 图片 {i+1}: 使用原始链接 {original_url}")
                else:
                    print(f"⚠️ 图片 {i+1}: 没有找到对应的 URL")
        else:
            # 模式2: 下载并上传到 MinIO（原有功能）
            print("📥 下载并上传到 MinIO 模式")
            if not self.enable_image_processing:
                print("⚠️ 图片处理功能未启用，跳过")
                return image_mapping
                
            for i, picture in enumerate(doc.pictures):
                try:
                    # 尝试获取图片数据
                    image_data = picture.get_image(doc)
                    
                    if image_data is None and i < len(image_urls):
                        # 如果 Docling 无法获取图片，从 URL 下载
                        image_url = image_urls[i]
                        print(f"🌐 尝试下载图片: {image_url}")
                        image_data = self._download_image_from_url(image_url)
                    
                    if image_data is None:
                        print(f"⚠️ 无法获取图片 {i+1} 的数据，跳过")
                        continue
                    
                    # 检测格式并上传
                    image_format = self._detect_image_format(image_data)
                    image_filename = f"html_image_{i+1}.{image_format}"
                    
                    success = self._upload_image_data_to_minio(image_data, image_filename)
                    if success:
                        minio_url = f"http://{self.minio_endpoint}/{self.minio_bucket}/{image_filename}"
                        image_mapping[f"image_{i}"] = minio_url
                        print(f"✅ 图片 {i+1} 上传成功: {minio_url}")
                    
                except Exception as e:
                    print(f"❌ 处理图片 {i+1} 失败: {e}")
        
        return image_mapping
    
    def _extract_image_urls_from_html(self, html_content: str, base_url: str) -> list[str]:
        """从 HTML 中提取图片 URL 和 Alt 文本"""
        import re
        from urllib.parse import urljoin, urlparse
        
        image_urls = []
        
        # 使用正则表达式查找所有 img 标签，同时提取 src 和 alt
        img_pattern = r'<img[^>]*src=["\'](.*?)["\'][^>]*>'
        matches = re.findall(img_pattern, html_content, re.IGNORECASE)
        
        for src in matches:
            if src.startswith('http'):
                image_urls.append(src)
            elif src.startswith('/'):
                if base_url:
                    parsed_base = urlparse(base_url)
                    full_url = f"{parsed_base.scheme}://{parsed_base.netloc}{src}"
                    image_urls.append(full_url)
            else:
                if base_url:
                    full_url = urljoin(base_url, src)
                    image_urls.append(full_url)
        
        print(f"🔗 提取到 {len(image_urls)} 个图片 URL")
        return image_urls
    
    def _upload_image_data_to_minio(self, image_data: bytes, object_name: str) -> bool:
        """将图片数据上传到 MinIO"""
        if not self.minio_client:
            return False
        
        try:
            from io import BytesIO
            self.minio_client.put_object(
                bucket_name=self.minio_bucket,
                object_name=object_name,
                data=BytesIO(image_data),
                length=len(image_data)
            )
            return True
        except Exception as e:
            print(f"❌ MinIO 上传失败: {e}")
            return False
    
    def _download_image_from_url(self, image_url: str) -> Optional[bytes]:
        """
        从URL下载图片数据
        
        Args:
            image_url (str): 图片URL
            
        Returns:
            Optional[bytes]: 图片数据，失败时返回None
        """
        try:
            # 处理相对URL
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
            elif image_url.startswith('/'):
                # 这里需要基础URL，暂时跳过相对路径
                print(f"   ⚠️ 跳过相对路径图片: {image_url}")
                return None
            elif not image_url.startswith(('http://', 'https://')):
                print(f"   ⚠️ 跳过无效URL: {image_url}")
                return None
            
            print(f"   🔄 下载图片: {image_url}")
            
            # 设置请求头
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': image_url  # 设置 Referer 头
            }
            
            # 下载图片
            response = requests.get(image_url, headers=headers, timeout=10, stream=True)
            response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"   ⚠️ 响应不是图片类型: {content_type}")
                return None
            
            # 获取图片数据
            image_data = response.content
            
            # 检查数据大小
            if len(image_data) < 100:  # 太小的数据可能不是有效图片
                print(f"   ⚠️ 图片数据太小: {len(image_data)} 字节")
                return None
            
            print(f"   ✅ 图片下载成功: {len(image_data)} 字节")
            return image_data
            
        except Exception as e:
            print(f"   ❌ 下载图片失败: {e}")
            return None
    
    def _detect_image_format(self, image_data: bytes) -> str:
        """
        检测图片格式
        
        Args:
            image_data (bytes): 图片数据
            
        Returns:
            str: 图片扩展名
        """
        try:
            if image_data.startswith(b'\x89PNG'):
                return 'png'
            elif image_data.startswith(b'\xff\xd8'):
                return 'jpg'
            elif image_data.startswith(b'GIF'):
                return 'gif'
            elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:12]:
                return 'webp'
            elif image_data.startswith(b'BM'):
                return 'bmp'
            else:
                return 'png'  # 默认PNG
        except Exception:
            return 'png'  # 默认PNG
    
    def _replace_images_in_markdown(self, markdown_text: str, image_mapping: Dict[str, Dict[str, str]]) -> str:
        """
        替换 Markdown 中的图片链接
        
        Args:
            markdown_text (str): 原始 Markdown 文本
            image_mapping (Dict[str, Dict[str, str]]): 图片映射表 {ref: {'url': url, 'caption': caption}}
            
        Returns:
            str: 替换后的 Markdown 文本
        """
        if not image_mapping:
            return markdown_text
        
        # 提取图片信息列表
        image_infos = list(image_mapping.values())
        
        # Docling 生成的 Markdown 中图片用 <!-- image --> 注释标记
        image_comment_pattern = r'<!-- image -->'
        matches = list(re.finditer(image_comment_pattern, markdown_text))
        
        if not matches:
            print("   ⚠️ 未找到图片注释标记")
            return markdown_text
        
        print(f"   🔍 找到 {len(matches)} 个图片注释标记")
        
        # 从后往前替换，避免位置偏移
        for i, match in enumerate(reversed(matches)):
            if i < len(image_infos):
                # 获取对应的图片信息
                image_info = image_infos[-(i+1)]  # 反向索引
                image_url = image_info['url']
                caption = image_info['caption']
                
                # 创建 Markdown 图片语法
                img_markdown = f"![{caption}]({image_url})"
                
                # 替换注释
                start, end = match.span()
                markdown_text = markdown_text[:start] + img_markdown + markdown_text[end:]
                
                print(f"   ✅ 替换图片 {len(matches)-i}: <!-- image --> -> {img_markdown}")
            else:
                print(f"   ⚠️ 图片注释多于上传的图片数量")
                break
        
        return markdown_text
    
    def _replace_images_in_markdown_simple(self, markdown_text: str, image_mapping: Dict[str, str]) -> str:
        """简单的图片链接替换方法"""
        import re
        
        print(f"🔄 开始替换图片链接，映射: {len(image_mapping)} 个图片")
        
        # 方法1: 按索引顺序替换 Docling 生成的图片占位符 <!-- image -->
        placeholder_pattern = r'<!-- image -->'
        placeholders = re.findall(placeholder_pattern, markdown_text)
        print(f"   找到 {len(placeholders)} 个图片占位符")
        
        # 按索引顺序替换占位符
        for i in range(len(placeholders)):
            # 构建对应的映射键
            mapping_key = f"image_{i}"
            if mapping_key in image_mapping:
                image_url = image_mapping[mapping_key]
                # 替换第一个找到的占位符
                markdown_text = markdown_text.replace('<!-- image -->', f'![图片{i+1}]({image_url})', 1)
                print(f"   ✅ 替换占位符 {i+1}: <!-- image --> -> ![图片{i+1}]({image_url})")
            else:
                print(f"   ⚠️ 没有找到映射键 {mapping_key}，跳过占位符 {i+1}")
        
        # 方法2: 处理特定的文本图片引用（仅处理数字格式的引用，避免覆盖）
        # 查找类似 "image_1" 或 "image\\1" 的文本引用
        text_refs = re.findall(r'image[_\\\\]{1,2}(\d+)', markdown_text)
        for ref_num in text_refs:
            mapping_key = f"image_{ref_num}"
            if mapping_key in image_mapping:
                new_url = image_mapping[mapping_key]
                text_pattern = rf'image[_\\\\]{{1,2}}{re.escape(ref_num)}'
                # 将纯文本引用替换为 Markdown 图片语法
                replacement = f'![{ref_num}]({new_url})'
                markdown_text = re.sub(text_pattern, replacement, markdown_text, flags=re.IGNORECASE)
                print(f"   ✅ 替换文本引用: image[_\\\\]{{1,2}}{ref_num} -> {replacement}")
        
        # 方法3: 清理所有剩余的原始图片引用文本
        # 移除所有单独成行的 image_XXXXX 文本引用
        remaining_refs = re.findall(r'^\s*image[_\\\\]{1,2}[a-zA-Z0-9_]+\s*$', markdown_text, re.MULTILINE)
        if remaining_refs:
            print(f"   🧹 清理 {len(remaining_refs)} 个剩余的图片引用文本")
            for ref in remaining_refs:
                markdown_text = markdown_text.replace(ref.strip(), '')
                print(f"      ❌ 移除: {ref.strip()}")
        
        # 清理连续的空行（由移除引用文本产生的）
        markdown_text = re.sub(r'\n\s*\n\s*\n', '\n\n', markdown_text)
        
        return markdown_text
    
    def convert_html_url_to_markdown(self, html_url: str) -> str:
        """
        将 HTML 页面 URL 转换为 Markdown 文本
        
        Args:
            html_url (str): HTML 页面的 URL
            
        Returns:
            str: 转换后的 Markdown 文本
            
        Raises:
            Exception: 转换过程中的各种错误
        """
        temp_dir = None
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            print(f"📁 创建临时目录: {temp_dir}")
            
            # 获取 HTML 内容
            html_content = self._fetch_html_from_url(html_url)
            
            # 保存 HTML 到临时文件
            html_file_path = self._save_html_to_temp_file(html_content, temp_dir)
            
            # 调用核心转换方法
            return self._convert_html_file_to_markdown(html_file_path, temp_dir, html_content, html_url)
            
        except Exception as e:
            print(f"❌ HTML 转换失败: {e}")
            raise
        
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
                print(f"🧹 清理临时目录: {temp_dir}")
    
    def convert_html_content_to_markdown(self, html_content: str) -> str:
        """
        将 HTML 内容字符串转换为 Markdown 文本
        
        Args:
            html_content (str): HTML 内容字符串
            
        Returns:
            str: 转换后的 Markdown 文本
            
        Raises:
            Exception: 转换过程中的各种错误
        """
        temp_dir = None
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            print(f"📁 创建临时目录: {temp_dir}")
            
            # 保存 HTML 到临时文件
            html_file_path = self._save_html_to_temp_file(html_content, temp_dir)
            
            # 调用核心转换方法（对于字符串内容，不传递 base_url）
            return self._convert_html_file_to_markdown(html_file_path, temp_dir)
            
        except Exception as e:
            print(f"❌ HTML 转换失败: {e}")
            raise
        
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
                print(f"🧹 清理临时目录: {temp_dir}")
    
    def _convert_html_file_to_markdown(self, html_file_path: str, temp_dir: str, html_content: str = "", base_url: str = "") -> str:
        """
        核心转换方法：将 HTML 文件转换为 Markdown
        
        Args:
            html_file_path (str): HTML 文件路径
            temp_dir (str): 临时目录
            html_content (str): 原始 HTML 内容（用于图片处理）
            base_url (str): 基础 URL（用于相对路径处理）
            
        Returns:
            str: 转换后的 Markdown 文本
        """
        # 生成文档 ID
        doc_id = f"html_{uuid.uuid4().hex[:8]}"
        
        print(f"🔄 开始转换 HTML 文档: {html_file_path}")
        
        # 使用 Docling 转换 HTML 文档
        result = self.docling_converter.convert(html_file_path)
        doc = result.document
        
        # 处理图片
        image_mapping = {}
        if html_content and base_url:
            # 对于 HTML URL 转换，使用专门的图片处理方法
            image_mapping = self._extract_and_process_html_images(doc, html_content, base_url)
        elif self.enable_image_processing:
            # 对于其他情况，使用原有的图片处理方法
            image_mapping_old = self._extract_and_upload_images(doc, temp_dir, doc_id)
            # 转换格式以兼容
            for key, value in image_mapping_old.items():
                if isinstance(value, dict) and 'url' in value:
                    image_mapping[key] = value['url']
        
        # 导出为 Markdown
        markdown_text = doc.export_to_markdown()
        
        # 替换图片链接（如果有图片处理）
        if image_mapping:
            markdown_text = self._replace_images_in_markdown_simple(markdown_text, image_mapping)
            print(f"✅ 已处理 {len(image_mapping)} 张图片")
        
        print(f"✅ HTML 文档转换完成")
        return markdown_text


# 使用示例
if __name__ == "__main__":
    # 基础用法：只转换 HTML 到 Markdown，不处理图片
    converter_basic = DoclingHtmlToMarkdownConverter()
    
    # 高级用法：包含图片处理和 MinIO 上传
    converter_advanced = DoclingHtmlToMarkdownConverter(
        minio_endpoint="localhost:9000",
        minio_access_key="your_access_key",
        minio_secret_key="your_secret_key",
        minio_bucket="html-images",
        minio_secure=False,  # 本地开发环境
        image_url_prefix="http://localhost:9000",  # 可选的自定义 URL 前缀
        enable_image_processing=True  # 启用图片处理
    )
    
    # 转换 HTML URL
    try:
        html_url = "https://example.com/page.html"
        markdown_content = converter_basic.convert_html_url_to_markdown(html_url)
        print("转换后的 Markdown 内容:")
        print(markdown_content)
    except Exception as e:
        print(f"转换失败: {e}")
    
    # 转换 HTML 内容字符串
    try:
        html_content = "<html><body><h1>Hello World</h1><p>This is a test.</p></body></html>"
        markdown_content = converter_basic.convert_html_content_to_markdown(html_content)
        print("转换后的 Markdown 内容:")
        print(markdown_content)
    except Exception as e:
        print(f"转换失败: {e}")
