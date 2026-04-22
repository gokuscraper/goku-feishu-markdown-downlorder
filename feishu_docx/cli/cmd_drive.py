# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：cmd_drive.py
# @Date   ：2026/03/11 13:35
# @Author ：leemysw
# 2026/03/11 11:45   Create
# 2026/03/11 13:35   Add risky clear command for cloud space
# =====================================================
"""
[INPUT]: 依赖 typer, feishu_docx.core.exporter
[OUTPUT]: 对外提供 drive_app 命令组
[POS]: cli 模块的云空间管理命令
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from datetime import datetime
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table

from feishu_docx.core.exporter import FeishuExporter
from .common import console, get_credentials, normalize_drive_target, normalize_folder_token

drive_app = typer.Typer(
    help="[dim]☁[/] 云空间文件管理",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


def _build_exporter(
        token: Optional[str],
        app_id: Optional[str],
        app_secret: Optional[str],
        auth_mode: Optional[str],
        lark: bool,
) -> tuple[FeishuExporter, str, str]:
    """构造导出器并返回访问凭证。"""
    if token:
        _, _, final_auth_mode = get_credentials(None, None, auth_mode)
        exporter = FeishuExporter(access_token=token, auth_mode=final_auth_mode)
        return exporter, token, final_auth_mode

    final_app_id, final_app_secret, final_auth_mode = get_credentials(app_id, app_secret, auth_mode)
    if not final_app_id or not final_app_secret:
        console.print(
            "[red]❌ 需要提供 Token 或应用凭证[/red]\n\n"
            "方式一：先配置凭证（推荐）\n"
            "  [cyan]feishu-docx config set --app-id xxx --app-secret xxx[/cyan]\n\n"
            "方式二：直接传 Token\n"
            "  [cyan]feishu-docx drive ls -t your_access_token[/cyan]\n\n"
            "方式三：命令行传入凭证\n"
            "  [cyan]feishu-docx drive ls --app-id xxx --app-secret xxx[/cyan]"
        )
        raise typer.Exit(1)

    exporter = FeishuExporter(
        app_id=final_app_id,
        app_secret=final_app_secret,
        is_lark=lark,
        auth_mode=final_auth_mode,
    )
    return exporter, exporter.get_access_token(), final_auth_mode


def _format_timestamp(timestamp: Optional[int]) -> str:
    """格式化时间戳。"""
    if not timestamp:
        return "-"
    if isinstance(timestamp, str):
        timestamp = timestamp.strip()
        if not timestamp:
            return "-"
        try:
            timestamp = int(timestamp)
        except ValueError:
            return timestamp
    if timestamp > 10 ** 12:
        timestamp = timestamp // 1000
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _resolve_target(target: str, file_type: Optional[str]) -> tuple[str, str]:
    """解析命令输入的 URL 或 token。"""
    token, parsed_type = normalize_drive_target(target, file_type)
    if not parsed_type:
        console.print("[red]❌ 无法从输入中识别资源类型，请通过 --type 指定[/red]")
        raise typer.Exit(1)
    return token, parsed_type


def _filter_files(files: list, file_type: Optional[str]) -> list:
    """按类型过滤文件。"""
    if not file_type:
        return files
    return [item for item in files if getattr(item, "type", None) == file_type]


@drive_app.command("ls")
def list_files(
        folder: Optional[str] = typer.Option(
            None,
            "--folder",
            help="文件夹 URL 或 token，不传则列出根目录",
        ),
        file_type: Optional[str] = typer.Option(
            None,
            "--type",
            help="仅显示指定类型，如 docx / sheet / bitable / wiki / folder / file",
        ),
        order_by: Optional[str] = typer.Option(
            "EditedTime",
            "--order-by",
            help="排序字段，如 EditedTime / CreatedTime",
        ),
        direction: Optional[str] = typer.Option(
            "DESC",
            "--direction",
            help="排序方向: ASC / DESC",
        ),
        page_size: int = typer.Option(
            50,
            "--page-size",
            min=1,
            max=200,
            help="每页数量",
        ),
        token: Optional[str] = typer.Option(
            None,
            "-t",
            "--token",
            envvar="FEISHU_ACCESS_TOKEN",
            help="直接传入 access_token",
        ),
        app_id: Optional[str] = typer.Option(None, "--app-id", help="飞书应用 App ID"),
        app_secret: Optional[str] = typer.Option(None, "--app-secret", help="飞书应用 App Secret"),
        auth_mode: Optional[str] = typer.Option(
            None,
            "--auth-mode",
            help="认证模式: tenant / oauth",
        ),
        lark: bool = typer.Option(False, "--lark", help="使用 Lark (海外版)"),
):
    """
    列出当前云空间文件。

    `tenant` 模式列出应用云空间，`oauth` 模式列出个人云空间。
    """
    try:
        exporter, access_token, current_auth_mode = _build_exporter(token, app_id, app_secret, auth_mode, lark)
        folder_token = normalize_folder_token(folder)
        files = exporter.sdk.drive.list_files(
            access_token=access_token,
            folder_token=folder_token,
            page_size=page_size,
            order_by=order_by,
            direction=direction,
        )
        files = _filter_files(files, file_type)

        table = Table(title=f"云空间文件列表 ({current_auth_mode})")
        table.add_column("名称", overflow="fold")
        table.add_column("类型", style="cyan", no_wrap=True)
        table.add_column("Token", style="green", overflow="fold")
        table.add_column("修改时间", no_wrap=True)
        table.add_column("链接", overflow="fold")

        for item in files:
            table.add_row(
                item.name or "-",
                item.type or "-",
                item.token or "-",
                _format_timestamp(item.modified_time),
                item.url or "-",
            )

        console.print(table)
        console.print(
            Panel(
                f"共 [green]{len(files)}[/green] 个文件"
                f"\n认证模式: [cyan]{current_auth_mode}[/cyan]"
                f"\n空间类型: "
                f"{'应用云空间' if current_auth_mode == 'tenant' else '个人云空间' if current_auth_mode == 'oauth' else '由 token 类型决定'}",
                border_style="green",
            )
        )
    except Exception as e:
        console.print(f"[red]❌ 获取文件列表失败: {e}[/red]")
        raise typer.Exit(1)


@drive_app.command("rm")
def remove_file(
        target: str = typer.Argument(..., help="文件 URL 或 token"),
        file_type: Optional[str] = typer.Option(
            None,
            "--type",
            help="资源类型，如 docx / sheet / bitable / wiki / folder / file / doc",
        ),
        force: bool = typer.Option(
            False,
            "--force",
            help="跳过确认",
        ),
        token: Optional[str] = typer.Option(None, "-t", "--token", envvar="FEISHU_ACCESS_TOKEN", help="直接传入 access_token"),
        app_id: Optional[str] = typer.Option(None, "--app-id", help="飞书应用 App ID"),
        app_secret: Optional[str] = typer.Option(None, "--app-secret", help="飞书应用 App Secret"),
        auth_mode: Optional[str] = typer.Option(None, "--auth-mode", help="认证模式: tenant / oauth"),
        lark: bool = typer.Option(False, "--lark", help="使用 Lark (海外版)"),
):
    """删除云空间文件。"""
    try:
        exporter, access_token, _ = _build_exporter(token, app_id, app_secret, auth_mode, lark)
        file_token, resolved_type = _resolve_target(target, file_type)

        if not force:
            confirmed = typer.confirm(f"确认删除 {resolved_type}:{file_token} ?")
            if not confirmed:
                raise typer.Exit(0)

        exporter.sdk.drive.delete_file(
            file_token=file_token,
            file_type=resolved_type,
            access_token=access_token,
        )
        console.print(f"[green]✅ 已删除 {resolved_type}:{file_token}[/green]")
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]❌ 删除失败: {e}[/red]")
        raise typer.Exit(1)


@drive_app.command("clear")
def clear_files(
        folder: Optional[str] = typer.Option(
            None,
            "--folder",
            help="文件夹 URL 或 token，不传则清空根目录当前可见文件",
        ),
        file_type: Optional[str] = typer.Option(
            None,
            "--type",
            help="仅清空指定类型，如 docx / sheet / bitable / wiki / folder / file",
        ),
        page_size: int = typer.Option(
            200,
            "--page-size",
            min=1,
            max=200,
            help="每页获取数量",
        ),
        force: bool = typer.Option(
            False,
            "--force",
            help="跳过输入 CLEAR，仍保留一次确认",
        ),
        token: Optional[str] = typer.Option(None, "-t", "--token", envvar="FEISHU_ACCESS_TOKEN", help="直接传入 access_token"),
        app_id: Optional[str] = typer.Option(None, "--app-id", help="飞书应用 App ID"),
        app_secret: Optional[str] = typer.Option(None, "--app-secret", help="飞书应用 App Secret"),
        auth_mode: Optional[str] = typer.Option(None, "--auth-mode", help="认证模式: tenant / oauth"),
        lark: bool = typer.Option(False, "--lark", help="使用 Lark (海外版)"),
):
    """批量清空当前云空间中的文件。"""
    try:
        exporter, access_token, current_auth_mode = _build_exporter(token, app_id, app_secret, auth_mode, lark)
        folder_token = normalize_folder_token(folder)
        files = exporter.sdk.drive.list_files(
            access_token=access_token,
            folder_token=folder_token,
            page_size=page_size,
        )
        files = _filter_files(files, file_type)

        if not files:
            console.print("[yellow]当前范围内没有可清空的文件[/yellow]")
            raise typer.Exit(0)

        preview = Table(title="即将删除的文件（最多展示前 10 个）")
        preview.add_column("名称", overflow="fold")
        preview.add_column("类型", style="cyan", no_wrap=True)
        preview.add_column("Token", style="green", overflow="fold")
        preview.add_column("修改时间", no_wrap=True)
        preview.add_column("链接", overflow="fold")

        for item in files[:10]:
            preview.add_row(
                item.name or "-",
                item.type or "-",
                item.token or "-",
                item.modified_time or "-",
                item.url or "-",
            )
        console.print(preview)

        console.print(
            Panel(
                f"[red]高风险操作[/red]\n\n"
                f"将删除 [bold]{len(files)}[/bold] 个文件"
                f"\n认证模式: [cyan]{current_auth_mode}[/cyan]"
                f"\n空间类型: {'应用云空间' if current_auth_mode == 'tenant' else '个人云空间'}"
                f"\n目录范围: [cyan]{folder_token or 'root'}[/cyan]"
                f"\n类型过滤: [cyan]{file_type or '全部'}[/cyan]"
                f"\n\n删除后无法通过本工具恢复，请确认删除范围正确。",
                border_style="red",
            )
        )

        if not force:
            first_confirm = typer.confirm(
                f"确认删除以上 {len(files)} 个文件吗？此操作不可恢复",
                default=False,
            )
            if not first_confirm:
                console.print("[yellow]已取消清空操作[/yellow]")
                raise typer.Exit(0)

            confirmation = typer.prompt("请输入 CLEAR 确认继续")
            if confirmation.strip() != "CLEAR":
                console.print("[yellow]已取消清空操作[/yellow]")
                raise typer.Exit(0)
        else:
            first_confirm = typer.confirm(
                f"确认删除以上 {len(files)} 个文件吗？此操作不可恢复",
                default=False,
            )
            if not first_confirm:
                console.print("[yellow]已取消清空操作[/yellow]")
                raise typer.Exit(0)

        deleted_count = 0
        for item in files:
            item_token = getattr(item, "token", None)
            item_type = getattr(item, "type", None)
            if not item_token or not item_type:
                continue
            exporter.sdk.drive.delete_file(
                file_token=item_token,
                file_type=item_type,
                access_token=access_token,
            )
            deleted_count += 1

        console.print(
            f"[green]✅ 清空完成[/green]，共删除 [bold]{deleted_count}[/bold] 个文件"
        )
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]❌ 清空失败: {e}[/red]")
        raise typer.Exit(1)


@drive_app.command("perm-show")
def show_public_permission(
        target: str = typer.Argument(..., help="文件 URL 或 token"),
        file_type: Optional[str] = typer.Option(None, "--type", help="资源类型，如 docx / sheet / bitable / wiki / folder / file / doc"),
        token: Optional[str] = typer.Option(None, "-t", "--token", envvar="FEISHU_ACCESS_TOKEN", help="直接传入 access_token"),
        app_id: Optional[str] = typer.Option(None, "--app-id", help="飞书应用 App ID"),
        app_secret: Optional[str] = typer.Option(None, "--app-secret", help="飞书应用 App Secret"),
        auth_mode: Optional[str] = typer.Option(None, "--auth-mode", help="认证模式: tenant / oauth"),
        lark: bool = typer.Option(False, "--lark", help="使用 Lark (海外版)"),
):
    """查看文件公开权限。"""
    try:
        exporter, access_token, _ = _build_exporter(token, app_id, app_secret, auth_mode, lark)
        file_token, resolved_type = _resolve_target(target, file_type)
        permission = exporter.sdk.drive.get_public_permission(
            token=file_token,
            file_type=resolved_type,
            access_token=access_token,
        )

        table = Table(title=f"公开权限 {resolved_type}:{file_token}")
        table.add_column("字段", style="cyan")
        table.add_column("值", style="green", overflow="fold")
        table.add_row("external_access", str(permission.external_access))
        table.add_row("security_entity", str(permission.security_entity))
        table.add_row("comment_entity", str(permission.comment_entity))
        table.add_row("share_entity", str(permission.share_entity))
        table.add_row("link_share_entity", str(permission.link_share_entity))
        table.add_row("invite_external", str(permission.invite_external))
        table.add_row("lock_switch", str(permission.lock_switch))
        console.print(table)
    except Exception as e:
        console.print(f"[red]❌ 获取公开权限失败: {e}[/red]")
        raise typer.Exit(1)


@drive_app.command("perm-set")
def set_public_permission(
        target: str = typer.Argument(..., help="文件 URL 或 token"),
        file_type: Optional[str] = typer.Option(None, "--type", help="资源类型，如 docx / sheet / bitable / wiki / folder / file / doc"),
        external_access: Optional[bool] = typer.Option(None, "--external-access/--no-external-access", help="是否允许外部访问"),
        invite_external: Optional[bool] = typer.Option(None, "--invite-external/--no-invite-external", help="是否允许邀请外部用户"),
        security_entity: Optional[str] = typer.Option(None, "--security-entity", help="安全策略"),
        comment_entity: Optional[str] = typer.Option(None, "--comment-entity", help="评论权限策略"),
        share_entity: Optional[str] = typer.Option(None, "--share-entity", help="分享权限策略"),
        link_share_entity: Optional[str] = typer.Option(None, "--link-share-entity", help="链接分享权限策略"),
        token: Optional[str] = typer.Option(None, "-t", "--token", envvar="FEISHU_ACCESS_TOKEN", help="直接传入 access_token"),
        app_id: Optional[str] = typer.Option(None, "--app-id", help="飞书应用 App ID"),
        app_secret: Optional[str] = typer.Option(None, "--app-secret", help="飞书应用 App Secret"),
        auth_mode: Optional[str] = typer.Option(None, "--auth-mode", help="认证模式: tenant / oauth"),
        lark: bool = typer.Option(False, "--lark", help="使用 Lark (海外版)"),
):
    """更新文件公开权限。"""
    try:
        if all(
                value is None for value in [
                    external_access,
                    invite_external,
                    security_entity,
                    comment_entity,
                    share_entity,
                    link_share_entity,
                ]
        ):
            console.print("[red]❌ 至少提供一个权限字段进行更新[/red]")
            raise typer.Exit(1)

        exporter, access_token, _ = _build_exporter(token, app_id, app_secret, auth_mode, lark)
        file_token, resolved_type = _resolve_target(target, file_type)
        permission = exporter.sdk.drive.update_public_permission(
            token=file_token,
            file_type=resolved_type,
            access_token=access_token,
            external_access=external_access,
            security_entity=security_entity,
            comment_entity=comment_entity,
            share_entity=share_entity,
            link_share_entity=link_share_entity,
            invite_external=invite_external,
        )

        console.print(Panel(
            f"✅ 公开权限更新成功\n\n"
            f"share_entity: [green]{permission.share_entity}[/green]\n"
            f"link_share_entity: [green]{permission.link_share_entity}[/green]\n"
            f"comment_entity: [green]{permission.comment_entity}[/green]",
            border_style="green",
        ))
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]❌ 更新公开权限失败: {e}[/red]")
        raise typer.Exit(1)


@drive_app.command("perm-members")
def list_permission_members(
        target: str = typer.Argument(..., help="文件 URL 或 token"),
        file_type: Optional[str] = typer.Option(None, "--type", help="资源类型，如 docx / sheet / bitable / wiki / folder / file / doc"),
        perm_type: Optional[str] = typer.Option(None, "--perm-type", help="权限类型，如 container"),
        fields: str = typer.Option(
            "member_id,member_type,perm,perm_type,type,name,avatar,external_label",
            "--fields",
            help="返回字段列表",
        ),
        token: Optional[str] = typer.Option(None, "-t", "--token", envvar="FEISHU_ACCESS_TOKEN", help="直接传入 access_token"),
        app_id: Optional[str] = typer.Option(None, "--app-id", help="飞书应用 App ID"),
        app_secret: Optional[str] = typer.Option(None, "--app-secret", help="飞书应用 App Secret"),
        auth_mode: Optional[str] = typer.Option(None, "--auth-mode", help="认证模式: tenant / oauth"),
        lark: bool = typer.Option(False, "--lark", help="使用 Lark (海外版)"),
):
    """列出文件权限成员。"""
    try:
        exporter, access_token, _ = _build_exporter(token, app_id, app_secret, auth_mode, lark)
        file_token, resolved_type = _resolve_target(target, file_type)
        members = exporter.sdk.drive.list_permission_members(
            token=file_token,
            file_type=resolved_type,
            access_token=access_token,
            fields=fields,
            perm_type=perm_type,
        )

        table = Table(title=f"权限成员 {resolved_type}:{file_token}")
        table.add_column("名称", overflow="fold")
        table.add_column("成员类型", style="cyan")
        table.add_column("成员 ID", style="green", overflow="fold")
        table.add_column("权限")
        table.add_column("权限范围")
        table.add_column("外部成员")

        for member in members:
            table.add_row(
                member.name or "-",
                member.member_type or "-",
                member.member_id or "-",
                member.perm or "-",
                member.perm_type or "-",
                str(member.external_label),
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]❌ 获取权限成员失败: {e}[/red]")
        raise typer.Exit(1)


@drive_app.command("perm-add")
def add_permission_member(
        target: str = typer.Argument(..., help="文件 URL 或 token"),
        member_id: str = typer.Option(..., "--member-id", help="成员 ID"),
        member_type: str = typer.Option(..., "--member-type", help="成员类型，如 open_id / user_id / email / chat_id / union_id"),
        perm: str = typer.Option(..., "--perm", help="权限，如 full_access / edit / view"),
        file_type: Optional[str] = typer.Option(None, "--type", help="资源类型，如 docx / sheet / bitable / wiki / folder / file / doc"),
        perm_type: str = typer.Option("container", "--perm-type", help="权限范围"),
        need_notification: bool = typer.Option(False, "--need-notification", help="是否发送通知"),
        token: Optional[str] = typer.Option(None, "-t", "--token", envvar="FEISHU_ACCESS_TOKEN", help="直接传入 access_token"),
        app_id: Optional[str] = typer.Option(None, "--app-id", help="飞书应用 App ID"),
        app_secret: Optional[str] = typer.Option(None, "--app-secret", help="飞书应用 App Secret"),
        auth_mode: Optional[str] = typer.Option(None, "--auth-mode", help="认证模式: tenant / oauth"),
        lark: bool = typer.Option(False, "--lark", help="使用 Lark (海外版)"),
):
    """新增文件权限成员。"""
    try:
        exporter, access_token, _ = _build_exporter(token, app_id, app_secret, auth_mode, lark)
        file_token, resolved_type = _resolve_target(target, file_type)
        member = exporter.sdk.drive.create_permission_member(
            token=file_token,
            file_type=resolved_type,
            access_token=access_token,
            member_id=member_id,
            member_type=member_type,
            perm=perm,
            perm_type=perm_type,
            need_notification=need_notification,
        )
        console.print(
            f"[green]✅ 已新增权限成员[/green] {getattr(member, 'name', None) or member.member_id} "
            f"({getattr(member, 'perm', None) or perm})"
        )
    except Exception as e:
        console.print(f"[red]❌ 新增权限成员失败: {e}[/red]")
        raise typer.Exit(1)


@drive_app.command("perm-update")
def update_permission_member(
        target: str = typer.Argument(..., help="文件 URL 或 token"),
        member_id: str = typer.Option(..., "--member-id", help="成员 ID"),
        member_type: str = typer.Option(..., "--member-type", help="成员类型，如 open_id / user_id / email / chat_id / union_id"),
        perm: str = typer.Option(..., "--perm", help="权限，如 full_access / edit / view"),
        file_type: Optional[str] = typer.Option(None, "--type", help="资源类型，如 docx / sheet / bitable / wiki / folder / file / doc"),
        perm_type: str = typer.Option("container", "--perm-type", help="权限范围"),
        need_notification: bool = typer.Option(False, "--need-notification", help="是否发送通知"),
        token: Optional[str] = typer.Option(None, "-t", "--token", envvar="FEISHU_ACCESS_TOKEN", help="直接传入 access_token"),
        app_id: Optional[str] = typer.Option(None, "--app-id", help="飞书应用 App ID"),
        app_secret: Optional[str] = typer.Option(None, "--app-secret", help="飞书应用 App Secret"),
        auth_mode: Optional[str] = typer.Option(None, "--auth-mode", help="认证模式: tenant / oauth"),
        lark: bool = typer.Option(False, "--lark", help="使用 Lark (海外版)"),
):
    """更新文件权限成员。"""
    try:
        exporter, access_token, _ = _build_exporter(token, app_id, app_secret, auth_mode, lark)
        file_token, resolved_type = _resolve_target(target, file_type)
        member = exporter.sdk.drive.update_permission_member(
            token=file_token,
            file_type=resolved_type,
            access_token=access_token,
            member_id=member_id,
            member_type=member_type,
            perm=perm,
            perm_type=perm_type,
            need_notification=need_notification,
        )
        console.print(
            f"[green]✅ 已更新权限成员[/green] {getattr(member, 'name', None) or member.member_id} "
            f"({getattr(member, 'perm', None) or perm})"
        )
    except Exception as e:
        console.print(f"[red]❌ 更新权限成员失败: {e}[/red]")
        raise typer.Exit(1)


@drive_app.command("perm-rm")
def remove_permission_member(
        target: str = typer.Argument(..., help="文件 URL 或 token"),
        member_id: str = typer.Option(..., "--member-id", help="成员 ID"),
        member_type: str = typer.Option(..., "--member-type", help="成员类型，如 open_id / user_id / email / chat_id / union_id"),
        file_type: Optional[str] = typer.Option(None, "--type", help="资源类型，如 docx / sheet / bitable / wiki / folder / file / doc"),
        perm_type: str = typer.Option("container", "--perm-type", help="权限范围"),
        token: Optional[str] = typer.Option(None, "-t", "--token", envvar="FEISHU_ACCESS_TOKEN", help="直接传入 access_token"),
        app_id: Optional[str] = typer.Option(None, "--app-id", help="飞书应用 App ID"),
        app_secret: Optional[str] = typer.Option(None, "--app-secret", help="飞书应用 App Secret"),
        auth_mode: Optional[str] = typer.Option(None, "--auth-mode", help="认证模式: tenant / oauth"),
        lark: bool = typer.Option(False, "--lark", help="使用 Lark (海外版)"),
):
    """删除文件权限成员。"""
    try:
        exporter, access_token, _ = _build_exporter(token, app_id, app_secret, auth_mode, lark)
        file_token, resolved_type = _resolve_target(target, file_type)
        exporter.sdk.drive.delete_permission_member(
            token=file_token,
            file_type=resolved_type,
            access_token=access_token,
            member_id=member_id,
            member_type=member_type,
            perm_type=perm_type,
        )
        console.print(f"[green]✅ 已删除权限成员[/green] {member_type}:{member_id}")
    except Exception as e:
        console.print(f"[red]❌ 删除权限成员失败: {e}[/red]")
        raise typer.Exit(1)
