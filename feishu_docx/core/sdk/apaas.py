# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：apaas.py
# @Date   ：2026/01/29 15:22
# @Author ：leemysw
# 2026/02/01 18:30   Refactor - 组合模式重构
# =====================================================
"""
[INPUT]: 依赖 base.py, lark_oapi
[OUTPUT]: 对外提供 APaaSAPI
[POS]: SDK APaaS 数据平台相关 API
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
from typing import List, Optional

import lark_oapi as lark
from lark_oapi.core import BaseResponse

from feishu_docx.utils.console import get_console
from .base import SubModule

console = get_console()


class APaaSAPI(SubModule):
    """APaaS 数据平台 API"""

    def get_workspace_tables(
            self,
            workspace_id: str,
            access_token: str,
            page_size: int = 10,
            page_token: Optional[str] = None,
    ) -> Optional[dict]:
        """获取工作空间下的数据表列表"""
        request = (
            lark.BaseRequest.builder()
            .http_method(lark.HttpMethod.GET)
            .uri(f"/open-apis/apaas/v1/workspaces/{workspace_id}/tables")
            .token_types({self._get_token_type()})
            .build()
        )

        request.add_query("page_size", str(page_size))
        if page_token:
            request.add_query("page_token", page_token)

        option = self._build_option(access_token)
        response: BaseResponse = self.client.request(request, option)

        if not response.success():
            self._log_error("apaas.v1.workspaces.tables.list", response)
            return None

        try:
            content = response.raw.content.decode("utf-8")
            resp_json = json.loads(content)
            return resp_json.get("data", {})
        except Exception as e:
            console.print(f"[red]解析工作空间数据表失败: {e}[/red]")
            return None

    def get_all_workspace_tables(self, workspace_id: str, access_token: str) -> List[dict]:
        """获取工作空间下的所有数据表"""
        all_tables = []
        page_token = None
        has_more = True

        while has_more:
            result = self.get_workspace_tables(
                workspace_id=workspace_id,
                access_token=access_token,
                page_token=page_token,
            )
            if not result:
                break

            all_tables.extend(result.get("items", []))
            has_more = result.get("has_more", False)
            page_token = result.get("page_token")

        return all_tables
