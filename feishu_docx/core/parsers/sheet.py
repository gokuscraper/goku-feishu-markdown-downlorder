# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：sheet.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# =====================================================
"""
[INPUT]: 依赖 feishu_docx.core.sdk 的 FeishuSDK
[OUTPUT]: 对外提供 SheetParser 类，将飞书电子表格解析为 Markdown
[POS]: parsers 模块的电子表格解析器
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from typing import Optional

from feishu_docx.core.sdk import FeishuSDK
from feishu_docx.schema.models import SheetValueMode, TableMode
from feishu_docx.utils.progress import ProgressManager


class SheetParser:
    """
    飞书电子表格解析器

    将飞书电子表格解析为 Markdown 格式，每个工作表作为一个章节。
    """

    def __init__(
            self,
            spreadsheet_token: str,
            user_access_token: str,
            table_mode: str = "md",
            sheet_value_mode: str = "display",
            sdk: Optional[FeishuSDK] = None,
            silent: bool = False,
            progress_callback=None,
    ):
        """
        初始化电子表格解析器

        Args:
            spreadsheet_token: 电子表格 token
            user_access_token: 用户访问凭证
            table_mode: 表格输出格式 ("html" 或 "md")
            sheet_value_mode: 单元格值导出模式 ("display" 或 "formula")
            sdk: 可选的 SDK 实例
            silent: 是否静默模式
            progress_callback: 进度回调函数
        """
        self.sdk = sdk or FeishuSDK()
        self.table_mode = TableMode(table_mode)
        self.sheet_value_mode = SheetValueMode(sheet_value_mode)
        self.user_access_token = user_access_token
        self.spreadsheet_token = spreadsheet_token
        self.block_info = {}

        # 进度管理器
        self.pm = ProgressManager(silent=silent, callback=progress_callback)

    def parse(self) -> str:
        """
        解析电子表格为 Markdown

        Returns:
            Markdown 格式的内容，每个工作表作为一个章节
        """
        pm = self.pm

        # 获取工作表列表
        with pm.spinner("获取工作表列表..."):
            sheets = self.sdk.sheet.get_sheet_list(
                spreadsheet_token=self.spreadsheet_token,
                access_token=self.user_access_token,
            )

        total_sheets = len(sheets)
        pm.log(f"  [dim]发现 {total_sheets} 个工作表[/dim]")
        pm.report("发现工作表", total_sheets, total_sheets)

        if total_sheets == 0:
            return ""

        sections = []

        # 解析每个工作表
        with pm.bar("解析工作表...", total_sheets) as advance:
            for sheet in sheets:
                sheet_id = sheet.sheet_id
                sheet_title = sheet.title
                resource_type = sheet.resource_type

                sheet_data = None

                if resource_type == "sheet":
                    sheet_data = self.sdk.sheet.get_sheet(
                        sheet_token=self.spreadsheet_token,
                        sheet_id=sheet_id,
                        access_token=self.user_access_token,
                        table_mode=self.table_mode,
                        value_mode=self.sheet_value_mode,
                    )
                elif resource_type == "bitable":
                    sheet_data = self._parse_bitable_sheet(sheet_id, sheet_title)
                else:
                    pm.log(f"  [yellow]跳过不支持类型: {resource_type}[/yellow]")

                if sheet_data:
                    sections.append(f"# {sheet_title}\n\n{sheet_data}")

                advance()  # noqa

        pm.log(f"  [dim]解析完成 ({len(sections)} 个工作表)[/dim]")
        pm.report("解析完成", len(sections), total_sheets)

        return "\n\n---\n\n".join(sections)

    def _parse_bitable_sheet(self, sheet_id: str, sheet_title: str) -> Optional[str]:
        """解析嵌入的 Bitable 工作表"""
        pm = self.pm

        # 获取 block info
        if not self.block_info:
            blocks = self.sdk.sheet.get_sheet_metadata(
                spreadsheet_token=self.spreadsheet_token,
                access_token=self.user_access_token,
            )
            if blocks:
                for block in blocks:
                    block_info = block.get("blockInfo")
                    if block_info:
                        block_token = block_info.get("blockToken", "")
                        self.block_info[block.get("sheetId")] = block_token

        token = self.block_info.get(sheet_id, "")
        if not token:
            pm.log(f"  [yellow]跳过: {sheet_title}[/yellow]")
            return None

        token_parts = token.split("_")
        if len(token_parts) < 2:
            pm.log(f"  [yellow]跳过无效 token: {sheet_title}[/yellow]")
            return None

        return self.sdk.bitable.get_bitable(
            app_token=token_parts[0],
            table_id=token_parts[1],
            access_token=self.user_access_token,
            table_mode=self.table_mode,
        )
