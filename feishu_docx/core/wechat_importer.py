# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：wechat_importer.py
# @Date   ：2026/03/02 10:39
# @Author ：leemysw
# 2026/03/02 10:39   Create
# =====================================================
"""
微信公众号文章导入器

[INPUT]: 依赖 httpx, bs4
[OUTPUT]: 对外提供 WeChatArticleImporter
[POS]: core 模块的公众号文章抓取与 Markdown 转换能力
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import re
from concurrent.futures import as_completed, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup, Tag
from markdownify import markdownify


class WeChatImportError(RuntimeError):
    """微信公众号导入异常。"""


@dataclass
class CodeBlockData:
    """代码块数据。"""

    language: str
    code: str


@dataclass
class ArticleMetadata:
    """文章元数据。"""

    title: str
    author: str
    publish_time: str


@dataclass
class WeChatArticle:
    """导入后的文章信息。"""

    source_url: str
    title: str
    author: str
    publish_time: str
    markdown_content: str
    article_dir: Path
    downloaded_images: int


class WeChatArticleImporter:
    """微信公众号文章抓取器。"""

    URL_PREFIX = "https://mp.weixin.qq.com/"
    IMAGE_CONCURRENCY = 5
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    def __init__(
            self,
            workspace: Path,
            image_concurrency: int = IMAGE_CONCURRENCY,
            timeout: float = DEFAULT_TIMEOUT,
    ):
        """初始化导入器。

        Args:
            workspace: 临时工作目录。
            image_concurrency: 图片下载并发数。
            timeout: 网络请求超时（秒）。
        """
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.image_concurrency = max(1, image_concurrency)
        self.timeout = timeout

    def validate_url(self, url: str) -> None:
        """校验公众号文章 URL。"""
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.netloc != "mp.weixin.qq.com":
            raise WeChatImportError("请输入有效的微信公众号文章 URL（https://mp.weixin.qq.com/...）")

    def import_article(self, source_url: str) -> WeChatArticle:
        """抓取公众号文章并转换为 Markdown。"""
        self.validate_url(source_url)
        html = self._fetch_html(source_url)
        soup = BeautifulSoup(html, "html.parser")

        metadata = self._extract_metadata(soup, html)
        if not metadata.title:
            raise WeChatImportError("未能提取到文章标题，可能触发了验证码或访问受限")

        content_el = soup.select_one("#js_content")
        if not isinstance(content_el, Tag):
            raise WeChatImportError("未能提取到正文内容")

        code_blocks, image_urls = self._process_content_dom(soup, content_el)

        article_dir = self.workspace / self._safe_filename(metadata.title)
        images_dir = article_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        url_map = self._download_all_images(image_urls, images_dir)
        self._replace_image_sources(content_el, url_map)

        body_md = self._convert_to_markdown(str(content_el), code_blocks)
        final_md = self._build_markdown(metadata=metadata, source_url=source_url, body_md=body_md)

        return WeChatArticle(
            source_url=source_url,
            title=metadata.title,
            author=metadata.author,
            publish_time=metadata.publish_time,
            markdown_content=final_md,
            article_dir=article_dir,
            downloaded_images=len(url_map),
        )

    def save_markdown(self, article: WeChatArticle, filename: Optional[str] = None) -> Path:
        """保存文章 Markdown 到本地。

        Args:
            article: 导入后的文章对象。
            filename: 自定义文件名（不含扩展名）。

        Returns:
            保存后的 Markdown 文件路径。
        """
        md_filename = self._safe_filename(filename or article.title)
        md_path = article.article_dir / f"{md_filename}.md"
        md_path.write_text(article.markdown_content, encoding="utf-8")
        return md_path

    def _fetch_html(self, source_url: str) -> str:
        """抓取公众号文章 HTML。"""
        try:
            with httpx.Client(
                    headers=self.DEFAULT_HEADERS,
                    timeout=self.timeout,
                    follow_redirects=True,
            ) as client:
                response = client.get(source_url)
                if response.status_code in (403, 412):
                    raise WeChatImportError("微信反爬拦截，请稍后重试或更换网络环境")
                response.raise_for_status()
                return response.text
        except httpx.TimeoutException as exc:
            raise WeChatImportError("请求超时，请检查网络连接") from exc
        except httpx.HTTPStatusError as exc:
            raise WeChatImportError(f"抓取失败，HTTP 状态码: {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise WeChatImportError(f"抓取失败: {exc}") from exc

    def _extract_metadata(self, soup: BeautifulSoup, html: str) -> ArticleMetadata:
        """提取文章元数据。"""
        title = ""
        title_el = soup.select_one("#activity-name")
        if isinstance(title_el, Tag):
            title = title_el.get_text(strip=True)

        if not title:
            og_title = soup.select_one("meta[property='og:title']")
            if isinstance(og_title, Tag):
                title = (og_title.get("content") or "").strip()

        author = ""
        author_el = soup.select_one("#js_name")
        if isinstance(author_el, Tag):
            author = author_el.get_text(strip=True)

        publish_time = self._extract_publish_time(html)
        return ArticleMetadata(title=title, author=author, publish_time=publish_time)

    def _process_content_dom(self, soup: BeautifulSoup, content_el: Tag) -> tuple[List[CodeBlockData], List[str]]:
        """预处理正文 DOM：图片、代码块、噪声元素。"""
        # 处理微信懒加载图片。
        for img in content_el.select("img"):
            src = (img.get("data-src") or img.get("src") or "").strip()
            if src:
                img["src"] = self._normalize_image_url(src)

        code_blocks: List[CodeBlockData] = []
        for block in content_el.select(".code-snippet__fix"):
            for line_index in block.select(".code-snippet__line-index"):
                line_index.decompose()

            lang = ""
            pre_el = block.select_one("pre[data-lang]")
            if isinstance(pre_el, Tag):
                lang = (pre_el.get("data-lang") or "").strip()

            lines: List[str] = []
            for line_el in block.select("code"):
                line_text = line_el.get_text()
                if re.match(r"^[ce]?ounter\(line", line_text):
                    continue
                lines.append(line_text)

            if not lines:
                raw_text = block.get_text("\n", strip=True)
                if raw_text:
                    lines.append(raw_text)

            placeholder = f"CODEBLOCKPLACEHOLDER{len(code_blocks)}"
            code_blocks.append(CodeBlockData(language=lang, code="\n".join(lines).rstrip()))

            placeholder_tag = soup.new_tag("p")
            placeholder_tag.string = placeholder
            block.replace_with(placeholder_tag)

        for selector in ["script", "style", ".qr_code_pc", ".reward_area"]:
            for noise in content_el.select(selector):
                noise.decompose()

        image_urls: List[str] = []
        seen = set()
        for img in content_el.select("img[src]"):
            src = (img.get("src") or "").strip()
            if src and src not in seen:
                seen.add(src)
                image_urls.append(src)

        return code_blocks, image_urls

    def _download_all_images(self, image_urls: List[str], image_dir: Path) -> Dict[str, str]:
        """并发下载图片并返回映射。"""
        if not image_urls:
            return {}

        url_map: Dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=self.image_concurrency) as executor:
            futures = {
                executor.submit(self._download_image, url, image_dir, index + 1): url
                for index, url in enumerate(image_urls)
            }
            for future in as_completed(futures):
                remote_url = futures[future]
                try:
                    local_path = future.result()
                except Exception:
                    local_path = None
                if local_path:
                    url_map[remote_url] = local_path

        return url_map

    def _download_image(self, image_url: str, image_dir: Path, index: int) -> Optional[str]:
        """下载单张图片。"""
        try:
            normalized_url = self._normalize_image_url(image_url)
            ext = self._guess_image_ext(normalized_url)
            filename = f"img_{index:03d}.{ext}"
            local_path = image_dir / filename
            local_path.write_bytes(self._download_binary(normalized_url))
            return f"images/{filename}"
        except Exception:
            return None

    def _download_binary(self, url: str) -> bytes:
        """下载二进制内容。"""
        headers = dict(self.DEFAULT_HEADERS)
        headers["Referer"] = self.URL_PREFIX
        response = httpx.get(
            url,
            headers=headers,
            timeout=self.timeout,
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.content

    @staticmethod
    def _replace_image_sources(content_el: Tag, url_map: Dict[str, str]) -> None:
        """将正文内图片地址替换为本地绝对路径。"""
        for img in content_el.select("img[src]"):
            src = (img.get("src") or "").strip()
            local_path = url_map.get(src)
            if local_path:
                img["src"] = local_path

    @staticmethod
    def _convert_to_markdown(content_html: str, code_blocks: List[CodeBlockData]) -> str:
        """HTML 转 Markdown，并恢复代码块。"""
        markdown_text = markdownify(
            content_html,
            heading_style="ATX",
            bullets="-",
            strip=["script", "style"],
        )

        for index, code_block in enumerate(code_blocks):
            placeholder = f"CODEBLOCKPLACEHOLDER{index}"
            fenced = f"\n```{code_block.language}\n{code_block.code}\n```\n"
            markdown_text = markdown_text.replace(placeholder, fenced)

        markdown_text = markdown_text.replace("\u00a0", " ")
        markdown_text = re.sub(r"\n{4,}", "\n\n\n", markdown_text)
        markdown_text = re.sub(r"[ \t]+$", "", markdown_text, flags=re.MULTILINE)
        return markdown_text.strip() + "\n"

    @staticmethod
    def _build_markdown(metadata: ArticleMetadata, source_url: str, body_md: str) -> str:
        """组装最终 Markdown。"""
        header = [f"# {metadata.title}", ""]
        if metadata.author:
            header.append(f"> 公众号: {metadata.author}")
        if metadata.publish_time:
            header.append(f"> 发布时间: {metadata.publish_time}")
        header.append(f"> 原文链接: {source_url}")
        header.extend(["", "---", ""])
        return "\n".join(header) + body_md

    def _extract_publish_time(self, html: str) -> str:
        """从 HTML 提取发布时间。"""
        m1 = re.search(r"create_time\s*:\s*JsDecode\('([^']+)'\)", html)
        if m1:
            value = m1.group(1)
            ts = int(value) if value.isdigit() else 0
            if ts > 0:
                return self._format_timestamp(ts)
            return value

        m2 = re.search(r"create_time\s*:\s*'(\d+)'", html)
        if m2:
            return self._format_timestamp(int(m2.group(1)))

        return ""

    @staticmethod
    def _format_timestamp(timestamp: int) -> str:
        """秒级时间戳转换为北京时间。"""
        utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        beijing_tz = timezone(timedelta(hours=8))
        return utc_dt.astimezone(beijing_tz).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _normalize_image_url(image_url: str) -> str:
        """规范化图片 URL。"""
        if image_url.startswith("//"):
            return f"https:{image_url}"
        return image_url

    @staticmethod
    def _guess_image_ext(image_url: str) -> str:
        """猜测图片扩展名。"""
        fmt_match = re.search(r"[?&]wx_fmt=(\w+)", image_url)
        if fmt_match:
            return fmt_match.group(1).lower()

        ext_match = re.search(r"\.([A-Za-z0-9]{3,4})(?:\?|$)", image_url)
        if ext_match:
            return ext_match.group(1).lower()

        return "png"

    @staticmethod
    def _safe_filename(filename: str, max_len: int = 80) -> str:
        """生成安全文件名。"""
        safe = re.sub(r"[/\\?%*:|\"<>]", "_", filename).strip()
        if not safe:
            safe = "wechat_article"
        return safe[:max_len]
