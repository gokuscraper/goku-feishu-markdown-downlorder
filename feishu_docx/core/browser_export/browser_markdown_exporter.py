# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：browser_markdown_exporter.py
# @Date   ：2026/03/30 20:25
# @Author ：leemysw
# 2026/03/30 20:25   Create
# =====================================================
"""浏览器 Markdown 导出器。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, TypeVar

try:
    from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
except ImportError:  # pragma: no cover - 按需导入
    Browser = Any  # type: ignore[misc,assignment]
    BrowserContext = Any  # type: ignore[misc,assignment]
    Page = Any  # type: ignore[misc,assignment]
    sync_playwright = None

from feishu_docx.core.browser_export.browser_asset_downloader import BrowserAssetDownloader
from feishu_docx.core.browser_export.browser_document_extractor import BrowserDocumentExtractor
from feishu_docx.core.browser_export.browser_fallback_error import BrowserFallbackError
from feishu_docx.core.browser_export.browser_markdown_parser import BrowserMarkdownParser

T = TypeVar("T")


class BrowserMarkdownExporter:
    """基于浏览器上下文的实验性 Markdown 导出器。"""

    def __init__(
            self,
            headless: bool = True,
            timeout_ms: int = 30000,
            scroll_rounds: int = 100,
            scroll_wait_ms: int = 400,
            storage_state_path: str | None = None,
            executable_path: str | None = None,
    ):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.storage_state_path = storage_state_path
        self.executable_path = executable_path
        self.document_extractor = BrowserDocumentExtractor(
            timeout_ms=timeout_ms,
            scroll_rounds=scroll_rounds,
            scroll_wait_ms=scroll_wait_ms,
        )
        self.markdown_parser = BrowserMarkdownParser()
        self.asset_downloader = BrowserAssetDownloader()

    def export_content(self, url: str) -> str:
        """通过浏览器上下文导出 Markdown 字符串。"""
        return self._run_with_page(
            url=url,
            handler=lambda page: self._export_content_from_page(page),
        )

    def export(
            self,
            url: str,
            output_dir: str | Path = ".",
            filename: str | None = None,
    ) -> Path:
        """导出 Markdown 文件与相关资源。"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        return self._run_with_page(
            url=url,
            handler=lambda page: self._export_file_from_page(
                page=page,
                output_dir=output_dir,
                filename=filename,
            ),
        )

    def _export_content_from_page(self, page: Page) -> str:
        """从页面导出 Markdown 字符串。"""
        model = self.document_extractor.extract_from_page(page)
        return self.markdown_parser.parse_document(model)

    def _export_file_from_page(
            self,
            page: Page,
            output_dir: Path,
            filename: str | None = None,
    ) -> Path:
        """从页面导出文件。"""
        model = self.document_extractor.extract_from_page(page)
        markdown = self.markdown_parser.parse_document(model)
        save_name = filename or self._sanitize_filename(model.title)
        assets_dir = output_dir / save_name
        markdown = self.asset_downloader.download(page, model, assets_dir, markdown)

        output_path = output_dir / f"{save_name}.md"
        output_path.write_text(markdown, encoding="utf-8")

        if assets_dir.exists() and not any(assets_dir.rglob("*")):
            assets_dir.rmdir()
        return output_path

    def _run_with_page(self, url: str, handler: Callable[[Page], T]) -> T:
        """统一管理浏览器生命周期。"""
        self._ensure_playwright()

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=self.headless,
                executable_path=self.executable_path,
            )
            context = self._create_context(browser)
            page = context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                return handler(page)
            finally:
                context.close()
                browser.close()

    def _create_context(self, browser: Browser) -> BrowserContext:
        """创建浏览器上下文。"""
        storage_state = self.storage_state_path if self.storage_state_path else None
        return browser.new_context(
            storage_state=storage_state,
            ignore_https_errors=True,
        )

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        normalized = re.sub(r"\s+", " ", name).strip()
        return re.sub(r'[<>:"/\\\\|?*]', "_", normalized).strip(". ") or "untitled"

    @staticmethod
    def _ensure_playwright() -> None:
        if sync_playwright is None:
            raise BrowserFallbackError("当前环境未安装 playwright，无法使用浏览器回退导出")
