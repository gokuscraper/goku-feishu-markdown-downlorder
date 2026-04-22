# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：__init__.py
# @Date   ：2026/01/18 15:40
# @Author ：leemysw
# 2026/01/18 15:40   Create
# =====================================================
"""
[INPUT]: 无
[OUTPUT]: 对外提供 MarkdownToBlocks 转换器
[POS]: converters 模块入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from feishu_docx.core.converters.md_to_blocks import MarkdownToBlocks

__all__ = ["MarkdownToBlocks"]
