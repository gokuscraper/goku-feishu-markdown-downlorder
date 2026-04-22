# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：cmd_export.py
# @Date   ：2026/02/01 19:15
# @Author ：leemysw
# 2026/02/01 19:15   Create - 从 main.py 拆分
# 2026/03/02 11:00   Add export-wechat command
# =====================================================
"""
[INPUT]: 依赖 typer, feishu_docx.core.exporter
[OUTPUT]: 对外提供 export, export_wechat, export_wiki_space 命令
[POS]: cli 模块的导出命令
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

from feishu_docx.core.exporter import FeishuExporter
from .common import console, get_credentials

# ==============================================================================
# export 命令
# ==============================================================================


def export(
        url: str = typer.Argument(..., help="飞书文档 URL"),
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
        token: Optional[str] = typer.Option(
            None,
            "-t",
            "--token",
            envvar="FEISHU_ACCESS_TOKEN",
            help="用户访问凭证（或设置环境变量 FEISHU_ACCESS_TOKEN）",
        ),
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
        table_format: str = typer.Option(
            "md",
            "--table",
            help="表格输出格式: html / md",
        ),
        sheet_value_mode: str = typer.Option(
            "display",
            "--sheet-value-mode",
            help="电子表格单元格导出模式: display / formula（仅影响 Sheet 与嵌入 Sheet）",
        ),
        lark: bool = typer.Option(
            False,
            "--lark",
            help="使用 Lark (海外版)",
        ),
        auth_mode: Optional[str] = typer.Option(
            None,
            "--auth-mode",
            help="认证模式: tenant / oauth（覆盖配置文件）",
        ),
        stdout: bool = typer.Option(
            False,
            "--stdout",
            "-c",
            help="直接输出内容到 stdout（不保存文件，适合 AI Agent 使用）",
        ),
        with_block_ids: bool = typer.Option(
            False,
            "--with-block-ids",
            "-b",
            help="在导出的 Markdown 中嵌入 Block ID 注释（用于后续更新文档）",
        ),
        export_board_metadata: bool = typer.Option(
            False,
            "--export-board-metadata",
            help="导出画板节点元数据（包含位置、大小、类型等信息）",
        ),
):
    """
    [green]▶[/] 导出飞书文档为 Markdown


    示例:

        # 使用已配置的凭证导出（推荐，需先运行 feishu-docx config set）\\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx"

        # 使用 Token (如: user_access_token) 导出 \\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" -t your_token

        # 使用 OAuth 授权（覆盖配置）\\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" --app-id xxx --app-secret xxx

        # 导出到指定目录 \\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" -o ./docs -n my_doc

        # 导出 Sheet 时保留公式 \\n
        feishu-docx export "https://xxx.feishu.cn/wiki/xxx" --table md --sheet-value-mode formula

        # 直接输出内容（适合 AI Agent）\\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" --stdout

        # 同时导出画板图片和元数据 \\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" --export-board-metadata
    """
    try:
        # 创建导出器
        if token:
            exporter = FeishuExporter.from_token(token)
        else:
            # 获取凭证（命令行参数 > 环境变量 > 配置文件）
            final_app_id, final_app_secret, final_auth_mode = get_credentials(app_id, app_secret, auth_mode)

            if final_app_id and final_app_secret:
                exporter = FeishuExporter(app_id=final_app_id, app_secret=final_app_secret, is_lark=lark, auth_mode=final_auth_mode)
            else:
                console.print(
                    "[red]❌ 需要提供 Token 或 OAuth 凭证[/red]\n\n"
                    "方式一：先配置凭证（推荐）\n"
                    "  [cyan]feishu-docx config set --app-id xxx --app-secret xxx[/cyan]\n\n"
                    "方式二：使用 Token (如: user_access_token)\n"
                    "  [cyan]feishu-docx export URL -t your_token[/cyan]\n\n"
                    "方式三：命令行传入\n"
                    "  [cyan]feishu-docx export URL --app-id xxx --app-secret xxx[/cyan]"
                )
                raise typer.Exit(1)

        # 执行导出
        if stdout:
            # 直接输出内容到 stdout
            content = exporter.export_content(
                url=url,
                table_format=table_format,  # type: ignore
                sheet_value_mode=sheet_value_mode,  # type: ignore
                export_board_metadata=export_board_metadata,
            )
            print(content)
        else:
            # 保存到文件
            output_path = exporter.export(
                url=url,
                output_dir=output,
                filename=filename,
                table_format=table_format,  # type: ignore
                sheet_value_mode=sheet_value_mode,  # type: ignore
                with_block_ids=with_block_ids,
                export_board_metadata=export_board_metadata,
            )
            console.print(Panel(f"✅ 导出完成: [green]{output_path}[/green]", border_style="green"))

    except ValueError as e:
        console.print(f"[red]❌ 错误: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ 导出失败: {e}[/red]")
        raise typer.Exit(1)


# ==============================================================================
# export-wechat 命令
# ==============================================================================


def export_wechat(
        url: str = typer.Argument(..., help="微信公众号文章 URL"),
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
):
    """
    [green]▶[/] 导出微信公众号文章为 Markdown

    示例:

        # 导出到默认目录 ./output\\\\n
        feishu-docx export-wechat \"https://mp.weixin.qq.com/s/xxxxx\"

        # 导出到指定目录\\\\n
        feishu-docx export-wechat \"https://mp.weixin.qq.com/s/xxxxx\" -o ./docs

        # 指定输出文件名\\\\n
        feishu-docx export-wechat \"https://mp.weixin.qq.com/s/xxxxx\" -n my_wechat_article
    """
    from feishu_docx.core.wechat_importer import WeChatArticleImporter, WeChatImportError

    try:
        importer = WeChatArticleImporter(workspace=output)
        article = importer.import_article(url)
        output_path = importer.save_markdown(article, filename=filename)

        console.print(Panel(
            f"✅ 导出完成!\n\n"
            f"[blue]文章标题:[/blue] {article.title}\n"
            f"[blue]输出文件:[/blue] {output_path}\n"
            f"[blue]下载图片:[/blue] {article.downloaded_images}",
            border_style="green",
        ))
    except WeChatImportError as e:
        console.print(f"[red]❌ 公众号导出失败: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ 导出失败: {e}[/red]")
        raise typer.Exit(1)


# ==============================================================================
# export-wiki-space 命令
# ==============================================================================


def export_wiki_space(
        space_id_or_url: str = typer.Argument(..., help="知识空间 ID、Wiki URL 或 my_library"),
        output: Path = typer.Option(
            Path("./wiki_export"),
            "-o",
            "--output",
            help="输出目录",
        ),
        parent_node: Optional[str] = typer.Option(
            None,
            "--parent-node",
            help="父节点 token（不传则导出space_id或wiki_url下的所有子节点）",
        ),
        max_depth: int = typer.Option(
            3,
            "--max-depth",
            help="最大遍历深度",
        ),
        sheet_value_mode: str = typer.Option(
            "display",
            "--sheet-value-mode",
            help="电子表格单元格导出模式: display / formula（仅影响 Sheet 与嵌入 Sheet）",
        ),
        token: Optional[str] = typer.Option(
            None,
            "-t",
            "--token",
            envvar="FEISHU_ACCESS_TOKEN",
            help="用户访问凭证",
        ),
        app_id: Optional[str] = typer.Option(None, "--app-id", help="飞书应用 App ID"),
        app_secret: Optional[str] = typer.Option(None, "--app-secret", help="飞书应用 App Secret"),
        auth_mode: Optional[str] = typer.Option(None, "--auth-mode", help="认证模式: tenant / oauth"),
        lark: bool = typer.Option(False, "--lark", help="使用 Lark (海外版)"),
):
    """
    [green]▶[/] 批量导出知识空间下的所有文档

    支持直接输入 Wiki URL，自动提取知识空间 ID。

    示例:

        # 使用 Wiki URL（自动提取 space_id）\\\\n
        feishu-docx export-wiki-space "https://my.feishu.cn/wiki/<token>"

        # 直接使用知识空间 ID\\\\n
        feishu-docx export-wiki-space <space_id>

        # 导出我的文档库\\\\n
        feishu-docx export-wiki-space my_library -o ./my_docs

        # 限制遍历深度\\\\n
        feishu-docx export-wiki-space my_library --max-depth 2

        # 批量导出时保留 Sheet 公式\\\\n
        feishu-docx export-wiki-space my_library --sheet-value-mode formula
    """
    try:
        # 获取凭证
        if token:
            exporter = FeishuExporter.from_token(token)
            access_token = token
        else:
            final_app_id, final_app_secret, final_auth_mode = get_credentials(app_id, app_secret, auth_mode)
            if not final_app_id or not final_app_secret:
                console.print("[red]❌ 需要提供凭证[/red]")
                raise typer.Exit(1)
            exporter = FeishuExporter(app_id=final_app_id, app_secret=final_app_secret, is_lark=lark, auth_mode=final_auth_mode)

        console.print(f"[blue]> 输入:[/blue] {space_id_or_url}")
        console.print(f"[blue]> 输出目录:[/blue] {output}")
        console.print(f"[blue]> 最大深度:[/blue] {max_depth}")
        console.print("[yellow]> 开始批量导出...[/yellow]")

        # 调用 Exporter 的 export_wiki_space 方法（支持 URL 或 space_id）
        result = exporter.export_wiki_space(
            space_id_or_url=space_id_or_url,
            output_dir=output,
            max_depth=max_depth,
            parent_node_token=parent_node,
            sheet_value_mode=sheet_value_mode,  # type: ignore
            silent=False,
        )

        # 输出统计
        console.print(Panel(
            f"✅ 导出完成!\n\n"
            f"[green]成功:[/green] {result['exported']} 个文档\n"
            f"[red]失败:[/red] {result['failed']} 个文档\n"
            f"[blue]输出目录:[/blue] {result['space_dir']}",
            border_style="green",
        ))

    except Exception as e:
        console.print(f"[red]❌ 批量导出失败: {e}[/red]")
        raise typer.Exit(1)
