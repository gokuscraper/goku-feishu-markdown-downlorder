# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：__init__.py
# @Date   ：2026/04/11 20:22
# @Author ：leemysw
# 2025/01/09 18:30   Create
# 2026/04/11 20:22   Release v0.2.5
# =====================================================
"""
[INPUT]: None
[OUTPUT]: 对外提供版本号 __version__ 和主要 API
[POS]: feishu_docx 包入口，是整个项目的对外接口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

# ⚠️ 必须在最顶部，抑制第三方库警告（如 lark_oapi）
import warnings

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*pkg_resources.*")

__version__ = "0.2.5"

from feishu_docx.core.exporter import FeishuExporter

__all__ = ["__version__", "FeishuExporter"]
