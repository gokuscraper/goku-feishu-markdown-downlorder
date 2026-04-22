# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：base.py
# @Date   ：2026/01/29 15:10
# @Author ：leemysw
# 2026/01/29 15:10   Create - SDK 基础类
# 2026/02/01 18:30   Refactor - 组合模式重构
# 2026/02/04 10:15   Add document domain storage for media fallback
# 2026/03/30 22:00   Store document url for web-session fallback
# =====================================================
"""
[INPUT]: 依赖 lark_oapi
[OUTPUT]: 对外提供 SDKCore, SubModule
[POS]: SDK 核心类和子模块基类
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import lark_oapi as lark

from feishu_docx.utils.console import get_console

if TYPE_CHECKING:
    from lark_oapi import Client

console = get_console()


class SDKCore:
    """
    SDK 核心类

    持有共享资源：lark client、临时目录、token 类型
    子模块通过组合方式访问这些资源
    """

    def __init__(self, temp_dir: Optional[Path] = None, token_type: str = "tenant"):
        """
        初始化 SDK 核心

        Args:
            temp_dir: 临时文件存储目录
            token_type: 凭证类型 "tenant" (默认) 或 "user"
        """
        self.client: Client = (
            lark.Client.builder()
            .enable_set_token(True)
            .log_level(lark.LogLevel.ERROR)
            .build()
        )
        self.temp_dir = temp_dir or Path(tempfile.gettempdir()) / "feishu_docx"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.token_type = token_type
        self.document_domain: Optional[str] = None
        self.document_url: Optional[str] = None

    def build_option(self, access_token: str) -> lark.RequestOption:
        """构建请求选项（根据 token_type 自动选择）"""
        builder = lark.RequestOption.builder()
        if self.token_type == "tenant":
            builder.tenant_access_token(access_token)
        else:
            builder.user_access_token(access_token)
        return builder.build()

    @staticmethod
    def log_error(api_name: str, response):
        """统一错误日志"""
        try:
            content = json.loads(response.raw.content)
            formatted = json.dumps(content, indent=2, ensure_ascii=False)
        except Exception:
            formatted = str(response.raw.content) if hasattr(response, 'raw') else ""

        console.print(
            f"[red]API 调用失败: {api_name}[/red]\n"
            f"  code: {response.code}\n"
            f"  msg: {response.msg}\n"
            f"  response: {formatted}"
        )

class SubModule:
    """
    子模块基类

    所有功能模块继承此类，通过 core 访问共享资源
    """

    def __init__(self, core: SDKCore):
        self._core = core

    @property
    def client(self) -> "Client":
        return self._core.client

    @property
    def temp_dir(self) -> Path:
        return self._core.temp_dir

    def _build_option(self, access_token: str) -> lark.RequestOption:
        return self._core.build_option(access_token)

    def _log_error(self, api_name: str, response):
        self._core.log_error(api_name, response)

    def _get_token_type(self) -> lark.AccessTokenType:
        """获取 AccessTokenType 用于 BaseRequest"""
        if self._core.token_type == "tenant":
            return lark.AccessTokenType.TENANT
        return lark.AccessTokenType.USER
