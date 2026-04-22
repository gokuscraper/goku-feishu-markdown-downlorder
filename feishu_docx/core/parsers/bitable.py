# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：bitable.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# =====================================================
"""
[INPUT]: 依赖 feishu_docx.core.sdk 的 FeishuSDK
[OUTPUT]: 对外提供 BitableParser 类，将飞书多维表格解析为 Markdown
[POS]: parsers 模块的多维表格解析器
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from typing import Optional

from feishu_docx.core.sdk import FeishuSDK
from feishu_docx.schema.models import TableMode
from feishu_docx.utils.progress import ProgressManager


class BitableParser:
    """
    飞书多维表格解析器

    将飞书多维表格解析为 Markdown 格式，每个数据表作为一个章节。
    """

    def __init__(
            self,
            user_access_token: str,
            node_token: Optional[str] = None,
            app_token: Optional[str] = None,
            table_mode: str = "md",
            sdk: Optional[FeishuSDK] = None,
            silent: bool = False,
            progress_callback=None,
    ):
        """
        初始化多维表格解析器

        Args:
            user_access_token: 用户访问凭证
            node_token: 知识库节点 token（二选一）
            app_token: 多维表格 app_token（二选一）
            table_mode: 表格输出格式 ("html" 或 "md")
            sdk: 可选的 SDK 实例
            silent: 是否静默模式
            progress_callback: 进度回调函数
        """
        self.sdk = sdk or FeishuSDK()
        self.table_mode = TableMode(table_mode)
        self.user_access_token = user_access_token
        self.node_token = node_token
        self.app_token = app_token

        # 进度管理器
        self.pm = ProgressManager(silent=silent, callback=progress_callback)

    def _get_app_token(self):
        """获取 app_token"""
        if self.app_token is None:
            if self.node_token is None:
                raise ValueError("需要提供 app_token 或 node_token")

            node_meta = self.sdk.wiki.get_node_metadata(
                node_token=self.node_token,
                access_token=self.user_access_token,
            )
            self.app_token = node_meta.obj_token

    def parse(self) -> str:
        """
        解析多维表格为 Markdown

        Returns:
            Markdown 格式的内容，每个数据表作为一个章节
        """
        pm = self.pm

        self._get_app_token()

        # 获取表格列表
        with pm.spinner("获取数据表列表..."):
            bitables = self.sdk.bitable.get_table_list(
                app_token=self.app_token,
                access_token=self.user_access_token,
            )

        total_tables = len(bitables)
        pm.log(f"  [dim]发现 {total_tables} 个数据表[/dim]")
        pm.report("发现数据表", total_tables, total_tables)

        if total_tables == 0:
            return ""

        sections = []

        # 解析每个数据表
        with pm.bar("解析数据表...", total_tables) as advance:
            for bitable in bitables:
                table_data = self.sdk.bitable.get_bitable(
                    app_token=self.app_token,
                    table_id=bitable.table_id,
                    access_token=self.user_access_token,
                    table_mode=self.table_mode,
                )

                if table_data:
                    sections.append(f"# {bitable.name}\n\n{table_data}")

                advance()  # noqa

        pm.log(f"  [dim]解析完成 ({len(sections)} 个数据表)[/dim]")
        pm.report("解析完成 ({len(sections)} 个数据表)", len(sections), total_tables)

        return "\n\n---\n\n".join(sections)
