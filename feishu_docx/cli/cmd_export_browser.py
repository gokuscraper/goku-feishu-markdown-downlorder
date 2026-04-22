# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：cmd_export_browser.py
# @Date   ：2026/03/30 20:31
# @Author ：leemysw
# 2026/03/30 20:31   Create
# =====================================================
"""
[INPUT]: 依赖 typer, feishu_docx.core.exporter
[OUTPUT]: 对外提供 export_browser 命令
[POS]: cli 模块的浏览器回退导出命令
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

from feishu_docx.core.exporter import FeishuExporter
from .common import console


def export_browser(
        url: str = typer.Argument(..., help="飞书/Lark 文档 URL"),
        output: Path = typer.Option(
            Path("./output"),
            "-o",
            "--output",
            help="输出目录",
            file_okay=False,
            dir_okay=True,
        ),
        filename: Optional[str] = typer.Option(
            None,
            "-n",
            "--name",
            help="输出文件名（不含扩展名）",
        ),
        stdout: bool = typer.Option(
            False,
            "--stdout",
            "-c",
            help="直接输出 Markdown 到 stdout",
        ),
        headless: bool = typer.Option(
            True,
            "--headless/--headed",
            help="是否使用无头浏览器",
        ),
        timeout_ms: int = typer.Option(
            30000,
            "--timeout-ms",
            min=1000,
            help="页面加载超时（毫秒）",
        ),
        storage_state: Optional[Path] = typer.Option(
            None,
            "--storage-state",
            help="Playwright storage state JSON 文件路径，用于复用登录态",
            exists=True,
            dir_okay=False,
            file_okay=True,
        ),
        executable_path: Optional[Path] = typer.Option(
            None,
            "--browser-executable",
            help="自定义浏览器可执行文件路径",
            exists=True,
            dir_okay=False,
            file_okay=True,
        ),
):
    """
    [green]▶[/] 使用浏览器上下文导出飞书文档为 Markdown

    适用于公开文档，或通过 `--storage-state` 提供浏览器登录态的场景。
    """
    try:
        exporter = FeishuExporter()

        if stdout:
            content = exporter.export_content_with_browser(
                url=url,
                headless=headless,
                timeout_ms=timeout_ms,
                storage_state_path=str(storage_state) if storage_state else None,
                executable_path=str(executable_path) if executable_path else None,
            )
            print(content)
            return

        output_path = exporter.export_with_browser(
            url=url,
            output_dir=output,
            filename=filename,
            headless=headless,
            timeout_ms=timeout_ms,
            storage_state_path=str(storage_state) if storage_state else None,
            executable_path=str(executable_path) if executable_path else None,
        )
        console.print(
            Panel(
                f"✅ 浏览器回退导出完成: [green]{output_path}[/green]",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(f"[red]❌ 浏览器回退导出失败: {e}[/red]")
        raise typer.Exit(1)
