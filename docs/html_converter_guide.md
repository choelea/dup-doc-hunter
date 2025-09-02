# DoclingHtmlToMarkdownConverter 使用指南

## 概述

`DoclingHtmlToMarkdownConverter` 是一个功能强大的 HTML 到 Markdown 转换器，基于 Docling 构建，支持：

- ✅ HTML 内容字符串转换
- ✅ HTML URL 页面转换  
- ✅ 可选的图片处理和 MinIO 存储
- ✅ 智能的内容解析和格式化

## 快速开始

### 基础用法（无图片处理）

```python
from core.docling_html_converter import DoclingHtmlToMarkdownConverter

# 创建转换器实例
converter = DoclingHtmlToMarkdownConverter()

# 方法1: 转换 HTML 内容字符串
html_content = """
<html>
<body>
    <h1>标题</h1>
    <p>这是一段文本</p>
</body>
</html>
"""
markdown_result = converter.convert_html_content_to_markdown(html_content)

# 方法2: 转换 HTML URL
markdown_result = converter.convert_html_url_to_markdown("https://example.com")
```

### 高级用法（带图片处理）

```python
from core.docling_html_converter import DoclingHtmlToMarkdownConverter

# 创建带图片处理的转换器
converter = DoclingHtmlToMarkdownConverter(
    minio_endpoint="10.3.70.127:9000",
    minio_access_key="minioadmin",
    minio_secret_key="minioadmin", 
    minio_bucket="html-images",
    minio_secure=False,
    image_url_prefix="http://10.3.70.127:9000",
    enable_image_processing=True  # 启用图片处理
)

# 转换包含图片的 HTML
markdown_result = converter.convert_html_url_to_markdown("https://example.com")
```

## 参数说明

### 构造函数参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `minio_endpoint` | `Optional[str]` | `None` | MinIO 服务端点 |
| `minio_access_key` | `Optional[str]` | `None` | MinIO 访问密钥 |
| `minio_secret_key` | `Optional[str]` | `None` | MinIO 密钥 |
| `minio_bucket` | `Optional[str]` | `None` | 存储桶名称 |
| `minio_secure` | `bool` | `True` | 是否使用 HTTPS |
| `image_url_prefix` | `Optional[str]` | `None` | 图片 URL 前缀 |
| `enable_image_processing` | `bool` | `False` | 是否启用图片处理 |

### 方法说明

#### `convert_html_url_to_markdown(html_url: str) -> str`

从 HTML URL 转换为 Markdown 文本。

**参数:**
- `html_url`: HTML 页面的 URL

**返回:**
- 转换后的 Markdown 文本

#### `convert_html_content_to_markdown(html_content: str) -> str`

将 HTML 内容字符串转换为 Markdown 文本。

**参数:**
- `html_content`: HTML 内容字符串

**返回:**
- 转换后的 Markdown 文本

## 功能特性

### 1. 智能内容解析

- 自动检测和处理 HTML 编码
- 支持复杂的 HTML 结构
- 保持内容的语义结构

### 2. 图片处理（可选）

- 自动提取 HTML 中的图片
- 上传到 MinIO 对象存储
- 在 Markdown 中插入正确的图片链接

### 3. 错误处理

- 网络请求错误处理
- 编码问题自动解决
- 详细的错误日志

## 使用场景

1. **网页内容抓取**: 将网页内容转换为 Markdown 格式存储
2. **文档迁移**: 从 HTML 格式文档迁移到 Markdown
3. **内容管理**: 处理富文本编辑器生成的 HTML 内容
4. **知识库建设**: 将网页资料整理为 Markdown 文档

## 测试示例

运行测试脚本验证功能：

```bash
cd /Users/joe/codes/gitee/dup-doc-hunter
conda run -n 3.12_dup_doc_hunter python test/test_html_converter.py
```

## 注意事项

1. **网络访问**: URL 转换需要网络连接
2. **MinIO 配置**: 启用图片处理时需要正确配置 MinIO 参数
3. **编码问题**: 自动处理大部分编码问题，但复杂情况可能需要手动调整
4. **图片限制**: 只能处理 Docling 支持的图片格式

## 错误排查

### 常见问题

1. **网络连接失败**
   - 检查 URL 是否可访问
   - 确认网络连接正常

2. **MinIO 连接失败** 
   - 验证 MinIO 服务是否正常运行
   - 检查访问密钥和端点配置

3. **转换质量问题**
   - HTML 结构过于复杂可能影响转换质量
   - 某些 JavaScript 生成的内容可能无法转换
