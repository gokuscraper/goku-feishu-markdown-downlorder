# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：__init__.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# 2026/01/29 14:50   Add TenantAuthenticator
# =====================================================
"""
[INPUT]: None
[OUTPUT]: 对外提供 OAuth2Authenticator, TenantAuthenticator
[POS]: auth 模块入口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from feishu_docx.auth.oauth import OAuth2Authenticator
from feishu_docx.auth.tenant import TenantAuthenticator

__all__ = ["OAuth2Authenticator", "TenantAuthenticator"]
