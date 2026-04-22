# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：__init__.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# =====================================================
"""
[INPUT]: None
[OUTPUT]: 对外提供文档、电子表格、多维表格解析器
[POS]: parsers 模块入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from feishu_docx.core.parsers.document import DocumentParser
from feishu_docx.core.parsers.sheet import SheetParser
from feishu_docx.core.parsers.bitable import BitableParser

__all__ = ["DocumentParser", "SheetParser", "BitableParser"]
