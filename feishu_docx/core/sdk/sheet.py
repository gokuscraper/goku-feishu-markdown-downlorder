# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：sheet.py
# @Date   ：2026/01/29 15:18
# @Author ：leemysw
# 2026/02/01 18:40   Refactor - 组合模式重构
# =====================================================
"""
[INPUT]: 依赖 base.py, lark_oapi
[OUTPUT]: 对外提供 SheetAPI
[POS]: SDK 电子表格 API
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import json
from typing import List, Optional

import lark_oapi as lark
from lark_oapi.api.sheets.v3 import (
    QuerySpreadsheetSheetRequest,
    QuerySpreadsheetSheetResponse,
    Sheet,
)
from lark_oapi.core import BaseResponse

from feishu_docx.schema.models import SheetValueMode, TableMode
from feishu_docx.utils.console import get_console
from feishu_docx.utils.render_table import convert_to_html, convert_to_markdown
from .base import SubModule

console = get_console()


class SheetAPI(SubModule):
    """电子表格 API"""

    _DATE_TIME_RENDER_OPTION = "FormattedString"
    _VALUE_RENDER_OPTIONS = {
        SheetValueMode.DISPLAY: "FormattedValue",
        SheetValueMode.FORMULA: "Formula",
    }

    def get_spreadsheet_info(self, spreadsheet_token: str, access_token: str) -> dict:
        """获取电子表格基本信息"""
        from lark_oapi.api.sheets.v3 import GetSpreadsheetRequest, GetSpreadsheetResponse

        request = GetSpreadsheetRequest.builder().spreadsheet_token(spreadsheet_token).build()
        option = self._build_option(access_token)
        response: GetSpreadsheetResponse = self.client.sheets.v3.spreadsheet.get(request, option)

        if not response.success():
            self._log_error("sheets.v3.spreadsheet.get", response)
            return {"spreadsheet_token": spreadsheet_token, "title": spreadsheet_token}

        sheet = response.data.spreadsheet
        return {
            "spreadsheet_token": sheet.token,
            "title": sheet.title or spreadsheet_token,
        }

    def get_sheet_list(self, spreadsheet_token: str, access_token: str) -> Optional[List[Sheet]]:
        """获取电子表格的所有工作表"""
        request = QuerySpreadsheetSheetRequest.builder().spreadsheet_token(spreadsheet_token).build()
        option = self._build_option(access_token)
        response: QuerySpreadsheetSheetResponse = self.client.sheets.v3.spreadsheet_sheet.query(request, option)

        if not response.success():
            self._log_error("sheets.v3.spreadsheet_sheet.query", response)
            raise RuntimeError("获取工作表列表失败")

        return response.data.sheets

    def get_sheet_metadata(self, spreadsheet_token: str, access_token: str) -> Optional[list]:
        """获取电子表格元数据"""
        request = (
            lark.BaseRequest.builder()
            .http_method(lark.HttpMethod.GET)
            .uri(f"/open-apis/sheets/v2/spreadsheets/{spreadsheet_token}/metainfo")
            .token_types({self._get_token_type()})
            .build()
        )
        option = self._build_option(access_token)
        response: BaseResponse = self.client.request(request, option)

        if not response.success():
            self._log_error("sheets.v2.metainfo", response)
            return None

        try:
            content = response.raw.content.decode("utf-8")
            resp_json = json.loads(content)
            return resp_json.get("data", {}).get("sheets", [])
        except Exception as e:
            console.print(f"[red]解析工作表元数据失败: {e}[/red]")
            return None

    def get_sheet(
            self,
            sheet_token: str,
            sheet_id: str,
            access_token: str,
            table_mode: TableMode,
            value_mode: SheetValueMode = SheetValueMode.DISPLAY,
    ) -> Optional[str]:
        """获取电子表格数据并转换为 Markdown/HTML"""
        request = self._build_sheet_values_request(sheet_token, sheet_id, value_mode)
        option = self._build_option(access_token)
        response: BaseResponse = self.client.request(request, option)

        if not response.success():
            self._log_error("sheets.v2.values", response)
            return None

        try:
            content = response.raw.content.decode("utf-8")
            resp_json = json.loads(content)
            values = resp_json.get("data", {}).get("valueRange", {}).get("values", [])

            if not values:
                return ""

            if table_mode == TableMode.MARKDOWN:
                return convert_to_markdown(values)
            else:
                return convert_to_html(values)

        except Exception as e:
            console.print(f"[red]解析工作表数据失败: {e}[/red]")
            return None

    def _build_sheet_values_request(
            self,
            sheet_token: str,
            sheet_id: str,
            value_mode: SheetValueMode,
    ) -> lark.BaseRequest:
        """构建工作表 values 请求"""
        request = (
            lark.BaseRequest.builder()
            .http_method(lark.HttpMethod.GET)
            .uri(f"/open-apis/sheets/v2/spreadsheets/{sheet_token}/values/{sheet_id}")
            .token_types({self._get_token_type()})
            .build()
        )
        request.add_query("valueRenderOption", self._VALUE_RENDER_OPTIONS[value_mode])
        request.add_query("dateTimeRenderOption", self._DATE_TIME_RENDER_OPTION)
        return request
