# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：exporter.py
# @Date   ：2026/03/30 20:25
# @Author ：leemysw
# 2025/01/09 18:30   Create
# 2026/01/28 12:05   Use safe console output
# 2026/01/28 16:00   Add whiteboard metadata export support
# 2026/01/28 19:00   Add support for old doc format (/doc/)
# 2026/01/28 19:30   Support both /sheet/ and /sheets/ URL formats
# 2026/02/04 10:15   Persist document domain for media fallback
# 2026/03/30 20:25   Add browser fallback export helpers
# =====================================================
"""
[INPUT]: 依赖 feishu_docx.core.parsers 的解析器，依赖 feishu_docx.auth 的认证器
[OUTPUT]: 对外提供 FeishuExporter 类，统一的导出入口
[POS]: core 模块的主导出器，是用户使用的主要接口
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import re
from urllib.parse import urlparse
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from feishu_docx.auth import OAuth2Authenticator, TenantAuthenticator
from feishu_docx.core.parsers.bitable import BitableParser
from feishu_docx.core.parsers.document import DocumentParser
from feishu_docx.core.parsers.sheet import SheetParser
from feishu_docx.core.sdk import FeishuSDK
from feishu_docx.utils.console import get_console

console = get_console()


# ==============================================================================
# URL 解析结果
# ==============================================================================
@dataclass
class NodeInfo:
    """文档信息"""
    node_type: str  # "docx", "sheet", "bitable", "wiki"
    node_token: str  # 文档 ID


# ==============================================================================
# 主导出器
# ==============================================================================
class FeishuExporter:
    """
    飞书文档导出器

    支持导出以下类型的飞书云文档：
    - 云文档 (docx)
    - 电子表格 (sheet)
    - 多维表格 (bitable)
    - 知识库文档 (wiki)

    使用示例：
        # 方式一：使用 OAuth 自动授权
        exporter = FeishuExporter(
            app_id="xxx",
            app_secret="xxx"
        )
        path = exporter.export("https://xxx.feishu.cn/docx/xxx", "./output")

        # 方式二：手动传入 Token
        exporter = FeishuExporter.from_token("user_access_token_xxx")
        path = exporter.export("https://xxx.feishu.cn/docx/xxx", "./output")
    """

    # URL 模式匹配
    URL_PATTERNS = {
        # 旧版云文档: https://xxx.feishu.cn/doc/{document_id}
        "doc": re.compile(r"(?:feishu|larksuite)\.cn/doc/([a-zA-Z0-9]+)|larkoffice\.com/doc/([a-zA-Z0-9]+)"),
        # 云文档: https://xxx.feishu.cn/docx/{document_id} 或 https://xxx.larkoffice.com/docx/{document_id}
        "docx": re.compile(r"(?:feishu|larksuite)\.cn/docx/([a-zA-Z0-9]+)|larkoffice\.com/docx/([a-zA-Z0-9]+)"),
        # 电子表格: https://xxx.feishu.cn/sheet(s)/{spreadsheet_token} 或 https://xxx.larkoffice.com/sheet(s)/{spreadsheet_token}
        "sheet": re.compile(r"(?:feishu|larksuite)\.cn/sheets?/([a-zA-Z0-9]+)|larkoffice\.com/sheets?/([a-zA-Z0-9]+)"),
        # 多维表格: https://xxx.feishu.cn/base/{app_token} 或 https://xxx.larkoffice.com/base/{app_token}
        "bitable": re.compile(r"(?:feishu|larksuite)\.cn/base/([a-zA-Z0-9]+)|larkoffice\.com/base/([a-zA-Z0-9]+)"),
        # Wiki 文档: https://xxx.feishu.cn/wiki/{node_token} 或 https://xxx.larkoffice.com/wiki/{node_token}
        "wiki": re.compile(r"(?:feishu|larksuite)\.cn/wiki/([a-zA-Z0-9]+)|larkoffice\.com/wiki/([a-zA-Z0-9]+)"),
    }

    def __init__(
            self,
            app_id: Optional[str] = None,
            app_secret: Optional[str] = None,
            access_token: Optional[str] = None,
            is_lark: bool = False,
            auth_mode: str = "tenant",
    ):
        """
        初始化导出器

        Args:
            app_id: 飞书应用 App ID
            app_secret: 飞书应用 App Secret
            access_token: 访问凭证（手动传入）
            is_lark: 是否使用 Lark (海外版)
            auth_mode: 认证模式 "tenant" (默认) 或 "oauth"
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.is_lark = is_lark
        self.auth_mode = auth_mode
        self._access_token = access_token
        self._authenticator = None  # OAuth2Authenticator 或 TenantAuthenticator
        self._sdk: Optional[FeishuSDK] = None

    @classmethod
    def from_token(cls, access_token: str) -> "FeishuExporter":
        """
        从已有 Token 创建导出器

        Args:
            access_token: 用户访问凭证

        Returns:
            FeishuExporter 实例
        """
        return cls(access_token=access_token)

    @property
    def sdk(self) -> FeishuSDK:
        """获取 SDK 实例（懒加载）"""
        if self._sdk is None:
            # 根据 auth_mode 确定 token 类型
            token_type = "tenant" if self.auth_mode == "tenant" else "user"
            self._sdk = FeishuSDK(token_type=token_type)
        return self._sdk

    def get_access_token(self) -> str:
        """
        获取访问凭证

        根据 auth_mode 选择认证方式：
        - tenant: 使用 tenant_access_token（默认，无需浏览器授权）
        - oauth: 使用 user_access_token（需要浏览器授权）
        """
        if self._access_token:
            return self._access_token

        if not self.app_id or not self.app_secret:
            raise ValueError("需要提供 access_token 或 (app_id + app_secret)")

        if self._authenticator is None:
            if self.auth_mode == "tenant":
                self._authenticator = TenantAuthenticator(
                    app_id=self.app_id,
                    app_secret=self.app_secret,
                    is_lark=self.is_lark,
                )
            else:
                self._authenticator = OAuth2Authenticator(
                    app_id=self.app_id,
                    app_secret=self.app_secret,
                    is_lark=self.is_lark,
                )

        # 根据认证器类型调用不同方法
        if isinstance(self._authenticator, TenantAuthenticator):
            return self._authenticator.get_token()
        else:
            return self._authenticator.authenticate()

    def parse_url(self, url: str) -> NodeInfo:
        """
        解析飞书文档 URL

        Args:
            url: 飞书文档 URL

        Returns:
            NodeInfo 文档信息

        Raises:
            ValueError: 不支持的 URL 格式
        """
        for doc_type, pattern in self.URL_PATTERNS.items():
            match = pattern.search(url)
            if match:
                # 支持多个域名，ID 可能在 group(1) 或 group(2)
                doc_id = match.group(1) or match.group(2)
                return NodeInfo(node_type=doc_type, node_token=doc_id)

        raise ValueError(f"不支持的 URL 格式: {url}")

    def export(
            self,
            url: str,
            output_dir: str | Path = ".",
            filename: Optional[str] = None,
            table_format: Literal["html", "md"] = "md",
            sheet_value_mode: Literal["display", "formula"] = "display",
            silent: bool = False,
            progress_callback=None,
            with_block_ids: bool = False,
            export_board_metadata: bool = False,
    ) -> Path:
        """
        导出飞书文档为 Markdown 文件

        Args:
            url: 飞书文档 URL
            output_dir: 输出目录
            filename: 输出文件名（不含扩展名），默认使用文档标题
            table_format: 表格输出格式 ("html" 或 "md")
            sheet_value_mode: 电子表格单元格值导出模式 ("display" 或 "formula")
            silent: 是否静默模式
            progress_callback: 进度回调
            with_block_ids: 是否在导出的 Markdown 中嵌入 Block ID 注释
            export_board_metadata: 是否导出画板节点元数据

        Returns:
            输出文件路径
        """
        # 1. 解析 URL 和获取标题
        self._set_document_domain_from_url(url)
        doc_info = self.parse_url(url)
        access_token = self.get_access_token()
        doc_title = self._get_document_title(doc_info, access_token)
        output_filename = filename or self._sanitize_filename(doc_title)

        if not silent:
            console.print(f"[blue]> 文档类型:[/blue] {doc_info.node_type}")
            console.print(f"[blue]> 文档 ID:[/blue]  {doc_info.node_token}")
            console.print(f"[blue]> 文档标题:[/blue] {doc_title}")

        # 2. 准备输出目录和资源目录
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 资源目录：以文件名命名的文件夹
        assets_dir = output_dir / output_filename
        assets_dir.mkdir(parents=True, exist_ok=True)

        # 3. 导出内容（核心逻辑）
        if not silent:
            console.print("[yellow]> 正在解析文档...[/yellow]")
        content = self._parse_document(
            doc_info, access_token, table_format, sheet_value_mode, assets_dir,
            silent=silent, progress_callback=progress_callback,
            with_block_ids=with_block_ids,
            export_board_metadata=export_board_metadata
        )

        # 4. 保存到文件
        output_path = output_dir / f"{output_filename}.md"
        output_path.write_text(content, encoding="utf-8")

        console.print(f"[green]✓ 导出成功:[/green] {output_path}")

        # 如果资源目录为空，删除它
        if not any(assets_dir.iterdir()):
            assets_dir.rmdir()
        elif not silent:
            console.print(f"[green]✓ 资源目录:[/green] {assets_dir}")

        return output_path

    def export_content(
            self,
            url: str,
            table_format: Literal["html", "md"] = "html",
            sheet_value_mode: Literal["display", "formula"] = "display",
            export_board_metadata: bool = False,
    ) -> str:
        """
        导出飞书文档为 Markdown 字符串（不保存到文件）

        Args:
            url: 飞书文档 URL
            table_format: 表格输出格式
            sheet_value_mode: 电子表格单元格值导出模式
            export_board_metadata: 是否导出画板节点元数据

        Returns:
            Markdown 格式的文档内容
        """
        doc_info = self.parse_url(url)
        self._set_document_domain_from_url(url)
        access_token = self.get_access_token()
        return self._parse_document(
            doc_info, access_token, table_format, sheet_value_mode, assets_dir=None,
            export_board_metadata=export_board_metadata
        )

    def export_content_with_browser(
            self,
            url: str,
            headless: bool = True,
            timeout_ms: int = 30000,
            storage_state_path: Optional[str] = None,
            executable_path: Optional[str] = None,
    ) -> str:
        """
        使用浏览器上下文回退导出 Markdown 字符串。

        适用于公开文档，或用户已通过 storage_state 提供可读会话的场景。
        """
        from feishu_docx.core.browser_export import BrowserMarkdownExporter

        exporter = BrowserMarkdownExporter(
            headless=headless,
            timeout_ms=timeout_ms,
            storage_state_path=storage_state_path,
            executable_path=executable_path,
        )
        return exporter.export_content(url)

    def export_with_browser(
            self,
            url: str,
            output_dir: str | Path = ".",
            filename: Optional[str] = None,
            headless: bool = True,
            timeout_ms: int = 30000,
            storage_state_path: Optional[str] = None,
            executable_path: Optional[str] = None,
    ) -> Path:
        """
        使用浏览器上下文回退导出 Markdown 文件。

        这是实验能力，不依赖飞书开放平台 Token。
        """
        from feishu_docx.core.browser_export import BrowserMarkdownExporter

        exporter = BrowserMarkdownExporter(
            headless=headless,
            timeout_ms=timeout_ms,
            storage_state_path=storage_state_path,
            executable_path=executable_path,
        )
        return exporter.export(
            url=url,
            output_dir=output_dir,
            filename=filename,
        )

    def _parse_document(
            self,
            doc_info: NodeInfo,
            access_token: str,
            table_format: Literal["html", "md"],
            sheet_value_mode: Literal["display", "formula"],
            assets_dir: Optional[Path],
            silent: bool = False,
            progress_callback=None,
            with_block_ids: bool = False,
            export_board_metadata: bool = False,
    ) -> str:
        """
        核心解析逻辑

        Args:
            doc_info: 文档信息
            access_token: 访问凭证
            table_format: 表格输出格式
            sheet_value_mode: 电子表格单元格值导出模式
            assets_dir: 资源目录（图片等），None 时使用临时目录
            silent: 是否静默模式
            progress_callback: 进度回调
            with_block_ids: 是否嵌入 Block ID 注释
            export_board_metadata: 是否导出画板节点元数据

        Returns:
            Markdown 内容
        """
        # 如果有资源目录，更新 SDK 的临时目录
        if assets_dir:
            self.sdk.temp_dir = assets_dir

        if doc_info.node_type in ("doc", "docx"):
            parser = DocumentParser(
                document_id=doc_info.node_token,
                user_access_token=access_token,
                table_mode=table_format,
                sheet_value_mode=sheet_value_mode,
                sdk=self.sdk,
                assets_dir=assets_dir,
                silent=silent,
                progress_callback=progress_callback,
                with_block_ids=with_block_ids,
                export_board_metadata=export_board_metadata,
            )
            return parser.parse()

        elif doc_info.node_type == "sheet":
            parser = SheetParser(
                spreadsheet_token=doc_info.node_token,
                user_access_token=access_token,
                table_mode=table_format,
                sheet_value_mode=sheet_value_mode,
                sdk=self.sdk,
                silent=silent,
                progress_callback=progress_callback,
            )
            return parser.parse()

        elif doc_info.node_type == "bitable":
            parser = BitableParser(
                app_token=doc_info.node_token,
                user_access_token=access_token,
                table_mode=table_format,
                sdk=self.sdk,
                silent=silent,
                progress_callback=progress_callback,
            )
            return parser.parse()

        elif doc_info.node_type == "wiki":
            # Wiki 需要先获取实际文档信息
            node = self.sdk.wiki.get_node_metadata(doc_info.node_token, access_token)
            obj_type = node.obj_type  # "doc", "sheet", "bitable"

            if obj_type in ("doc", "docx"):
                parser = DocumentParser(
                    document_id=node.obj_token,
                    user_access_token=access_token,
                    table_mode=table_format,
                    sheet_value_mode=sheet_value_mode,
                    sdk=self.sdk,
                    assets_dir=assets_dir,
                    silent=silent,
                    progress_callback=progress_callback,
                    export_board_metadata=export_board_metadata,
                )
                return parser.parse()
            elif obj_type == "sheet":
                parser = SheetParser(
                    spreadsheet_token=node.obj_token,
                    user_access_token=access_token,
                    table_mode=table_format,
                    sheet_value_mode=sheet_value_mode,
                    sdk=self.sdk,
                    silent=silent,
                    progress_callback=progress_callback,
                )
                return parser.parse()
            elif obj_type == "bitable":
                parser = BitableParser(
                    app_token=node.obj_token,
                    user_access_token=access_token,
                    table_mode=table_format,
                    sdk=self.sdk,
                    silent=silent,
                    progress_callback=progress_callback,
                )
                return parser.parse()
            else:
                raise ValueError(f"不支持的 Wiki 节点类型: {obj_type}")

        else:
            raise ValueError(f"不支持的文档类型: {doc_info.node_type}")

    def _get_document_title(self, doc_info: NodeInfo, access_token: str) -> str:
        """获取文档标题"""
        try:
            if doc_info.node_type in ("doc", "docx"):
                info = self.sdk.docx.get_document_info(doc_info.node_token, access_token)
                return info.get("title", doc_info.node_token)
            elif doc_info.node_type == "sheet":
                info = self.sdk.sheet.get_spreadsheet_info(doc_info.node_token, access_token)
                return info.get("title", doc_info.node_token)
            elif doc_info.node_type == "bitable":
                info = self.sdk.bitable.get_bitable_info(doc_info.node_token, access_token)
                return info.get("title", doc_info.node_token)
            elif doc_info.node_type == "wiki":
                node = self.sdk.wiki.get_node_metadata(doc_info.node_token, access_token)
                return node.title or doc_info.node_token
        except Exception:  # noqa
            pass
        return doc_info.node_token

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """清理文件名，移除非法字符"""
        import re
        name = re.sub(r"\s+", " ", name).strip()
        name = re.sub(r'[<>:"/\\|?*]', '_', name)
        name = name.strip('. ')
        return name or "untitled"

    def _set_document_domain_from_url(self, url: str) -> None:
        """从文档 URL 提取域名并写入 SDK"""
        self.sdk.set_document_url(url)
        try:
            parsed = urlparse(url)
            host = parsed.netloc.strip().lower()
            if host:
                host = host.split("@")[-1].split(":")[0]
                parts = host.split(".")
                domain = None
                for candidate in ("feishu", "larksuite", "larkoffice"):
                    if candidate in parts:
                        domain = candidate
                        break
                self.sdk.set_document_domain(domain or "feishu")
            else:
                self.sdk.set_document_domain("feishu")
        except Exception:
            self.sdk.set_document_domain("feishu")

    # ==========================================================================
    # 知识空间批量导出
    # ==========================================================================

    def export_wiki_space(
            self,
            space_id_or_url: str,
            output_dir: Path | str,
            max_depth: int = 3,
            parent_node_token: Optional[str] = None,
            silent: bool = False,
            progress_callback=None,
            table_format: Literal["html", "md"] = "md",
            sheet_value_mode: Literal["display", "formula"] = "display",
            with_block_ids: bool = False,
            export_board_metadata: bool = False,

    ) -> dict:
        """
        批量导出知识空间下的所有文档

        Args:
            space_id_or_url: 知识空间 ID 或 Wiki URL（自动解析，只导出输入URL子节点下的文档）
            output_dir: 输出目录
            max_depth: 最大遍历深度（默认 3）
            parent_node_token: 可选，从指定父节点开始导出
            silent: 是否静默模式
            progress_callback: 进度回调函数 (exported, failed, current_title)
            table_format: 表格输出格式
            sheet_value_mode: 电子表格单元格值导出模式
            with_block_ids: 是否嵌入 Block ID 注释
            export_board_metadata: 是否导出画板节点元数据

        Returns:
            dict: {"exported": int, "failed": int, "paths": list[Path]}

        使用示例:

            exporter = FeishuExporter(app_id="xxx", app_secret="xxx")
            result = exporter.export_wiki_space(
                space_id="xxx",
                output_dir="./wiki_backup",
                max_depth=3,
            )
            print(f"导出 {result['exported']} 个文档")
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        access_token = self.get_access_token()
        base_url = self._resolve_wiki_export_base_url(space_id_or_url)

        # 解析输入：支持 URL 或 space_id
        space_id = space_id_or_url
        save_dir = None
        if space_id_or_url.startswith(("http://", "https://")):
            space_id, save_dir, parent_node_token = self._resolve_wiki_space_scope(
                wiki_url=space_id_or_url,
                access_token=access_token,
                explicit_parent_node_token=parent_node_token,
                silent=silent,
            )
        else:
            self.sdk.set_document_domain("larkoffice" if self.is_lark else "feishu")

        # 获取知识空间信息
        try:
            space_info = self.sdk.wiki.get_space_info(space_id, access_token)
            space_name = space_info.name if space_info.name else space_id
        except Exception:
            space_name = space_id

        # 在 output_dir 下创建以 space_name 命名的目录
        if save_dir:
            space_name = save_dir
        space_name = self._sanitize_filename(space_name)
        space_dir = output_dir / space_name
        space_dir.mkdir(parents=True, exist_ok=True)

        if not silent:
            console.print(f"[blue]> 知识空间:[/blue] {space_name}")
            console.print(f"[blue]> 输出目录:[/blue] {space_dir}")

        result = {"exported": 0, "failed": 0, "paths": [], "space_name": space_name, "space_dir": space_dir}

        def traverse(parent_token: Optional[str], depth: int, current_path: Path):
            """递归遍历节点"""
            if depth > max_depth:
                return

            # 获取子节点列表
            nodes = self.sdk.wiki.get_all_space_nodes(
                space_id=space_id,
                access_token=access_token,
                parent_node_token=parent_token,
            )

            if not nodes:
                return

            for node in nodes:
                node_token = node.node_token
                obj_type = node.obj_type
                obj_token = node.obj_token
                title = node.title or node_token
                has_child = node.has_child

                # 清理文件名中的非法字符
                safe_title = self._sanitize_filename(title)


                # 判断是否为文档类型
                if obj_type in ["doc", "docx", "sheet" , "bitable"]:
                    # 构建文档 URL
                    if obj_type == "bitable":
                        url = f"{base_url}/wiki/{node_token}"
                    else:
                        url = f"{base_url}/{obj_type}/{obj_token}"

                    if has_child:
                        # 有子节点：创建子目录并导出
                        doc_dir = current_path / safe_title
                        doc_dir.mkdir(parents=True, exist_ok=True)

                        try:
                            path = self.export(
                                url=url,
                                output_dir=doc_dir,
                                filename=safe_title,
                                table_format=table_format,
                                sheet_value_mode=sheet_value_mode,
                                silent=True,
                                with_block_ids=with_block_ids,
                                export_board_metadata=export_board_metadata,
                            )
                            result["exported"] += 1
                            result["paths"].append(path)

                            if not silent:
                                console.print(f"[green]✓[/green] {safe_title}")

                            if progress_callback:
                                progress_callback(result["exported"], result["failed"], safe_title)

                        except Exception as e:
                            result["failed"] += 1
                            if not silent:
                                console.print(f"[red]✗[/red] {safe_title}: {e}")

                        # 递归处理子节点
                        traverse(node_token, depth + 1, doc_dir)

                    else:
                        # 无子节点：直接导出到当前目录
                        try:
                            path = self.export(
                                url=url,
                                output_dir=current_path,
                                filename=safe_title,
                                table_format=table_format,
                                sheet_value_mode=sheet_value_mode,
                                silent=silent,
                                with_block_ids=with_block_ids,
                                export_board_metadata=export_board_metadata,
                            )
                            result["exported"] += 1
                            result["paths"].append(path)

                            if not silent:
                                console.print(f"[green]✓[/green] {safe_title}")

                            if progress_callback:
                                progress_callback(result["exported"], result["failed"], safe_title)

                        except Exception as e:
                            result["failed"] += 1
                            if not silent:
                                console.print(f"[red]✗[/red] {safe_title}: {e}")

                elif has_child:
                    # 纯目录节点（非文档但有子节点）
                    sub_dir = current_path / safe_title
                    sub_dir.mkdir(parents=True, exist_ok=True)

                    if not silent:
                        console.print(f"[dim]📁 {safe_title}/[/dim]")

                    traverse(node_token, depth + 1, sub_dir)

        # 开始遍历
        traverse(parent_node_token, 0, space_dir)

        return result

    def _resolve_wiki_space_scope(
            self,
            wiki_url: str,
            access_token: str,
            explicit_parent_node_token: Optional[str],
            silent: bool,
    ) -> tuple[str, Optional[str], Optional[str]]:
        """解析 Wiki URL 对应的知识空间和导出范围。"""
        try:
            doc_info = self.parse_url(wiki_url)
        except ValueError as e:
            raise ValueError(f"URL 格式错误: {e}")

        if doc_info.node_type != "wiki":
            raise ValueError(f"输入的不是 Wiki 链接（类型: {doc_info.node_type}）")

        node_info = self.sdk.wiki.get_node_by_token(
            token=doc_info.node_token,
            access_token=access_token,
        )

        if not node_info or not node_info.space_id:
            raise ValueError("无法获取知识空间信息")

        resolved_parent_node_token = explicit_parent_node_token
        if resolved_parent_node_token is None:
            # 知识空间首页常表现为“无父节点且无子节点”的占位 Wiki URL。
            # 这类 URL 应回退为导出整个 space 的顶层节点，而不是错误地按 node_token 过滤。
            if node_info.has_child:
                resolved_parent_node_token = doc_info.node_token
            elif getattr(node_info, "parent_node_token", ""):
                resolved_parent_node_token = doc_info.node_token
            else:
                resolved_parent_node_token = None

        if not silent:
            console.print(f"[green]✓ 从 URL 解析得到 space_id:[/green] {node_info.space_id}")
        self._set_document_domain_from_url(wiki_url)
        return node_info.space_id, node_info.title or node_info.node_token, resolved_parent_node_token

    def _resolve_wiki_export_base_url(self, space_id_or_url: str) -> str:
        """解析批量导出时用于拼接子文档链接的基础 URL。"""
        if space_id_or_url.startswith(("http://", "https://")):
            parsed = urlparse(space_id_or_url)
            if parsed.scheme and parsed.netloc:
                return f"{parsed.scheme}://{parsed.netloc}"
        if self.is_lark:
            return "https://my.larkoffice.com"
        return "https://my.feishu.cn"
