# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：common.py
# @Date   ：2026/03/11 11:45
# @Author ：leemysw
# 2026/02/01 19:15   Create - 从 main.py 拆分
# 2026/03/11 11:45   Add drive token normalization helpers
# =====================================================
"""
[INPUT]: 依赖 typer, feishu_docx.utils.config, feishu_docx.utils.console
[OUTPUT]: 对外提供 get_credentials, normalize_folder_token, normalize_drive_target, console
[POS]: cli 模块的共享工具函数
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import os
import re
from typing import Optional
from urllib.parse import urlparse

from feishu_docx.utils.config import AppConfig
from feishu_docx.utils.console import get_console

console = get_console()


def get_credentials(
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None,
        auth_mode: Optional[str] = None,
) -> tuple[Optional[str], Optional[str], str]:
    """
    获取凭证（优先级：命令行参数 > 环境变量 > 配置文件）

    Args:
        app_id: 命令行传入的 App ID
        app_secret: 命令行传入的 App Secret
        auth_mode: 命令行传入的认证模式 (tenant/oauth)

    Returns:
        (app_id, app_secret, auth_mode)
        - auth_mode: "tenant" 使用 tenant_access_token，"oauth" 使用 user_access_token
    """
    # 加载配置文件作为 fallback
    config = AppConfig.load()

    # ========================================
    # 1. 确定 app_id (命令行 > 环境变量 > 配置)
    # ========================================
    final_app_id = (
        app_id
        or os.getenv("FEISHU_APP_ID")
        or config.app_id
    )

    # ========================================
    # 2. 确定 app_secret (命令行 > 环境变量 > 配置)
    # ========================================
    final_app_secret = (
        app_secret
        or os.getenv("FEISHU_APP_SECRET")
        or config.app_secret
    )

    # ========================================
    # 3. 确定 auth_mode (命令行 > 环境变量 > 配置 > 默认 tenant)
    # ========================================
    final_auth_mode = (
        auth_mode
        or os.getenv("FEISHU_AUTH_MODE")
        or config.auth_mode
        or "tenant"
    )

    # 验证 auth_mode 值
    if final_auth_mode not in ("tenant", "oauth"):
        final_auth_mode = "tenant"

    # 检查凭证完整性
    if final_app_id and final_app_secret:
        return final_app_id, final_app_secret, final_auth_mode

    return None, None, final_auth_mode


def normalize_folder_token(folder: Optional[str]) -> Optional[str]:
    """从 URL 或 token 提取 folder token"""
    if not folder:
        return None
    if re.match(r"^[A-Za-z0-9]+$", folder):
        return folder
    try:
        parsed = urlparse(folder)
        if not parsed.path:
            return folder
        match = re.search(r"/drive/folder/([A-Za-z0-9]+)", parsed.path)
        if match:
            return match.group(1)
    except Exception:
        return folder
    return folder


def normalize_drive_target(value: str, file_type: Optional[str] = None) -> tuple[str, Optional[str]]:
    """从 URL 或 token 提取 drive token 和类型。"""
    parsed_type = file_type
    token = value

    try:
        parsed = urlparse(value)
        path = parsed.path or ""
        patterns = [
            (r"/docx/([A-Za-z0-9]+)", "docx"),
            (r"/docs/([A-Za-z0-9]+)", "doc"),
            (r"/sheet/([A-Za-z0-9]+)", "sheet"),
            (r"/sheets/([A-Za-z0-9]+)", "sheet"),
            (r"/base/([A-Za-z0-9]+)", "bitable"),
            (r"/wiki/([A-Za-z0-9]+)", "wiki"),
            (r"/drive/folder/([A-Za-z0-9]+)", "folder"),
            (r"/file/([A-Za-z0-9]+)", "file"),
        ]
        for pattern, matched_type in patterns:
            match = re.search(pattern, path)
            if match:
                token = match.group(1)
                if parsed_type is None:
                    parsed_type = matched_type
                break
    except Exception:
        return value, parsed_type

    return token, parsed_type
