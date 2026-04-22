# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：cmd_auth.py
# @Date   ：2026/02/01 19:15
# @Author ：leemysw
# 2026/02/01 19:15   Create - 从 main.py 拆分
# =====================================================
"""
[INPUT]: 依赖 typer, feishu_docx.auth.oauth
[OUTPUT]: 对外提供 auth 命令
[POS]: cli 模块的认证 命令
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from typing import Optional

import typer
from rich.panel import Panel

from feishu_docx.auth.oauth import OAuth2Authenticator
from .common import console, get_credentials


# ==============================================================================
# auth 命令
# ==============================================================================


def auth(
        app_id: Optional[str] = typer.Option(
            None,
            "--app-id",
            help="飞书应用 App ID（覆盖配置文件）",
        ),
        app_secret: Optional[str] = typer.Option(
            None,
            "--app-secret",
            help="飞书应用 App Secret（覆盖配置文件）",
        ),
        auth_mode: Optional[str] = typer.Option(
            None,
            "--auth-mode",
            help="认证模式: tenant / oauth（覆盖配置文件）",
        ),
        lark: bool = typer.Option(
            False,
            "--lark",
            help="使用 Lark (海外版)",
        ),
):
    """
    [yellow]❁[/] 获取授权，获取并缓存 Token

    首次使用前运行此命令进行授权：

        # 使用已配置的凭证（推荐，需先运行 feishu-docx config set）
        feishu-docx auth

        # 或指定凭证
        feishu-docx auth --app-id xxx --app-secret xxx

    授权成功后，Token 将被缓存，后续导出无需再次授权。
    """
    try:
        # 获取凭证
        final_app_id, final_app_secret, final_auth_mode = get_credentials(app_id, app_secret, auth_mode)

        if not final_app_id or not final_app_secret:
            console.print(
                "[red]❌ 需要提供 OAuth 凭证[/red]\n\n"
                "方式一：先配置凭证（推荐）\n"
                "  [cyan]feishu-docx config set --app-id xxx --app-secret xxx[/cyan]\n\n"
                "方式二：命令行传入\n"
                "  [cyan]feishu-docx auth --app-id xxx --app-secret xxx[/cyan]"
            )
            raise typer.Exit(1)

        authenticator = OAuth2Authenticator(
            app_id=final_app_id,
            app_secret=final_app_secret,
            is_lark=lark,
        )

        console.print("[yellow]>[/yellow] 正在进行 OAuth 授权...")
        token = authenticator.authenticate()

        console.print(Panel(
            f"✅ 授权成功！\n\n"
            f"Token 已缓存至: [cyan]{authenticator.cache_file}[/cyan]\n\n"
            f"后续使用 [green]feishu-docx export[/green] 命令将自动使用缓存的 Token。",
            title="授权成功",
            border_style="green",
        ))

    except Exception as e:
        console.print(f"[red]❌ 授权失败: {e}[/red]")
        raise typer.Exit(1)
