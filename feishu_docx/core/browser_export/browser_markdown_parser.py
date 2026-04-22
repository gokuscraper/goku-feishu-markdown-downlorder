# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：browser_markdown_parser.py
# @Date   ：2026/03/30 20:25
# @Author ：leemysw
# 2026/03/30 20:25   Create
# =====================================================
"""浏览器块树 Markdown 解析器。"""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import unquote

from feishu_docx.core.browser_export.browser_document_model import BrowserDocumentModel


class BrowserMarkdownParser:
    """浏览器块树转 Markdown。"""

    LIST_TYPES = {"bullet", "ordered", "todo"}
    ASSET_TYPES = {"image", "file", "whiteboard", "diagram"}

    def parse_document(self, model: BrowserDocumentModel) -> str:
        """将浏览器侧抽取的块树渲染为 Markdown。"""
        title = self._clean_text(model.title) or "untitled"
        sections = self._render_blocks(model.root.get("children") or [])
        if not sections:
            return f"# {title}"
        return f"# {title}\n\n{sections}".rstrip()

    def _render_blocks(self, blocks: list[dict[str, Any]], indent: int = 0) -> str:
        sections: list[str] = []
        index = 0

        while index < len(blocks):
            block = blocks[index]
            block_type = block.get("type")

            if block_type in self.LIST_TYPES:
                list_lines: list[str] = []
                while index < len(blocks) and blocks[index].get("type") in self.LIST_TYPES:
                    rendered = self._render_list_item(blocks[index], indent)
                    if rendered:
                        list_lines.append(rendered)
                    index += 1
                if list_lines:
                    sections.append("\n".join(list_lines))
                continue

            rendered = self._render_block(block, indent)
            if rendered:
                sections.append(rendered)
            index += 1

        return "\n\n".join(section for section in sections if section.strip())

    def _render_block(self, block: dict[str, Any], indent: int = 0) -> str:
        block_type = block.get("type") or ""

        if block_type == "divider":
            return " " * indent + "---"

        if block_type.startswith("heading") and block_type[-1].isdigit():
            level = int(block_type[-1])
            if 1 <= level <= 6:
                content = self._render_inline_ops(block)
                return f"{' ' * indent}{'#' * level} {content}".rstrip()

        if block_type in {"text", "heading7", "heading8", "heading9"}:
            content = self._render_inline_ops(block)
            if not content:
                return ""
            return " " * indent + content

        if block_type == "code":
            language = self._clean_text(block.get("language") or "")
            code = self._clean_text(self._zone_all_text(block), keep_newline=True)
            if not code:
                return ""
            return f"{' ' * indent}```{language}\n{code}\n{' ' * indent}```"

        if block_type in {"quote_container", "callout"}:
            parts: list[str] = []
            own = self._render_inline_ops(block)
            if own:
                parts.append(own)
            child_content = self._render_blocks(self._iter_children(block), indent=0)
            if child_content:
                parts.append(child_content)
            if not parts:
                return ""
            content = "\n\n".join(part for part in parts if part.strip())
            return "\n".join(
                f"{' ' * indent}> {line}" if line else f"{' ' * indent}>"
                for line in content.splitlines()
            )

        if block_type == "table":
            return self._render_table(block, indent)

        if block_type == "grid":
            return self._render_blocks(self._iter_children(block), indent)

        if block_type in self.ASSET_TYPES:
            return self._render_asset_block(block, indent)

        if block_type == "iframe":
            iframe = ((block.get("snapshot") or {}).get("iframe") or {})
            url = ((iframe.get("component") or {}).get("url") or "").strip()
            if not url:
                return ""
            return f"{' ' * indent}<iframe src=\"{url}\"></iframe>"

        if block_type == "isv":
            return self._render_isv(block, indent)

        if block_type in {"synced_source", "synced_reference", "grid_column", "table_cell", "page", "view"}:
            return self._render_blocks(self._iter_children(block), indent)

        return self._render_blocks(self._iter_children(block), indent)

    def _render_asset_block(self, block: dict[str, Any], indent: int = 0) -> str:
        block_type = block.get("type") or ""
        asset_url = self._build_asset_url(block)

        if block_type == "file":
            file_data = ((block.get("snapshot") or {}).get("file") or {})
            name = self._clean_text(file_data.get("name") or "附件")
            return f"{' ' * indent}[{name}]({asset_url})".rstrip()

        alt = ""
        if block_type == "image":
            alt = self._clean_text(
                ((block.get("snapshot") or {}).get("image") or {}).get("caption") or ""
            )
        elif block_type == "whiteboard":
            alt = self._clean_text(
                ((block.get("snapshot") or {}).get("whiteboard") or {}).get("caption") or "whiteboard"
            )
        elif block_type == "diagram":
            alt = "diagram"

        return f"{' ' * indent}![{alt}]({asset_url})".rstrip()

    def _render_list_item(self, block: dict[str, Any], indent: int = 0) -> str:
        block_type = block.get("type") or ""
        content = self._render_inline_ops(block)
        marker = "- "

        if block_type == "ordered":
            seq = ((block.get("snapshot") or {}).get("seq") or "1").strip() or "1"
            marker = f"{seq}. " if seq.isdigit() else "1. "
        elif block_type == "todo":
            done = bool((block.get("snapshot") or {}).get("done"))
            marker = "- [x] " if done else "- [ ] "

        first_line = f"{' ' * indent}{marker}{content}".rstrip()
        if not content:
            first_line = f"{' ' * indent}{marker.rstrip()}"

        child_content = self._render_blocks(self._iter_children(block), indent + 4)
        if child_content:
            return f"{first_line}\n{child_content}"
        return first_line

    def _render_table(self, block: dict[str, Any], indent: int = 0) -> str:
        columns = ((block.get("snapshot") or {}).get("columns_id") or [])
        column_count = len(columns)
        if column_count <= 0:
            return self._render_blocks(self._iter_children(block), indent)

        rows: list[list[str]] = []
        current_row: list[str] = []

        for cell in self._iter_children(block):
            current_row.append(self._extract_plain_text(cell))
            if len(current_row) == column_count:
                rows.append(current_row)
                current_row = []

        if current_row:
            current_row.extend([""] * (column_count - len(current_row)))
            rows.append(current_row)

        if not rows:
            return ""

        header = rows[0]
        separators = ["---"] * column_count
        body = rows[1:] if len(rows) > 1 else []
        lines = [
            self._table_line(header, indent),
            self._table_line(separators, indent),
        ]
        lines.extend(self._table_line(row, indent) for row in body)
        return "\n".join(lines)

    def _render_isv(self, block: dict[str, Any], indent: int = 0) -> str:
        snapshot = block.get("snapshot") or {}
        block_type_id = snapshot.get("block_type_id") or ""
        data = snapshot.get("data") or {}

        if block_type_id == "blk_631fefbbae02400430b8f9f4":
            mermaid = self._clean_text((data or {}).get("data") or "", keep_newline=True)
            if mermaid:
                return f"{' ' * indent}```mermaid\n{mermaid}\n{' ' * indent}```"

        if block_type_id == "blk_6358a421bca0001c22536e4c":
            items = data.get("items") or []
            if isinstance(items, list) and items:
                lines = ["timeline"]
                for item in items:
                    time = self._clean_text((item or {}).get("time") or "")
                    title = self._clean_text((item or {}).get("title") or "").replace(":", "：")
                    text = self._clean_text((item or {}).get("text") or "", keep_newline=True)
                    if text:
                        lines.append(f"    {time} : {title} : {text.replace(chr(10), '<br>')}")
                    else:
                        lines.append(f"    {time} : {title}")
                content = "\n".join(lines)
                return f"{' ' * indent}```mermaid\n{content}\n{' ' * indent}```"

        return ""

    def _render_inline_ops(self, block: dict[str, Any]) -> str:
        ops = (((block.get("zone_state") or {}).get("content") or {}).get("ops") or [])
        pieces: list[str] = []
        for op in self._normalize_ops(ops):
            pieces.append(self._render_inline_piece(op.get("insert") or "", op.get("attributes") or {}))
        content = "".join(piece for piece in pieces if piece)
        return self._clean_text(content, keep_newline=True)

    def _normalize_ops(self, ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized_ops: list[dict[str, Any]] = []

        for op in ops:
            insert = op.get("insert") or ""
            attributes = dict(op.get("attributes") or {})

            if attributes.get("fixEnter") is not None:
                continue
            if not attributes and insert == "\n":
                continue

            inline_component = attributes.get("inline-component")
            if inline_component:
                try:
                    component = json.loads(inline_component)
                except json.JSONDecodeError:
                    component = None

                if isinstance(component, dict):
                    component_type = component.get("type")
                    data = component.get("data") or {}
                    if component_type == "mention_doc":
                        attributes["link"] = data.get("raw_url") or attributes.get("link")
                        insert = f"{insert}{data.get('title') or ''}"
                    elif component_type == "user":
                        attributes["mentionUserId"] = data.get("uid") or ""
                        insert = insert or "@mention"

            normalized_ops.append({"insert": insert, "attributes": attributes})

        return normalized_ops

    def _render_inline_piece(self, insert: str, attributes: dict[str, Any]) -> str:
        if attributes.get("mentionUserId") and not insert:
            insert = "@mention"

        equation = self._clean_text(attributes.get("equation") or "", keep_newline=True)
        if equation:
            return f"${equation}$"

        if attributes.get("inlineCode") is not None:
            content = insert.replace("`", "\\`")
            return f"`{content}`"

        text = self._escape_markdown(insert).replace("\n", "  \n")
        if attributes.get("underline") is not None and text:
            text = f"<u>{text}</u>"
        if attributes.get("strikethrough") is not None and text:
            text = f"~~{text}~~"
        if attributes.get("italic") is not None and text:
            text = f"*{text}*"
        if attributes.get("bold") is not None and text:
            text = f"**{text}**"

        link = attributes.get("link")
        if link:
            label = text or self._escape_markdown(unquote(str(link)))
            text = f"[{label}]({unquote(str(link))})"

        return text

    def _extract_plain_text(self, block: dict[str, Any]) -> str:
        block_type = block.get("type") or ""
        text_types = {
            "text", "heading1", "heading2", "heading3", "heading4", "heading5", "heading6",
            "heading7", "heading8", "heading9", "bullet", "ordered", "todo",
        }
        if block_type in text_types:
            content = self._render_inline_ops(block)
            child_texts = [self._extract_plain_text(child) for child in self._iter_children(block)]
            child_texts = [text for text in child_texts if text]
            if child_texts:
                return "\n".join([content] + child_texts if content else child_texts)
            return content

        if block_type == "table_cell":
            texts = [self._extract_plain_text(child) for child in self._iter_children(block)]
            return "<br>".join(text for text in texts if text)

        if block_type in {"image", "whiteboard", "diagram"}:
            return self._clean_text(self._render_asset_block(block))

        if block_type == "file":
            return self._clean_text((((block.get("snapshot") or {}).get("file")) or {}).get("name") or "附件")

        texts = [self._extract_plain_text(child) for child in self._iter_children(block)]
        return "\n".join(text for text in texts if text)

    def _build_asset_url(self, block: dict[str, Any]) -> str:
        block_type = block.get("type") or "asset"
        block_id = block.get("id") or "unknown"
        return f"browser-asset://{block_type}/{block_id}"

    @staticmethod
    def _table_line(cells: list[str], indent: int = 0) -> str:
        normalized = [cell.replace("\n", "<br>").strip() for cell in cells]
        return f"{' ' * indent}| " + " | ".join(normalized) + " |"

    @staticmethod
    def _iter_children(block: dict[str, Any]) -> list[dict[str, Any]]:
        synced_children = block.get("synced_children")
        if isinstance(synced_children, list) and synced_children:
            return synced_children
        children = block.get("children")
        if isinstance(children, list):
            return children
        return []

    @staticmethod
    def _zone_all_text(block: dict[str, Any]) -> str:
        zone_state = block.get("zone_state") or {}
        return zone_state.get("all_text") or ""

    @staticmethod
    def _clean_text(text: str, keep_newline: bool = False) -> str:
        if keep_newline:
            return text.rstrip()
        return text.replace("\r", "").replace("\n", " ").strip()

    @staticmethod
    def _escape_markdown(text: str) -> str:
        if not text:
            return ""
        return re.sub(r"([\\\\`*_{}\\[\\]()#+\\-.!|>])", r"\\\\\1", text)
