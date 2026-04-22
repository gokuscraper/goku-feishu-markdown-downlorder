# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：cmd_config.py
# @Date   ：2026/02/01 19:15
# @Author ：leemysw
# 2026/02/01 19:15   Create - 从 main.py 拆分
# =====================================================
"""
[INPUT]: 依赖 typer, feishu_docx.utils.config
[OUTPUT]: 对外提供 config_set, config_show, config_clear 命令
[POS]: cli 模块的配置管理命令
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import os
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table

from feishu_docx.utils.config import AppConfig, get_config_dir
from .common import console


# ==============================================================================
# config set 命令
# ==============================================================================


def config_set(
        app_id: Optional[str] = typer.Option(
            None,
            "--app-id",
            help="飞书应用 App ID",
        ),
        app_secret: Optional[str] = typer.Option(
            None,
            "--app-secret",
            help="飞书应用 App Secret",
        ),
        auth_mode: Optional[str] = typer.Option(
            None,
            "--auth-mode",
            help="认证模式: tenant (默认，无需授权页面) 或 oauth (浏览器授权)",
        ),
        lark: bool = typer.Option(
            False,
            "--lark",
            help="使用 Lark (海外版)",
        ),
):
    """
    设置飞书应用凭证

    配置后，export 和 auth 命令将自动使用这些凭证，无需每次传入。

    认证模式：
    - tenant (默认): 使用 tenant_access_token，无需浏览器授权，适合 AI Agent
    - oauth: 使用 user_access_token，需要浏览器授权，支持更多用户级权限

    示例:
        feishu-docx config set --app-id cli_xxx --app-secret xxx
        feishu-docx config set --auth-mode oauth  # 切换到 OAuth 模式
    """
    config = AppConfig.load()

    # 更新配置（只更新传入的值）
    if app_id:
        config.app_id = app_id
    if app_secret:
        config.app_secret = app_secret
    if auth_mode:
        if auth_mode not in ("tenant", "oauth"):
            console.print("[red]❌ auth_mode 必须是 'tenant' 或 'oauth'[/red]")
            raise typer.Exit(1)
        config.auth_mode = auth_mode
    if lark:
        config.is_lark = lark

    # 交互式输入缺失的值
    if not config.app_id:
        config.app_id = typer.prompt("App ID")
    if not config.app_secret:
        config.app_secret = typer.prompt("App Secret", hide_input=True)

    config.save()

    auth_mode_desc = "tenant_access_token (无需授权页面)" if config.auth_mode == "tenant" else "OAuth 2.0 (浏览器授权)"
    console.print(Panel(
        f"✅ 配置已保存至: [cyan]{config.config_file}[/cyan]\n\n"
        f"App ID: [green]{config.app_id[:10]}...{config.app_id[-4:]}[/green]\n"
        f"App Secret: [dim]已保存（已隐藏）[/dim]\n"
        f"认证模式: [blue]{auth_mode_desc}[/blue]\n"
        f"Lark 模式: {'是' if config.is_lark else '否'}\n\n"
        "现在你可以直接运行：\n"
        "  [cyan]feishu-docx export URL[/cyan] - 导出文档",
        title="配置成功",
        border_style="green",
    ))


# ==============================================================================
# config show 命令
# ==============================================================================


def config_show():
    """显示当前配置"""
    config = AppConfig.load()

    table = Table(title="当前配置")
    table.add_column("配置项", style="cyan")
    table.add_column("来源", style="dim")
    table.add_column("值", style="green")

    # App ID
    app_id_env = os.getenv("FEISHU_APP_ID")
    if app_id_env:
        table.add_row("App ID", "环境变量",
                      f"{app_id_env[:10]}...{app_id_env[-4:]}" if len(app_id_env) > 14 else app_id_env)
    elif config.app_id:
        table.add_row("App ID", "配置文件",
                      f"{config.app_id[:10]}...{config.app_id[-4:]}" if len(config.app_id) > 14 else config.app_id)
    else:
        table.add_row("App ID", "-", "[dim]未设置[/dim]")

    # App Secret
    app_secret_env = os.getenv("FEISHU_APP_SECRET")
    if app_secret_env:
        table.add_row("App Secret", "环境变量", "[dim]已设置（已隐藏）[/dim]")
    elif config.app_secret:
        table.add_row("App Secret", "配置文件", "[dim]已设置（已隐藏）[/dim]")
    else:
        table.add_row("App Secret", "-", "[dim]未设置[/dim]")

    # Access Token
    if os.getenv("FEISHU_ACCESS_TOKEN"):
        table.add_row("Access Token", "环境变量", "[dim]已设置（已隐藏）[/dim]")
    else:
        if not (app_secret_env or config.app_secret) and not (app_id_env or config.app_id):
            table.add_row("Access Token", "-", "[dim]未设置[/dim]")

    # Lark 模式
    table.add_row("Lark 模式", "配置文件", "是" if config.is_lark else "否")

    # 缓存位置
    cache_dir = get_config_dir()
    table.add_row("配置文件", "-", "存在" if config.config_file.exists() else "❌ 不存在")
    table.add_row("Token 缓存", "-", "存在" if (cache_dir / "token.json").exists() else "❌ 不存在")
    table.add_row("配置目录", "-", str(cache_dir))

    console.print(table)

    # 提示
    if not config.has_credentials() and not app_id_env:
        console.print("\n[yellow]💡 提示: 运行以下命令配置凭证[/yellow]")
        console.print("   [cyan]feishu-docx config set --app-id xxx --app-secret xxx[/cyan]")


# ==============================================================================
# config clear 命令
# ==============================================================================


def config_clear(
        force: bool = typer.Option(False, "--force", "-f", help="跳过确认"),
        token: bool = typer.Option(True, "--token", "-t", help="清除 Token 缓存"),
        config: bool = typer.Option(False, "--config", "-c", help="清除配置文件"),
        all: bool = typer.Option(False, "--all", "-a", help="同时清除配置和 Token 缓存"),
):
    """清除配置和缓存"""
    app_config = AppConfig.load()
    cache_dir = get_config_dir()
    token_file = cache_dir / "token.json"

    has_config = app_config.config_file.exists()
    has_token = token_file.exists()

    if not has_config and not has_token:
        console.print("[yellow]没有可清除的配置或缓存[/yellow]")
        return

    # 确认
    if not force:
        if all or (config and token):
            msg = "确定要清除配置文件和 Token 缓存吗？"
        elif config:
            msg = "确定要清除配置文件吗？（Token 缓存保留，使用 --all 同时清除配置）"
        else:
            msg = "确定要清除 Token 缓存吗？（配置文件保留，使用 --all 同时清除配置）"
        confirm = typer.confirm(msg)
        if not confirm:
            console.print("已取消")
            raise typer.Abort()

    # 清除
    if (all or config) and has_config:
        app_config.clear()
        console.print("[green]✅ 配置文件已清除[/green]")

    if (token or all) and has_token:
        token_file.unlink()
        console.print("[green]✅ Token 缓存已清除[/green]")
