# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：browser_document_model.py
# @Date   ：2026/03/30 20:25
# @Author ：leemysw
# 2026/03/30 20:25   Create
# =====================================================
"""浏览器文档模型。"""

from dataclasses import dataclass
from typing import Any


@dataclass
class BrowserDocumentModel:
    """浏览器侧抽取后的文档模型。"""

    title: str
    root: dict[str, Any]
