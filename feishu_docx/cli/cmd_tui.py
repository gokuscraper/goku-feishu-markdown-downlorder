# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：cmd_tui
# @Date   ：2026/2/1 19:28
# @Author ：leemysw
#
# 2026/2/1 19:28   Create
# =====================================================

"""
[INPUT]: 依赖 typer
[OUTPUT]: 对外提供 tui 命令
[POS]: cli 模块的认 TUI 命令
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import typer

from .common import console


# ==============================================================================
# tui 命令
# ==============================================================================


def tui():
    """
    [magenta]✪[/] TUI 交互界面

    提供终端图形界面进行文档导出操作。
    """
    try:
        from feishu_docx.tui.app import FeishuDocxApp
        app_tui = FeishuDocxApp()
        app_tui.run()
    except ImportError as e:
        console.print(f"[red]❌ TUI 模块加载失败: {e}[/red]")
        console.print("[yellow]请确保已安装 textual: pip install textual[/yellow]")
        raise typer.Exit(1)
