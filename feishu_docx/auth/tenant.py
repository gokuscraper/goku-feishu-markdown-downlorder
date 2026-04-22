# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：tenant
# @Date   ：2026/2/1 19:03
# @Author ：leemysw
#
# 2026/2/1 19:03   Create
# =====================================================

import json
import time
from pathlib import Path
from typing import Optional

import httpx

from feishu_docx.utils.console import get_console

console = get_console()


# ==============================================================================
# Tenant Access Token 认证器
# ==============================================================================
class TenantAuthenticator:
    """
    飞书 Tenant Access Token 认证器

    使用自建应用的 app_id 和 app_secret 直接获取 tenant_access_token，
    无需用户授权页面，适合 AI Agent 和自动化场景。

    特点：
    - 无需浏览器授权，配置凭证后直接使用
    - Token 有效期 2 小时，剩余 30 分钟内会自动刷新
    - 仅能访问应用被授权的文档（需在飞书开放平台配置权限）

    使用示例：
        auth = TenantAuthenticator(app_id="xxx", app_secret="xxx")
        token = auth.get_token()
    """

    # 飞书 API 端点
    FEISHU_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    LARK_TOKEN_URL = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"

    def __init__(
            self,
            app_id: str,
            app_secret: str,
            cache_dir: Optional[Path] = None,
            is_lark: bool = False,
    ):
        """
        初始化认证器

        Args:
            app_id: 飞书应用 App ID
            app_secret: 飞书应用 App Secret
            cache_dir: Token 缓存目录
            is_lark: 是否使用 Lark (海外版)
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.is_lark = is_lark

        # 选择 API 端点
        self.token_url = self.LARK_TOKEN_URL if is_lark else self.FEISHU_TOKEN_URL

        # Token 缓存
        self.cache_dir = cache_dir or Path.home() / ".feishu-docx"
        self.cache_file = self.cache_dir / "tenant_token.json"
        self._token: Optional[str] = None
        self._expires_at: float = 0

        # HTTP 客户端
        self._client = httpx.Client(timeout=30)

    def get_token(self) -> str:
        """
        获取 tenant_access_token

        优先从缓存加载，如果过期或即将过期（30 分钟内）则重新获取。

        Returns:
            tenant_access_token
        """
        # 尝试从缓存加载
        if self._load_from_cache():
            # 检查是否还有 30 分钟以上有效期
            if time.time() < self._expires_at - 1800:
                return self._token

        # 获取新 Token
        return self._fetch_token()

    def _fetch_token(self) -> str:
        """从飞书 API 获取 tenant_access_token"""
        response = self._client.post(
            self.token_url,
            headers={"Content-Type": "application/json; charset=utf-8"},
            json={
                "app_id": self.app_id,
                "app_secret": self.app_secret,
            },
        )

        data = response.json()

        if data.get("code") != 0:
            raise RuntimeError(f"获取 tenant_access_token 失败: {data.get('msg')}")

        self._token = data["tenant_access_token"]
        self._expires_at = time.time() + data.get("expire", 7200)

        # 保存到缓存
        self._save_to_cache()

        return self._token

    def _load_from_cache(self) -> bool:
        """从缓存加载 Token"""
        if not self.cache_file.exists():
            return False

        try:
            data = json.loads(self.cache_file.read_text())
            self._token = data.get("token")
            self._expires_at = data.get("expires_at", 0)
            return bool(self._token)
        except Exception:  # noqa
            return False

    def _save_to_cache(self):
        """保存 Token 到缓存"""
        if not self._token:
            return

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps({
            "token": self._token,
            "expires_at": self._expires_at,
        }, indent=2))
