# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：bitable.py
# @Date   ：2026/01/29 15:20
# @Author ：leemysw
# 2026/02/01 18:40   Refactor - 组合模式重构
# =====================================================
"""
[INPUT]: 依赖 base.py, lark_oapi
[OUTPUT]: 对外提供 BitableAPI
[POS]: SDK 多维表格 API
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
from datetime import datetime
from typing import Any, List, Optional

from lark_oapi.api.bitable.v1 import (
    AppTable,
    AppTableFieldForList,
    ListAppTableFieldRequest,
    ListAppTableFieldResponse,
    ListAppTableRequest,
    ListAppTableResponse,
    SearchAppTableRecordRequest,
    SearchAppTableRecordRequestBody,
    SearchAppTableRecordResponse,
    GetAppRequest,
    GetAppResponse,
)

from feishu_docx.schema.models import TableMode
from feishu_docx.utils.console import get_console
from feishu_docx.utils.render_table import convert_to_html, convert_to_markdown
from .base import SubModule

console = get_console()


class BitableAPI(SubModule):
    """多维表格 API"""

    def get_bitable_info(self, app_token: str, access_token: str) -> dict:
        """获取多维表格基本信息"""
        request = GetAppRequest.builder().app_token(app_token).build()
        option = self._build_option(access_token)
        response: GetAppResponse = self.client.bitable.v1.app.get(request, option)

        if not response.success():
            self._log_error("bitable.v1.app.get", response)
            return {"app_token": app_token, "title": app_token}

        app = response.data.app
        return {
            "app_token": app.app_token,
            "title": app.name or app_token,
        }

    def get_table_list(self, app_token: str, access_token: str) -> List[AppTable]:
        """获取多维表格的所有数据表"""
        request = ListAppTableRequest.builder().app_token(app_token).page_size(20).build()
        option = self._build_option(access_token)
        response: ListAppTableResponse = self.client.bitable.v1.app_table.list(request, option)

        if not response.success():
            self._log_error("bitable.v1.app_table.list", response)
            raise RuntimeError("获取多维表格列表失败")

        return response.data.items

    def get_bitable(
            self,
            app_token: str,
            table_id: str,
            access_token: str,
            table_mode: TableMode,
            view_id: Optional[str] = None,
    ) -> Optional[str]:
        """获取多维表格数据并转换为 Markdown/HTML"""
        try:
            headers = self._get_headers(app_token, table_id, view_id, access_token)
            if not headers:
                raise RuntimeError(f"多维表格 {app_token}/{table_id} 没有字段")

            records = self._get_records(app_token, table_id, view_id, access_token)

            matrix = [[header.field_name for header in headers]]

            for record in records:
                row_values = []
                fields_data = record.fields
                for header in headers:
                    val = fields_data.get(header.field_name, "")
                    parsed_val = self._parse_field_value(header, val)
                    row_values.append(parsed_val)
                matrix.append(row_values)

            if table_mode == TableMode.MARKDOWN:
                return convert_to_markdown(matrix)
            else:
                return convert_to_html(matrix)

        except Exception as e:
            console.print(f"[red]处理多维表格失败: {e}[/red]")
            return None

    def _get_headers(
            self,
            app_token: str,
            table_id: str,
            view_id: Optional[str],
            access_token: str,
    ) -> Optional[List[AppTableFieldForList]]:
        """获取多维表格字段列表"""
        request = (
            ListAppTableFieldRequest.builder()
            .app_token(app_token)
            .table_id(table_id)
            .page_size(100)
            .build()
        )

        if view_id:
            request.view_id = view_id
            request.add_query("view_id", view_id)

        option = self._build_option(access_token)
        response: ListAppTableFieldResponse = self.client.bitable.v1.app_table_field.list(request, option)

        if not response.success():
            self._log_error("bitable.v1.app_table_field.list", response)
            return []

        return response.data.items

    def _get_records(
            self,
            app_token: str,
            table_id: str,
            view_id: Optional[str],
            access_token: str,
    ) -> List[Any]:
        """获取多维表格所有记录"""
        all_records = []
        page_token = None
        has_more = True

        option = self._build_option(access_token)

        while has_more:
            request = (
                SearchAppTableRecordRequest.builder()
                .app_token(app_token)
                .table_id(table_id)
                .user_id_type("user_id")
                .page_size(100)
                .request_body(SearchAppTableRecordRequestBody.builder().build())
                .build()
            )

            if view_id:
                request.view_id = view_id
                request.add_query("view_id", view_id)

            if page_token:
                request.page_token = page_token
                request.add_query("page_token", page_token)

            response: SearchAppTableRecordResponse = self.client.bitable.v1.app_table_record.search(
                request, option
            )

            if not response.success():
                self._log_error("bitable.v1.app_table_record.search", response)
                return []

            if response.data.items:
                all_records.extend(response.data.items)

            has_more = response.data.has_more
            page_token = response.data.page_token

        return all_records

    @staticmethod
    def _parse_field_value(header: AppTableFieldForList, value: Any) -> str:
        """解析多维表格字段值"""
        if value is None:
            return ""

        if header.ui_type == "DateTime":
            try:
                return datetime.fromtimestamp(value / 1000).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                return str(value)

        def extract_text(data):
            texts = []
            for item in data:
                if isinstance(item, dict):
                    if "text" in item:
                        texts.append(item["text"])
                    elif "name" in item:
                        texts.append(item["name"])
                    elif "url" in item:
                        texts.append(item["url"])
                    elif "full_name" in item:
                        texts.append(item["full_name"])
                    else:
                        texts.append(str(item))
                else:
                    texts.append(str(item))
            return ", ".join(texts)

        if isinstance(value, list):
            return extract_text(value)

        if isinstance(value, dict):
            if "text" in value:
                return value["text"]
            if "name" in value:
                return value["name"]
            if "value" in value:
                return extract_text(value["value"])
            return json.dumps(value, ensure_ascii=False)

        return str(value)
