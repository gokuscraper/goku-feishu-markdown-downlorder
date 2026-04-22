# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：constants.py
# @Date   ：2025/01/10 16:30
# @Author ：leemysw
# 2025/01/10 16:30   Create
# =====================================================
"""
[INPUT]: 无
[OUTPUT]: 对外提供 TUI 常量：LOGO, DESCRIPTION, VERSION, AUTHOR, REPO
[POS]: tui 模块的常量定义
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

# ==============================================================================
# ASCII Art Logo
# ==============================================================================
LOGO = r"""
  ╔═╗╔═╗╦╔═╗╦ ╦╦ ╦  ╔╦╗╔═╗╔═╗═╗ ╦
  ╠╣ ║╣ ║╚═╗╠═╣║ ║───║║║ ║║  ╔╩╦╝
  ╚  ╚═╝╩╚═╝╩ ╩╚═╝  ═╩╝╚═╝╚═╝╩ ╚═"""

DESCRIPTION = """飞书/Lark 云文档 → Markdown 导出工具
支持 Docx · Sheet · Bitable · Wiki"""

VERSION = "v0.1.0"
AUTHOR = "leemysw"
REPO = "github.com/leemysw/feishu-docx"
