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


class DoclingWordToMarkdownConverter:
    """
    使用 Docling 将 Word 文档转换为 Markdown 的核心类
    支持从 URL 下载文档，提取图片并上传到 MinIO 对象存储
    """
    
    def __init__(
        self,
        minio_endpoint: str,
        minio_access_key: str,
        minio_secret_key: str,
        minio_bucket: str,
        minio_secure: bool = True,
        image_url_prefix: Optional[str] = None
    ):
        """
        初始化转换器
        
        Args:
            minio_endpoint (str): MinIO 服务端点，如 'localhost:9000'
            minio_access_key (str): MinIO 访问密钥
            minio_secret_key (str): MinIO 密钥
            minio_bucket (str): 存储桶名称
            minio_secure (bool): 是否使用 HTTPS，默认 True
            image_url_prefix (str, optional): 图片 URL 前缀，如果为 None 则使用 MinIO 默认 URL
        """
        self.minio_endpoint = minio_endpoint
        self.minio_access_key = minio_access_key
        self.minio_secret_key = minio_secret_key
        self.minio_bucket = minio_bucket
        self.minio_secure = minio_secure
        self.image_url_prefix = image_url_prefix
        
        # 初始化 MinIO 客户端
        self.minio_client = Minio(
            endpoint=minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=minio_secure
        )
        
        # 初始化 Docling 转换器
        self.docling_converter = DocumentConverter()
        
        # 确保存储桶存在
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保 MinIO 存储桶存在"""
        try:
            if not self.minio_client.bucket_exists(self.minio_bucket):
                self.minio_client.make_bucket(self.minio_bucket)
                print(f"✅ 创建存储桶: {self.minio_bucket}")
            else:
                print(f"✅ 存储桶已存在: {self.minio_bucket}")
        except S3Error as e:
            print(f"❌ MinIO 存储桶操作失败: {e}")
            raise
    
    def _download_file_from_url(self, url: str, temp_dir: str) -> str:
        """
        从 URL 下载文件到临时目录
        
        Args:
            url (str): 文件 URL
            temp_dir (str): 临时目录路径
            
        Returns:
            str: 下载的文件路径
            
        Raises:
            requests.RequestException: 下载失败
        """
        try:
            print(f"🔄 正在下载文件: {url}")
            
            # 发送 GET 请求下载文件
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 从 URL 或 Content-Disposition 头获取文件名
            filename = self._extract_filename_from_url_or_header(url, response.headers)
            
            # 下载文件
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ 文件下载完成: {file_path}")
            return file_path
            
        except requests.RequestException as e:
            print(f"❌ 文件下载失败: {e}")
            raise
    
    def _extract_filename_from_url_or_header(self, url: str, headers: Union[Dict[str, Any], Any]) -> str:
        """
        从 URL 或响应头中提取文件名
        
        Args:
            url (str): 文件 URL
            headers: HTTP 响应头
            
        Returns:
            str: 文件名
        """
        # 尝试从 Content-Disposition 头获取文件名
        content_disposition = headers.get('Content-Disposition', '')
        if content_disposition:
            filename_match = re.search(r'filename[*]?=([^;]+)', content_disposition)
            if filename_match:
                filename = filename_match.group(1).strip('"\'')
                return filename
        
        # 从 URL 路径获取文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # 如果没有扩展名，添加默认扩展名
        if not filename or '.' not in filename:
            filename = f"document_{uuid.uuid4().hex[:8]}.docx"
        
        return filename
    
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
    
    def _extract_image_caption(self, picture, doc, caption_texts: Dict[int, str], picture_index: int) -> Optional[str]:
        """
        提取图片题注
        
        Args:
            picture: Docling 图片对象
            doc: Docling 文档对象
            caption_texts: 包含图片相关文本的字典 {文本索引: 文本内容}
            picture_index: 图片索引
            
        Returns:
            Optional[str]: 图片题注，如果没有找到则返回 None
        """
        caption = None
        
        try:
            # 方法1: 尝试使用 Docling 内置的题注方法
            if hasattr(picture, 'caption_text') and callable(picture.caption_text):
                try:
                    caption = picture.caption_text(doc)
                    if caption and str(caption).strip():
                        print(f"   📝 通过 caption_text() 找到题注: {caption}")
                        return str(caption).strip()
                except Exception as e:
                    print(f"   ⚠️ caption_text() 方法失败: {e}")
            
            # 方法2: 尝试从 captions 属性获取
            if hasattr(picture, 'captions') and picture.captions:
                try:
                    if isinstance(picture.captions, list) and picture.captions:
                        caption = str(picture.captions[0])
                        if caption and caption.strip():
                            print(f"   📝 通过 captions 属性找到题注: {caption}")
                            return caption.strip()
                    elif isinstance(picture.captions, str) and picture.captions.strip():
                        print(f"   📝 通过 captions 属性找到题注: {picture.captions}")
                        return picture.captions.strip()
                except Exception as e:
                    print(f"   ⚠️ captions 属性解析失败: {e}")
            
            # 方法3: 在 Markdown 中查找题注（优先级提高）
            if hasattr(doc, 'export_to_markdown'):
                try:
                    markdown_content = doc.export_to_markdown()
                    caption = self._extract_caption_from_markdown(markdown_content, picture_index)
                    if caption:
                        print(f"   📝 通过 Markdown 分析找到题注: {caption}")
                        return caption
                except Exception as e:
                    print(f"   ⚠️ Markdown 题注提取失败: {e}")
            
            # 方法4: 基于位置的题注检测（最后尝试）
            # 查找与此图片最相关的题注文本
            potential_captions = []
            for text_index, text_content in caption_texts.items():
                # 检查是否是图片相关的题注
                if self._is_likely_image_caption(text_content, picture_index):
                    # 为题注评分，优先选择包含数字的题注
                    score = self._score_caption_relevance(text_content, picture_index)
                    potential_captions.append((score, text_content, text_index))
            
            # 按分数排序，选择最相关的题注
            if potential_captions:
                potential_captions.sort(key=lambda x: x[0], reverse=True)
                best_caption = potential_captions[0][1]
                text_index = potential_captions[0][2]
                print(f"   📝 通过位置分析找到题注 (文本索引 {text_index}): {best_caption}")
                return best_caption.strip()
            
        except Exception as e:
            print(f"   ⚠️ 题注提取过程出错: {e}")
        
        return None
    
    def _is_likely_image_caption(self, text: str, picture_index: int) -> bool:
        """
        判断文本是否可能是图片题注
        
        Args:
            text (str): 文本内容
            picture_index (int): 图片索引
            
        Returns:
            bool: 是否可能是题注
        """
        text = text.strip()
        if not text:
            return False
        
        # 检查是否包含图片相关关键词
        image_keywords = ['图', 'Figure', 'Fig.', '图片', '示意图', '流程图', '架构图', '时序图']
        
        # 检查是否以数字开头（如 "图 1"，"Figure 1" 等）
        number_patterns = [
            r'^图\s*\d+',  # 图 1, 图1
            r'^Figure\s*\d+',  # Figure 1
            r'^Fig\.\s*\d+',  # Fig. 1
            r'^\d+\.\s*图',  # 1. 图
        ]
        
        # 检查模式匹配
        for pattern in number_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # 检查是否包含图片关键词且长度合理（通常题注不会太长）
        if any(keyword in text for keyword in image_keywords) and len(text) < 200:
            return True
        
        return False
    
    def _extract_caption_from_markdown(self, markdown_content: str, picture_index: int) -> Optional[str]:
        """
        从 Markdown 内容中提取图片题注
        
        Args:
            markdown_content (str): Markdown 文本
            picture_index (int): 图片索引
            
        Returns:
            Optional[str]: 提取的题注
        """
        try:
            lines = markdown_content.split('\n')
            image_comment_count = 0
            
            # 查找对应索引的图片注释后的题注
            for i, line in enumerate(lines):
                if '<!-- image -->' in line:
                    if image_comment_count == picture_index:
                        # 检查后续几行是否有题注
                        for j in range(1, 5):  # 检查后续4行
                            if i + j < len(lines):
                                next_line = lines[i + j].strip()
                                if next_line and self._is_likely_image_caption(next_line, picture_index):
                                    return next_line
                        break
                    image_comment_count += 1
            
        except Exception as e:
            print(f"   ⚠️ Markdown 题注解析失败: {e}")
        
        return None
    
    def _extract_image_caption(self, picture, doc, caption_texts: Dict[int, str], picture_index: int) -> Optional[str]:
        """
        提取图片题注
        
        Args:
            picture: Docling 图片对象
            doc: Docling 文档对象
            caption_texts: 包含图片相关文本的字典 {文本索引: 文本内容}
            picture_index: 图片索引
            
        Returns:
            Optional[str]: 图片题注，如果没有找到则返回 None
        """
        caption = None
        
        try:
            # 方法1: 尝试使用 Docling 内置的题注方法
            if hasattr(picture, 'caption_text') and callable(picture.caption_text):
                try:
                    caption = picture.caption_text(doc)
                    if caption and caption.strip():
                        print(f"   📝 通过 caption_text() 找到题注: {caption}")
                        return caption.strip()
                except Exception as e:
                    print(f"   ⚠️ caption_text() 方法失败: {e}")
            
            # 方法2: 尝试从 captions 属性获取
            if hasattr(picture, 'captions') and picture.captions:
                try:
                    if isinstance(picture.captions, list) and picture.captions:
                        caption = str(picture.captions[0])
                        if caption and caption.strip():
                            print(f"   📝 通过 captions 属性找到题注: {caption}")
                            return caption.strip()
                    elif isinstance(picture.captions, str) and picture.captions.strip():
                        print(f"   📝 通过 captions 属性找到题注: {picture.captions}")
                        return picture.captions.strip()
                except Exception as e:
                    print(f"   ⚠️ captions 属性解析失败: {e}")
            
            # 方法3: 在 Markdown 中查找题注（优先级提高）
            if hasattr(doc, 'export_to_markdown'):
                try:
                    markdown_content = doc.export_to_markdown()
                    caption = self._extract_caption_from_markdown(markdown_content, picture_index)
                    if caption:
                        print(f"   📝 通过 Markdown 分析找到题注: {caption}")
                        return caption
                except Exception as e:
                    print(f"   ⚠️ Markdown 题注提取失败: {e}")
            
            # 方法4: 基于位置的题注检测（最后尝试）
            # 查找与此图片最相关的题注文本
            potential_captions = []
            for text_index, text_content in caption_texts.items():
                # 检查是否是图片相关的题注
                if self._is_likely_image_caption(text_content, picture_index):
                    # 为题注评分，优先选择包含数字的题注
                    score = self._score_caption_relevance(text_content, picture_index)
                    potential_captions.append((score, text_content, text_index))
            
            # 按分数排序，选择最相关的题注
            if potential_captions:
                potential_captions.sort(key=lambda x: x[0], reverse=True)
                best_caption = potential_captions[0][1]
                text_index = potential_captions[0][2]
                print(f"   📝 通过位置分析找到题注 (文本索引 {text_index}): {best_caption}")
                return best_caption.strip()
            
        except Exception as e:
            print(f"   ⚠️ 题注提取过程出错: {e}")
        
        return None
    
    def _score_caption_relevance(self, text: str, picture_index: int) -> float:
        """
        为题注相关性评分
        
        Args:
            text (str): 题注文本
            picture_index (int): 图片索引
            
        Returns:
            float: 相关性分数，越高越相关
        """
        score = 0.0
        
        # 检查是否包含对应的图片编号（图 1, 图 2 等）
        expected_number = picture_index + 1
        if f'图 {expected_number}' in text or f'图{expected_number}' in text:
            score += 10.0
        
        if f'Figure {expected_number}' in text or f'Fig. {expected_number}' in text:
            score += 10.0
        
        # 检查是否是具体的图片描述（而不是通用定义）
        general_terms = ['题注：', '定义', '说明', '指', '位于', '针对']
        if not any(term in text for term in general_terms):
            score += 5.0
        
        # 短小精悍的题注得分更高
        if len(text) < 50:
            score += 2.0
        elif len(text) > 200:
            score -= 2.0
        
        # 包含描述性词汇的题注得分更高
        descriptive_terms = ['示例', '流程', '结构', '界面', '功能', '操作']
        score += sum(1.0 for term in descriptive_terms if term in text)
        
        return score
    
    def _extract_and_upload_images(self, doc, temp_dir: str, doc_id: str) -> Dict[str, Dict[str, str]]:
        """
        提取文档中的图片并上传到 MinIO
        
        Args:
            doc: Docling 文档对象
            temp_dir (str): 临时目录
            doc_id (str): 文档 ID
            
        Returns:
            Dict[str, Dict[str, str]]: 图片路径映射表 {原始路径: {'url': MinIO URL, 'caption': 题注}}
        """
        image_mapping = {}
        
        try:
            # 从文档中提取图片
            if hasattr(doc, 'pictures') and doc.pictures:
                print(f"🖼️ 发现 {len(doc.pictures)} 张图片")
                
                # 获取所有文本对象，用于题注检测
                caption_texts = {}
                if hasattr(doc, 'texts') and doc.texts:
                    for i, text_item in enumerate(doc.texts):
                        if hasattr(text_item, 'text') and text_item.text:
                            text = text_item.text.strip()
                            # 检查是否包含图片相关关键词
                            if any(keyword in text for keyword in ['图', 'Figure', 'Fig.', '图片', '示意图', '流程图', '架构图', '时序图']):
                                caption_texts[i] = text
                                print(f"   📝 找到候选题注文本 {i}: {text}")
                
                for i, picture in enumerate(doc.pictures):
                    try:
                        print(f"🔄 处理图片 {i+1}/{len(doc.pictures)}")
                        
                        # 检查图片对象的属性
                        print(f"   图片对象类型: {type(picture)}")
                        
                        # 尝试获取图片题注
                        caption = self._extract_image_caption(picture, doc, caption_texts, i)
                        if caption:
                            print(f"   📝 检测到题注: {caption}")
                        else:
                            print(f"   📝 未检测到题注，使用默认值")
                        
                        # 尝试获取图片数据
                        image_data = None
                        
                        # 尝试使用 get_image() 方法
                        if hasattr(picture, 'get_image') and callable(picture.get_image):
                            try:
                                # 传入 doc 参数
                                image_data = picture.get_image(doc)
                                print(f"   📷 通过 get_image(doc) 获取图片数据: {type(image_data)}")
                            except Exception as e:
                                print(f"   ⚠️ get_image(doc) 失败: {e}")
                                # 尝试不传参数
                                try:
                                    image_data = picture.get_image()
                                    print(f"   📷 通过 get_image() 获取图片数据: {type(image_data)}")
                                except Exception as e2:
                                    print(f"   ⚠️ get_image() 也失败: {e2}")
                        
                        # 如果 get_image() 没有成功，尝试其他方法
                        if image_data is None:
                            if hasattr(picture, 'image') and picture.image:
                                image_ref = picture.image
                                print(f"   📷 图片引用类型: {type(image_ref)}")
                                
                                # 如果是 ImageRef 对象，尝试获取其数据
                                if hasattr(image_ref, 'get_image') and callable(image_ref.get_image):
                                    try:
                                        image_data = image_ref.get_image()
                                        print(f"   📷 通过 ImageRef.get_image() 获取数据: {type(image_data)}")
                                    except Exception as e:
                                        print(f"   ⚠️ ImageRef.get_image() 失败: {e}")
                                
                                # 尝试其他可能的属性
                                if image_data is None:
                                    for attr in ['data', 'content', 'bytes', 'image_data']:
                                        if hasattr(image_ref, attr):
                                            potential_data = getattr(image_ref, attr)
                                            if isinstance(potential_data, bytes):
                                                image_data = potential_data
                                                print(f"   📷 通过 {attr} 属性获取数据")
                                                break
                            
                            # 尝试其他直接属性
                            if image_data is None:
                                for attr in ['data', 'content', 'bytes', 'image_data']:
                                    if hasattr(picture, attr):
                                        potential_data = getattr(picture, attr)
                                        if isinstance(potential_data, bytes):
                                            image_data = potential_data
                                            print(f"   📷 通过 picture.{attr} 属性获取数据")
                                            break
                        
                        # 确保图片数据是字节类型
                        if image_data is not None:
                            if isinstance(image_data, bytes):
                                # 直接是字节数据
                                print(f"   📷 图片数据已是字节格式: {len(image_data)} 字节")
                            else:
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
                        else:
                            print(f"   ⚠️ 无法获取图片 {i} 的数据")
                            continue
                        
                        # 生成图片文件名
                        image_ext = self._get_image_extension(picture)
                        image_filename = f"{doc_id}_image_{i:03d}.{image_ext}"
                        image_path = os.path.join(temp_dir, image_filename)
                        
                        # 保存图片到临时文件
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        
                        print(f"   💾 保存图片: {image_filename} ({len(image_data)} 字节)")
                        
                        # 上传到 MinIO
                        minio_object_name = f"images/{doc_id}/{image_filename}"
                        image_url = self._upload_image_to_minio(image_path, minio_object_name)
                        
                        # 记录映射关系，包含题注信息
                        # 使用图片索引作为原始引用
                        original_ref = f"image_{i}"
                        if hasattr(picture, 'prov') and picture.prov:
                            original_ref = str(picture.prov)
                        elif hasattr(picture, 'id') and picture.id:
                            original_ref = str(picture.id)
                        
                        # 将题注信息也存储在映射中
                        final_caption = caption if caption else '图片'
                        image_mapping[original_ref] = {
                            'url': image_url,
                            'caption': final_caption
                        }
                        
                        print(f"   ✅ 图片映射: {original_ref} -> {image_url} (题注: {final_caption})")
                        
                    except Exception as e:
                        print(f"   ❌ 处理图片 {i} 时出错: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
            else:
                print("📷 文档中没有找到图片")
        
        except Exception as e:
            print(f"❌ 提取图片时出错: {e}")
            import traceback
            traceback.print_exc()
        
        return image_mapping
    
    def _get_image_extension(self, picture) -> str:
        """
        获取图片扩展名
        
        Args:
            picture: Docling 图片对象
            
        Returns:
            str: 图片扩展名
        """
        # 尝试从图片对象获取格式信息
        if hasattr(picture, 'format') and picture.format:
            return picture.format.lower()
        
        # 从图片数据判断格式
        try:
            if hasattr(picture, 'image'):
                image_data = picture.image
            elif hasattr(picture, 'data'):
                image_data = picture.data
            else:
                return 'png'  # 默认 PNG
            
            # 检查图片数据类型
            if isinstance(image_data, bytes):
                if image_data.startswith(b'\x89PNG'):
                    return 'png'
                elif image_data.startswith(b'\xff\xd8'):
                    return 'jpg'
                elif image_data.startswith(b'GIF'):
                    return 'gif'
                elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:12]:
                    return 'webp'
                else:
                    return 'png'  # 默认 PNG
            else:
                return 'png'  # 默认 PNG
                
        except Exception as e:
            print(f"⚠️ 获取图片扩展名时出错: {e}")
            return 'png'  # 默认 PNG
    
    def _replace_images_in_markdown(self, markdown_text: str, image_mapping: Dict[str, Dict[str, str]]) -> str:
        """
        替换 Markdown 中的图片链接，使用检测到的题注作为 alt 文本
        
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
        # 我们需要按顺序替换这些注释
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
                
                # 创建 Markdown 图片语法，使用题注作为 alt 文本
                img_markdown = f"![{caption}]({image_url})"
                
                # 替换注释
                start, end = match.span()
                markdown_text = markdown_text[:start] + img_markdown + markdown_text[end:]
                
                print(f"   ✅ 替换图片 {len(matches)-i}: <!-- image --> -> {img_markdown}")
            else:
                print(f"   ⚠️ 图片注释多于上传的图片数量")
                break
        
        return markdown_text
    
    def convert_word_url_to_markdown(self, word_url: str) -> str:
        """
        将 Word 文档 URL 转换为 Markdown 文本
        
        Args:
            word_url (str): Word 文档的 URL
            
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
            
            # 下载文件
            file_path = self._download_file_from_url(word_url, temp_dir)
            
            # 调用核心转换方法
            return self._convert_word_file_to_markdown(file_path, temp_dir)
            
        except Exception as e:
            print(f"❌ 转换失败: {e}")
            raise
        
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
                print(f"🧹 清理临时目录: {temp_dir}")

    def convert_local_word_to_markdown(self, word_file_path: str) -> str:
        """
        将本地 Word 文档转换为 Markdown 文本
        
        Args:
            word_file_path (str): 本地 Word 文档路径
            
        Returns:
            str: 转换后的 Markdown 文本
            
        Raises:
            Exception: 转换过程中的各种错误
        """
        if not os.path.exists(word_file_path):
            raise FileNotFoundError(f"文件不存在: {word_file_path}")
        
        temp_dir = None
        try:
            # 创建临时目录用于处理图片
            temp_dir = tempfile.mkdtemp()
            print(f"📁 创建临时目录: {temp_dir}")
            
            # 调用核心转换方法
            return self._convert_word_file_to_markdown(word_file_path, temp_dir)
            
        except Exception as e:
            print(f"❌ 转换失败: {e}")
            raise
        
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
                print(f"🧹 清理临时目录: {temp_dir}")

    def _convert_word_file_to_markdown(self, file_path: str, temp_dir: str) -> str:
        """
        核心转换方法：将 Word 文件转换为 Markdown
        
        Args:
            file_path (str): Word 文件路径
            temp_dir (str): 临时目录
            
        Returns:
            str: 转换后的 Markdown 文本
        """
        # 生成文档 ID
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        
        print(f"🔄 开始转换文档: {file_path}")
        
        # 使用 Docling 转换文档
        result = self.docling_converter.convert(file_path)
        doc = result.document
        
        # 提取并上传图片
        image_mapping = self._extract_and_upload_images(doc, temp_dir, doc_id)
        
        # 导出为 Markdown
        markdown_text = doc.export_to_markdown()
        
        # 替换图片链接
        if image_mapping:
            markdown_text = self._replace_images_in_markdown(markdown_text, image_mapping)
            print(f"✅ 已处理 {len(image_mapping)} 张图片")
        
        print(f"✅ 文档转换完成")
        return markdown_text


# 使用示例
if __name__ == "__main__":
    # 配置 MinIO 参数
    converter = DoclingWordToMarkdownConverter(
        minio_endpoint="localhost:9000",
        minio_access_key="your_access_key",
        minio_secret_key="your_secret_key",
        minio_bucket="documents",
        minio_secure=False,  # 本地开发环境
        image_url_prefix="http://localhost:9000"  # 可选的自定义 URL 前缀
    )
    
    # 转换文档
    try:
        word_url = "https://example.com/document.docx"
        markdown_content = converter.convert_word_url_to_markdown(word_url)
        print("转换后的 Markdown 内容:")
        print(markdown_content)
    except Exception as e:
        print(f"转换失败: {e}")
