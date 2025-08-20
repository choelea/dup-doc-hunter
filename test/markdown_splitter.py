import re


class MarkdownSlicer:
    def __init__(self, max_chars=2000, add_filename=True):
        """
        Markdown 切片器（支持标题切分、块完整性、文件名/父标题引用）

        功能：
        1. 遇到有内容的标题强制切片，保证每个标题及其内容独立
        2. 表格和图片块完整性保持，不拆分
        3. 支持超长块单独切片
        4. 可在切片开头加入文件名、父标题、当前标题引用信息

        :param max_chars: 每片最大字符数，超过则切片
        :param add_filename: 是否在切片开头加入文件名引用
        """
        self.max_chars = max_chars
        self.add_filename = add_filename

        # 正则匹配
        self.table_line_re = re.compile(r'^\s*\|.*\|\s*$')  # Markdown 表格行
        self.image_line_re = re.compile(r'!\[.*\]\(.*\)')  # Markdown 图片行
        self.heading_re = re.compile(r'^(#{1,6})\s+(.*)')  # Markdown 标题行（#）

    def slice(self, md_text, filename=""):
        """
        将 Markdown 文本切片

        :param md_text: Markdown 文本内容
        :param filename: 文件名（可选，用于切片引用）
        :return: 切片列表，每个元素是一段 Markdown 文本
        """
        lines = md_text.splitlines()
        slices = []  # 存储切片结果
        current_slice = []  # 当前累积切片内容
        current_len = 0  # 当前切片长度
        parent_title = ""  # 当前父级标题（二级标题）
        current_title = ""  # 当前标题（三级及以上标题）

        i = 0
        while i < len(lines):
            line = lines[i]

            # 检查是否标题行
            heading_match = self.heading_re.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                title_text = heading_match.group(2).strip()

                # 二级标题作为父标题，用于切片引用
                if level == 2:
                    parent_title = title_text
                    i += 1
                    continue

                # 遇到三级及以上标题时，先切分当前片
                if current_slice:
                    slice_content = self._build_slice(current_slice, filename, parent_title, current_title)
                    slices.append(slice_content)
                    current_slice = []
                    current_len = 0

                current_title = title_text
                # 将标题加入新切片开头
                current_slice.append(line + "\n")
                current_len += len(line) + 1
                i += 1
                continue

            # 处理表格块：连续的表格行归为一个块
            if self.table_line_re.match(line):
                block_lines = []
                while i < len(lines) and self.table_line_re.match(lines[i]):
                    block_lines.append(lines[i])
                    i += 1
                block_text = "\n".join(block_lines) + "\n"

            # 处理图片行
            elif self.image_line_re.match(line):
                block_text = line + "\n"
                i += 1

            # 普通段落
            else:
                block_text = line + "\n"
                i += 1

            # 如果当前切片加上本段超过 max_chars，先切片
            if current_len + len(block_text) > self.max_chars and current_slice:
                slice_content = self._build_slice(current_slice, filename, parent_title, current_title)
                slices.append(slice_content)
                current_slice = []
                current_len = 0

            # 如果块本身长度超过 max_chars，单独切片（保证块完整性）
            if len(block_text) > self.max_chars:
                slice_content = self._build_slice([block_text], filename, parent_title, current_title)
                slices.append(slice_content)
                continue

            # 将当前块加入切片
            current_slice.append(block_text)
            current_len += len(block_text)

        # 最后一片
        if current_slice:
            slice_content = self._build_slice(current_slice, filename, parent_title, current_title)
            slices.append(slice_content)

        return slices

    def _build_slice(self, lines, filename, parent_title, current_title):
        """
        构建切片文本，添加文件名、父标题、当前标题引用
        使用 Markdown 引用 '>' 格式

        :param lines: 切片内容块
        :param filename: 文件名
        :param parent_title: 父级标题（二级标题）
        :param current_title: 当前标题
        :return: 切片文本
        """
        header_lines = []
        if self.add_filename and filename:
            header_lines.append(f"> 文件名: {filename}")
        if parent_title:
            header_lines.append(f"> 父标题: {parent_title}")
        if current_title:
            header_lines.append(f"> 当前标题: {current_title}")
        # 空行分隔引用和内容
        header_lines.append("")
        return "\n".join(header_lines + lines)


# ================= 使用示例 =================
if __name__ == "__main__":
    # 读取 Markdown 文件
    with open("output/sample.md", "r", encoding="utf-8") as f:
        md_text = f.read()

    # 初始化切片器
    slicer = MarkdownSlicer(max_chars=1000, add_filename=True)
    md_slices = slicer.slice(md_text, filename="sample.md")

    # 打印每片切片
    for idx, s in enumerate(md_slices, 1):
        print(f"==== 切片 {idx} ====")
        print(s)
        print("\n\n")