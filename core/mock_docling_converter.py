import os
import uuid
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Union
import re

from docling.document_converter import DocumentConverter


class MockDoclingWordToMarkdownConverter:
    """
    DoclingWordToMarkdownConverter 的模拟版本
    用于在没有 MinIO 服务的情况下测试核心转换功能
    图片会保存到本地目录而不是上传到对象存储
    """
    
    def __init__(
        self,
        local_image_dir: str = "images",
        image_url_prefix: str = "./images"
    ):
        """
        初始化模拟转换器
        
        Args:
            local_image_dir (str): 本地图片保存目录
            image_url_prefix (str): 图片 URL 前缀
        """
        self.local_image_dir = local_image_dir
        self.image_url_prefix = image_url_prefix
        
        # 初始化 Docling 转换器
        self.docling_converter = DocumentConverter()
        
        # 确保图片目录存在
        os.makedirs(local_image_dir, exist_ok=True)
        print(f"✅ 本地图片目录: {local_image_dir}")
    
    def _save_image_locally(self, image_data: bytes, image_filename: str) -> str:
        """
        保存图片到本地目录
        
        Args:
            image_data (bytes): 图片数据
            image_filename (str): 图片文件名
            
        Returns:
            str: 图片的访问路径
        """
        try:
            image_path = os.path.join(self.local_image_dir, image_filename)
            
            # 创建子目录（如果需要）
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            
            # 保存图片
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            # 生成访问 URL
            image_url = f"{self.image_url_prefix}/{image_filename}"
            
            print(f"✅ 图片保存成功: {image_filename} -> {image_url}")
            return image_url
            
        except Exception as e:
            print(f"❌ 图片保存失败: {e}")
            raise
    
    def _extract_and_save_images_locally(self, doc, doc_id: str) -> Dict[str, str]:
        """
        提取文档中的图片并保存到本地
        
        Args:
            doc: Docling 文档对象
            doc_id (str): 文档 ID
            
        Returns:
            Dict[str, str]: 图片路径映射表 {原始路径: 本地URL}
        """
        image_mapping = {}
        
        try:
            print(f"🔍 开始提取图片，文档ID: {doc_id}")
            
            # 从文档中提取图片
            if hasattr(doc, 'pictures') and doc.pictures:
                print(f"📸 发现 {len(doc.pictures)} 张图片")
                
                for i, picture in enumerate(doc.pictures):
                    try:
                        print(f"🔄 处理图片 {i+1}/{len(doc.pictures)}")
                        
                        # 获取图片数据
                        image_data = None
                        if hasattr(picture, 'image'):
                            image_data = picture.image
                        elif hasattr(picture, 'data'):
                            image_data = picture.data
                        else:
                            print(f"⚠️ 无法获取图片 {i} 的数据")
                            continue
                        
                        # 生成图片文件名
                        image_ext = self._get_image_extension(image_data)
                        image_filename = f"{doc_id}/image_{i:03d}.{image_ext}"
                        
                        # 保存图片到本地
                        image_url = self._save_image_locally(image_data, image_filename)
                        
                        # 记录映射关系
                        # 尝试获取图片的原始引用
                        original_ref = self._get_picture_reference(picture, i)
                        image_mapping[original_ref] = image_url
                        
                        print(f"✅ 图片 {i+1} 处理完成: {original_ref} -> {image_url}")
                        
                    except Exception as e:
                        print(f"⚠️ 处理图片 {i} 时出错: {e}")
                        continue
            else:
                print("📷 文档中没有发现图片")
        
        except Exception as e:
            print(f"⚠️ 提取图片时出错: {e}")
        
        print(f"🎯 图片提取完成，共处理 {len(image_mapping)} 张图片")
        return image_mapping
    
    def _get_picture_reference(self, picture, index: int) -> str:
        """
        获取图片的原始引用
        
        Args:
            picture: Docling 图片对象
            index (int): 图片索引
            
        Returns:
            str: 图片引用标识
        """
        # 尝试从图片对象获取各种可能的引用信息
        possible_refs = []
        
        if hasattr(picture, 'prov'):
            possible_refs.append(str(picture.prov))
        if hasattr(picture, 'name'):
            possible_refs.append(str(picture.name))
        if hasattr(picture, 'id'):
            possible_refs.append(str(picture.id))
        if hasattr(picture, 'path'):
            possible_refs.append(str(picture.path))
        if hasattr(picture, 'bbox'):
            possible_refs.append(f"bbox_{picture.bbox}")
        
        # 如果有引用信息，使用第一个
        if possible_refs:
            return possible_refs[0]
        
        # 否则使用索引
        return f"image_{index}"
    
    def _get_image_extension(self, image_data: bytes) -> str:
        """
        根据图片数据判断图片格式
        
        Args:
            image_data (bytes): 图片数据
            
        Returns:
            str: 图片扩展名
        """
        if image_data.startswith(b'\x89PNG'):
            return 'png'
        elif image_data.startswith(b'\xff\xd8'):
            return 'jpg'
        elif image_data.startswith(b'GIF'):
            return 'gif'
        elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:20]:
            return 'webp'
        else:
            return 'png'  # 默认 PNG
    
    def _replace_images_in_markdown(self, markdown_text: str, image_mapping: Dict[str, str]) -> str:
        """
        替换 Markdown 中的图片链接
        
        Args:
            markdown_text (str): 原始 Markdown 文本
            image_mapping (Dict[str, str]): 图片路径映射表
            
        Returns:
            str: 替换后的 Markdown 文本
        """
        if not image_mapping:
            return markdown_text
        
        print(f"🔄 开始替换 Markdown 中的图片链接")
        original_text = markdown_text
        
        # 替换图片链接
        for original_ref, local_url in image_mapping.items():
            # 匹配各种可能的图片引用格式
            patterns = [
                rf'!\[([^\]]*)\]\([^)]*{re.escape(str(original_ref))}[^)]*\)',  # ![alt](path)
                rf'<img[^>]*src=["\'][^"\']*{re.escape(str(original_ref))}[^"\']*["\'][^>]*>',  # <img src="path">
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, markdown_text)
                if matches:
                    print(f"🎯 找到图片引用: {original_ref} (匹配 {len(matches)} 次)")
                    
                    def replace_func(match):
                        if match.group().startswith('!['):
                            alt_text = re.search(r'!\[([^\]]*)\]', match.group())
                            alt = alt_text.group(1) if alt_text else f"图片 {original_ref}"
                            return f"![{alt}]({local_url})"
                        elif match.group().startswith('<img'):
                            return re.sub(r'src=["\'][^"\']*["\']', f'src="{local_url}"', match.group())
                        else:
                            return local_url
                    
                    markdown_text = re.sub(pattern, replace_func, markdown_text)
        
        # 如果没有找到明确的引用，尝试通用替换
        if markdown_text == original_text and image_mapping:
            print("🔍 尝试通用图片引用替换")
            # 查找所有图片标记并按顺序替换
            img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            matches = list(re.finditer(img_pattern, markdown_text))
            
            if matches and len(matches) <= len(image_mapping):
                image_urls = list(image_mapping.values())
                for i, match in enumerate(matches):
                    if i < len(image_urls):
                        alt_text = match.group(1) or f"图片 {i+1}"
                        new_img = f"![{alt_text}]({image_urls[i]})"
                        markdown_text = markdown_text.replace(match.group(0), new_img)
                        print(f"✅ 替换图片 {i+1}: {match.group(2)} -> {image_urls[i]}")
        
        return markdown_text
    
    def convert_local_word_to_markdown(self, word_file_path: str) -> str:
        """
        将本地 Word 文档转换为 Markdown 文本
        
        Args:
            word_file_path (str): 本地 Word 文档路径
            
        Returns:
            str: 转换后的 Markdown 文本
        """
        if not os.path.exists(word_file_path):
            raise FileNotFoundError(f"文件不存在: {word_file_path}")
        
        try:
            # 生成文档 ID
            doc_id = f"doc_{uuid.uuid4().hex[:8]}"
            
            print(f"🔄 开始转换文档: {word_file_path}")
            print(f"📋 文档ID: {doc_id}")
            
            # 使用 Docling 转换文档
            result = self.docling_converter.convert(word_file_path)
            doc = result.document
            
            # 提取并保存图片到本地
            image_mapping = self._extract_and_save_images_locally(doc, doc_id)
            
            # 导出为 Markdown
            markdown_text = doc.export_to_markdown()
            
            # 替换图片链接
            if image_mapping:
                markdown_text = self._replace_images_in_markdown(markdown_text, image_mapping)
                print(f"✅ 已处理 {len(image_mapping)} 张图片")
            
            print(f"✅ 文档转换完成")
            return markdown_text
            
        except Exception as e:
            print(f"❌ 转换失败: {e}")
            raise


# 使用示例
if __name__ == "__main__":
    # 创建模拟转换器
    converter = MockDoclingWordToMarkdownConverter(
        local_image_dir="output/images",
        image_url_prefix="./images"
    )
    
    # 测试转换
    test_file = "input/sample.docx"
    if os.path.exists(test_file):
        try:
            markdown_content = converter.convert_local_word_to_markdown(test_file)
            
            # 保存结果
            output_file = "output/test_mock_converter.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✅ 转换完成: {output_file}")
        except Exception as e:
            print(f"❌ 转换失败: {e}")
    else:
        print(f"❌ 测试文件不存在: {test_file}")
