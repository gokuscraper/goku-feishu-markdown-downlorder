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
[OUTPUT]: 对外提供 FeishuDocxApp
[POS]: tui 模块入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from feishu_docx.tui.app import FeishuDocxApp

__all__ = ["FeishuDocxApp"]
