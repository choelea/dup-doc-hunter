import re

class MarkdownSlicer:
    def __init__(self, max_chars=2000, add_filename=True):
        """
        Markdown 切片器（支持标题切分、块完整性、文件名/父标题引用）
        :param max_chars: 每片最大字符数
        :param add_filename: 是否在切片开头加入文件名
        """
        self.max_chars = max_chars
        self.add_filename = add_filename

        # 正则匹配
        self.table_line_re = re.compile(r'^\s*\|.*\|\s*$')
        self.image_line_re = re.compile(r'!\[.*\]\(.*\)')
        self.heading_re = re.compile(r'^(#{1,6})\s+(.*)')

    def slice(self, md_text, filename=""):
        lines = md_text.splitlines()
        slices = []
        current_slice = []
        current_len = 0
        parent_title = ""
        current_title = ""

        i = 0
        while i < len(lines):
            line = lines[i]

            heading_match = self.heading_re.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                title_text = heading_match.group(2).strip()

                # 二级标题作为父标题
                if level == 2:
                    parent_title = title_text
                    i += 1
                    continue

                # 遇到三级或以上标题时，先切分当前片
                if current_slice:
                    slice_content = self._build_slice(current_slice, filename, parent_title)
                    slices.append(slice_content)
                    current_slice = []
                    current_len = 0

                current_title = title_text
                current_slice.append(line + "\n")
                current_len += len(line) + 1
                i += 1
                continue

            # 表格连续行
            if self.table_line_re.match(line):
                block_lines = []
                while i < len(lines) and self.table_line_re.match(lines[i]):
                    block_lines.append(lines[i])
                    i += 1
                block_text = "\n".join(block_lines) + "\n"
            # 图片段落
            elif self.image_line_re.match(line):
                block_text = line + "\n"
                i += 1
            # 普通段落
            else:
                block_text = line + "\n"
                i += 1

            # 超长切片判断
            if current_len + len(block_text) > self.max_chars and current_slice:
                slice_content = self._build_slice(current_slice, filename, parent_title)
                slices.append(slice_content)
                current_slice = []
                current_len = 0

            # 块本身太大，单独切片
            if len(block_text) > self.max_chars:
                slice_content = self._build_slice([block_text], filename, parent_title)
                slices.append(slice_content)
                continue

            current_slice.append(block_text)
            current_len += len(block_text)

        # 最后一片
        if current_slice:
            slice_content = self._build_slice(current_slice, filename, parent_title)
            slices.append(slice_content)

        return slices

    def _build_slice(self, lines, filename, parent_title):
        header_lines = []
        if self.add_filename and filename:
            header_lines.append(f"> {filename}")
        if parent_title:
            header_lines.append(f"> {parent_title}")
        # 空行分隔引用和内容
        header_lines.append("")
        return "\n".join(header_lines + lines)


# ================= 使用示例 =================
if __name__ == "__main__":
    with open("output/sample.md", "r", encoding="utf-8") as f:
        md_text = f.read()

    slicer = MarkdownSlicer(max_chars=1000, add_filename=True)
    md_slices = slicer.slice(md_text, filename="sample.md")

    for idx, s in enumerate(md_slices, 1):
        print(f"==== 切片 {idx} ====")
        print(s)
        print("\n\n")