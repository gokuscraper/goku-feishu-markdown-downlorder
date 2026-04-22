# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：sdk.py
# @Date   ：2025/01/01 00:00
# @Author ：leemysw
# 2025/01/01 00:00   Create
# 2026/01/29 15:25   Refactor - 拆分为 sdk/ 模块
# =====================================================
"""
[INPUT]: 依赖 sdk/ 模块
[OUTPUT]: 对外提供 FeishuSDK（兼容导入）
[POS]: 兼容层，保持原有导入路径可用
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md

Note:
    此文件为兼容层，实际实现已拆分至 sdk/ 目录。
    建议使用: from feishu_docx.core.sdk import FeishuSDK
"""

# 从拆分后的模块导入（保持兼容性）
from feishu_docx.core.sdk import FeishuSDK

__all__ = ["FeishuSDK"]
