# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：cmd_write.py
# @Date   ：2026/03/28 10:35
# @Author ：leemysw
# 2026/02/01 19:15   Create - 从 main.py 拆分
# 2026/03/02 10:39   Add wechat import into create command
# 2026/03/28 10:35   Add native markdown convert switch for create and write
# =====================================================
"""
[INPUT]: 依赖 typer, feishu_docx.core.writer, feishu_docx.core.exporter
[OUTPUT]: 对外提供 create, write, update 命令
[POS]: cli 模块的写入命令
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import typer
from rich.panel import Panel

from .common import console, get_credentials, normalize_folder_token


# ==============================================================================
# create 命令 - 创建文档
# ==============================================================================


def create(
        title: Optional[str] = typer.Argument(None, help="文档标题（使用 --url 时可省略）"),
        url: Optional[str] = typer.Option(
            None,
            "--url",
            help="微信公众号文章 URL（传入后自动抓取并导入）",
        ),
        content: Optional[str] = typer.Option(
            None,
            "-c",
            "--content",
            help="Markdown 内容字符串",
        ),
        file: Optional[Path] = typer.Option(
            None,
            "-f",
            "--file",
            help="Markdown 文件路径",
            exists=True,
        ),
        folder: Optional[str] = typer.Option(
            None,
            "--folder",
            help="目标文件夹 token",
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
        native: bool = typer.Option(
            False,
            "--native",
            help="使用飞书原生 Markdown 转换（可能存在顺序不稳定问题）",
        ),
):
    """
    [green]▶[/] 创建飞书文档

    示例:

        # 创建空白文档\\\\n
        feishu-docx create "我的笔记"

        # 根据公众号 URL 创建文档\\\\n
        feishu-docx create --url "https://mp.weixin.qq.com/s/xxxxx"

        # 创建文档并写入 Markdown 内容\\\\n
        feishu-docx create "会议记录" -c "# 会议纪要\\\\n\\\\n- 议题一\\\\n- 议题二"

        # 从 Markdown 文件创建文档\\\\n
        feishu-docx create "周报" -f ./weekly_report.md
    """
    if not title and not url:
        console.print("[red]❌ 必须提供文档标题或 --url[/red]")
        raise typer.Exit(1)

    if url and (content or file):
        console.print("[red]❌ 使用 --url 时不能同时传入 --content 或 --file[/red]")
        raise typer.Exit(1)

    if url:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "mp.weixin.qq.com":
            console.print("[red]❌ 请输入有效的微信公众号文章 URL（https://mp.weixin.qq.com/...）[/red]")
            raise typer.Exit(1)

    try:
        from feishu_docx.core.writer import FeishuWriter
        from feishu_docx.core.wechat_importer import WeChatArticleImporter, WeChatImportError
        from feishu_docx import FeishuExporter

        # 获取凭证
        if token:
            exporter = FeishuExporter.from_token(token)
            access_token = token
        else:
            final_app_id, final_app_secret, final_auth_mode = get_credentials(app_id, app_secret, auth_mode)
            if not final_app_id or not final_app_secret:
                console.print("[red]❌ 需要提供凭证，请运行 feishu-docx config set[/red]")
                raise typer.Exit(1)
            exporter = FeishuExporter(app_id=final_app_id, app_secret=final_app_secret, is_lark=lark,
                                      auth_mode=final_auth_mode)
            access_token = exporter.get_access_token()

        writer = FeishuWriter(sdk=exporter.sdk)

        if url:
            with tempfile.TemporaryDirectory(prefix="feishu_docx_wechat_") as temp_dir:
                importer = WeChatArticleImporter(workspace=Path(temp_dir))
                article = importer.import_article(url)
                md_path = importer.save_markdown(article)

                doc = writer.create_document(
                    title=title or article.title,
                    file_path=md_path,
                    folder_token=normalize_folder_token(folder),
                    user_access_token=access_token,
                    use_native_api=native,
                )

            console.print(Panel(
                f"✅ 创建成功!\n\n"
                f"[blue]文章标题:[/blue] {article.title}\n"
                f"[blue]文档 ID:[/blue] {doc['document_id']}\n"
                f"[blue]链接:[/blue] {doc['url']}\n"
                f"[blue]下载图片:[/blue] {article.downloaded_images}",
                border_style="green"
            ))
            return

        # 创建普通文档
        doc = writer.create_document(
            title=title or "",
            content=content,
            file_path=file,
            folder_token=normalize_folder_token(folder),
            user_access_token=access_token,
            use_native_api=native,
        )

        console.print(Panel(
            f"✅ 创建成功!\n\n"
            f"[blue]文档 ID:[/blue] {doc['document_id']}\n"
            f"[blue]链接:[/blue] {doc['url']}",
            border_style="green"
        ))

    except WeChatImportError as e:
        console.print(f"[red]❌ 公众号导入失败: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]❌ 创建失败: {e}[/red]")
        raise typer.Exit(1)


# ==============================================================================
# write 命令 - 向文档写入内容
# ==============================================================================


def write(
        url: str = typer.Argument(..., help="飞书文档 URL"),
        content: Optional[str] = typer.Option(
            None,
            "-c",
            "--content",
            help="Markdown 内容字符串",
        ),
        file: Optional[Path] = typer.Option(
            None,
            "-f",
            "--file",
            help="Markdown 文件路径",
            exists=True,
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
        native: bool = typer.Option(
            False,
            "--native",
            help="使用飞书原生 Markdown 转换（可能存在顺序不稳定问题）",
        ),
):
    """
    [green]▶[/] 向飞书文档追加 Markdown 内容

    示例:

        # 追加 Markdown 内容\\\\n
        feishu-docx write "https://xxx.feishu.cn/docx/xxx" -c "## 新章节\\\\n\\\\n内容"

        # 从文件追加内容\\\\n
        feishu-docx write "https://xxx.feishu.cn/docx/xxx" -f ./content.md
    """
    if not content and not file:
        console.print("[red]❌ 必须提供 -c/--content 或 -f/--file[/red]")
        raise typer.Exit(1)

    try:
        from feishu_docx.core.writer import FeishuWriter
        from feishu_docx import FeishuExporter

        # 获取凭证
        if token:
            exporter = FeishuExporter.from_token(token)
            access_token = token
        else:
            final_app_id, final_app_secret, final_auth_mode = get_credentials(app_id, app_secret, auth_mode)
            if not final_app_id or not final_app_secret:
                console.print("[red]❌ 需要提供凭证[/red]")
                raise typer.Exit(1)
            exporter = FeishuExporter(app_id=final_app_id, app_secret=final_app_secret, is_lark=lark,
                                      auth_mode=final_auth_mode)
            access_token = exporter.get_access_token()

        # 解析 URL 获取 document_id
        doc_info = exporter.parse_url(url)
        if doc_info.node_type not in ["docx", "wiki"]:
            console.print(f"[red]❌ 只支持 docx / wiki 类型文档，当前类型: {doc_info.node_type}[/red]")
            raise typer.Exit(1)

        writer = FeishuWriter(sdk=exporter.sdk)

        # 写入内容
        blocks = writer.write_content(
            document_id=doc_info.node_token,
            content=content,
            file_path=file,
            user_access_token=access_token,
            use_native_api=native,
        )

        console.print(Panel(f"✅ 写入成功! 添加了 {len(blocks)} 个 Block", border_style="green"))

    except Exception as e:
        console.print(f"[red]❌ 写入失败: {e}[/red]")
        raise typer.Exit(1)


# ==============================================================================
# update 命令 - 更新指定 Block
# ==============================================================================


def update(
        url: str = typer.Argument(..., help="飞书文档 URL"),
        block_id: str = typer.Option(..., "-b", "--block-id", help="Block ID (从 --with-block-ids 导出获取)"),
        content: str = typer.Option(..., "-c", "--content", help="新的文本内容"),
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
    [green]▶[/] 更新飞书文档中指定 Block 的内容

    示例:

        # 先导出获取 Block ID\\\\n
        feishu-docx export "https://xxx.feishu.cn/docx/xxx" --with-block-ids

        # 然后更新指定 Block\\\\n
        feishu-docx update "https://xxx.feishu.cn/docx/xxx" -b blk123abc -c "更新后的内容"
    """
    try:
        from feishu_docx.core.writer import FeishuWriter
        from feishu_docx import FeishuExporter

        # 获取凭证
        if token:
            exporter = FeishuExporter.from_token(token)
            access_token = token
        else:
            final_app_id, final_app_secret, final_auth_mode = get_credentials(app_id, app_secret, auth_mode)
            if not final_app_id or not final_app_secret:
                console.print("[red]❌ 需要提供凭证[/red]")
                raise typer.Exit(1)
            exporter = FeishuExporter(app_id=final_app_id, app_secret=final_app_secret, is_lark=lark,
                                      auth_mode=final_auth_mode)
            access_token = exporter.get_access_token()

        # 解析 URL 获取 document_id
        doc_info = exporter.parse_url(url)

        writer = FeishuWriter(sdk=exporter.sdk)

        # 更新 Block
        writer.update_block(
            document_id=doc_info.node_token,
            block_id=block_id,
            content=content,
            user_access_token=access_token,
        )

        console.print(Panel(f"✅ Block [cyan]{block_id}[/cyan] 更新成功!", border_style="green"))

    except Exception as e:
        console.print(f"[red]❌ 更新失败: {e}[/red]")
        raise typer.Exit(1)
