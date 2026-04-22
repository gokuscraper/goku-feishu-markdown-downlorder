# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：__init__.py
# @Date   ：2026/03/11 11:45
# @Author ：leemysw
# 2026/02/01 18:45   Refactor - 组合模式重构
# 2026/02/04 10:15   Add document domain setter for media fallback
# 2026/03/11 11:45   Add drive file management module
# =====================================================
"""
[INPUT]: 依赖各子模块
[OUTPUT]: 对外提供 FeishuSDK 类
[POS]: SDK 模块入口，使用组合模式组织各功能模块
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from pathlib import Path
from typing import Optional

from .apaas import APaaSAPI
from .base import SDKCore
from .bitable import BitableAPI
from .contact import ContactAPI
from .docx import DocxAPI
from .drive import DriveAPI
from .media import MediaAPI
from .sheet import SheetAPI
from .wiki import WikiAPI

__all__ = ["FeishuSDK"]


class FeishuSDK:
    """
    飞书 API 封装

    使用组合模式组织各功能模块，通过属性访问：
    - sdk.contact - 联系人/用户信息
    - sdk.wiki    - Wiki 知识库
    - sdk.docx    - 云文档 (CRUD)
    - sdk.drive   - 云空间文件管理
    - sdk.media   - 图片/附件/画板
    - sdk.sheet   - 电子表格
    - sdk.bitable - 多维表格
    - sdk.apaas   - APaaS 数据平台

    支持两种 token 类型：
    - tenant: tenant_access_token（默认，无需用户授权）
    - user: user_access_token（需要用户 OAuth 授权）

    Usage:
        sdk = FeishuSDK()
        sdk.wiki.get_node_metadata(node_token, token)
        sdk.docx.create_document(title, token)
    """

    def __init__(self, temp_dir: Optional[Path] = None, token_type: str = "tenant"):
        """
        初始化 SDK

        Args:
            temp_dir: 临时文件存储目录，默认使用系统临时目录
            token_type: 凭证类型 "tenant" (默认) 或 "user"
        """
        self._core = SDKCore(temp_dir=temp_dir, token_type=token_type)

        # 延迟初始化子模块
        self._contact: Optional[ContactAPI] = None
        self._wiki: Optional[WikiAPI] = None
        self._docx: Optional[DocxAPI] = None
        self._drive: Optional[DriveAPI] = None
        self._media: Optional[MediaAPI] = None
        self._sheet: Optional[SheetAPI] = None
        self._bitable: Optional[BitableAPI] = None
        self._apaas: Optional[APaaSAPI] = None

    @property
    def token_type(self) -> str:
        return self._core.token_type

    @property
    def temp_dir(self) -> Path:
        return self._core.temp_dir

    @temp_dir.setter
    def temp_dir(self, value: Path) -> None:
        self._core.temp_dir = value

    @property
    def client(self):
        return self._core.client

    def set_document_domain(self, domain: Optional[str]) -> None:
        """设置当前文档域名（用于图片降级下载）"""
        self._core.document_domain = domain

    def set_document_url(self, url: Optional[str]) -> None:
        """设置当前文档 URL（用于匿名会话预热下载）"""
        self._core.document_url = url

    # =========================================================================
    # 子模块（延迟初始化）
    # =========================================================================

    @property
    def contact(self) -> ContactAPI:
        if self._contact is None:
            self._contact = ContactAPI(self._core)
        return self._contact

    @property
    def wiki(self) -> WikiAPI:
        if self._wiki is None:
            self._wiki = WikiAPI(self._core)
        return self._wiki

    @property
    def docx(self) -> DocxAPI:
        if self._docx is None:
            self._docx = DocxAPI(self._core)
        return self._docx

    @property
    def drive(self) -> DriveAPI:
        if self._drive is None:
            self._drive = DriveAPI(self._core)
        return self._drive

    @property
    def media(self) -> MediaAPI:
        if self._media is None:
            self._media = MediaAPI(self._core)
        return self._media

    @property
    def sheet(self) -> SheetAPI:
        if self._sheet is None:
            self._sheet = SheetAPI(self._core)
        return self._sheet

    @property
    def bitable(self) -> BitableAPI:
        if self._bitable is None:
            self._bitable = BitableAPI(self._core)
        return self._bitable

    @property
    def apaas(self) -> APaaSAPI:
        if self._apaas is None:
            self._apaas = APaaSAPI(self._core)
        return self._apaas

    # =========================================================================
    # 便捷方法（保持向后兼容）
    # =========================================================================

    def get_user_name(self, user_id: str, access_token: str) -> str:
        """获取用户名称（兼容旧 API）"""
        return self.contact.get_user_name(user_id, access_token)

    def get_wiki_node_metadata(self, node_token: str, access_token: str):
        """获取知识库节点元数据（兼容旧 API）"""
        return self.wiki.get_node_metadata(node_token, access_token)

    def get_document_info(self, document_id: str, access_token: str) -> dict:
        """获取云文档基本信息（兼容旧 API）"""
        return self.docx.get_document_info(document_id, access_token)

    def get_document_block_list(self, document_id: str, access_token: str):
        """获取文档所有 Block（兼容旧 API）"""
        return self.docx.get_block_list(document_id, access_token)

    def get_image(self, file_token: str, access_token: str):
        """下载云文档中的图片（兼容旧 API）"""
        return self.media.get_image(file_token, access_token)

    def get_whiteboard(self, whiteboard_id: str, access_token: str):
        """导出画板为图片（兼容旧 API）"""
        return self.media.get_whiteboard(whiteboard_id, access_token)

    def get_spreadsheet_info(self, spreadsheet_token: str, access_token: str) -> dict:
        """获取电子表格基本信息（兼容旧 API）"""
        return self.sheet.get_spreadsheet_info(spreadsheet_token, access_token)

    def get_sheet_list(self, spreadsheet_token: str, access_token: str):
        """获取电子表格的所有工作表（兼容旧 API）"""
        return self.sheet.get_sheet_list(spreadsheet_token, access_token)

    def get_bitable_info(self, app_token: str, access_token: str) -> dict:
        """获取多维表格基本信息（兼容旧 API）"""
        return self.bitable.get_bitable_info(app_token, access_token)

    def get_bitable_table_list(self, app_token: str, access_token: str):
        """获取多维表格的所有数据表（兼容旧 API）"""
        return self.bitable.get_table_list(app_token, access_token)
