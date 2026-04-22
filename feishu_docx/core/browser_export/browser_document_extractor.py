# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：browser_document_extractor.py
# @Date   ：2026/03/30 20:25
# @Author ：leemysw
# 2026/03/30 20:25   Create
# =====================================================
"""浏览器文档提取器。"""

from __future__ import annotations

from typing import Any

try:
    from playwright.sync_api import Page
except ImportError:  # pragma: no cover - 按需导入
    Page = Any  # type: ignore[misc,assignment]

from feishu_docx.core.browser_export.browser_document_model import BrowserDocumentModel
from feishu_docx.core.browser_export.browser_fallback_error import BrowserFallbackError


class BrowserDocumentExtractor:
    """从浏览器页面抽取飞书块树。"""

    WAIT_PAGE_READY_JS = """
    () => {
      if (!window.PageMain?.blockManager?.rootBlockModel) {
        return false;
      }

      const root = window.PageMain.blockManager.rootBlockModel;
      const children = Array.isArray(root.children) ? root.children : [];

      return children.every((block) => {
        const snapshotType = block?.snapshot?.type;
        const blockType = block?.type;
        const ready = snapshotType !== 'pending';
        const syncedReady = blockType !== 'synced_reference' || block?.isAllDataReady;
        const whiteboardReady = blockType !== 'fallback' || snapshotType !== 'whiteboard';
        return ready && syncedReady && whiteboardReady;
      });
    }
    """

    SERIALIZE_BLOCK_TREE_JS = """
    () => {
      const trimCaption = (caption) => {
        return caption?.text?.initialAttributedTexts?.text?.[0] ?? '';
      };

      const safeJson = (value) => {
        try {
          return JSON.parse(JSON.stringify(value ?? null));
        } catch (error) {
          return null;
        }
      };

      const simplifyOps = (ops) => {
        if (!Array.isArray(ops)) {
          return [];
        }
        return ops.map((op) => ({
          insert: typeof op?.insert === 'string' ? op.insert : '',
          attributes: safeJson(op?.attributes ?? {}),
        }));
      };

      const simplifySnapshot = (block) => {
        const snapshot = block?.snapshot ?? {};
        const base = { type: snapshot.type ?? block?.type ?? '' };

        switch (block?.type) {
          case 'ordered':
            return { ...base, seq: snapshot.seq ?? '' };
          case 'todo':
            return { ...base, done: Boolean(snapshot.done) };
          case 'table':
            return {
              ...base,
              rows_id: Array.isArray(snapshot.rows_id) ? snapshot.rows_id : [],
              columns_id: Array.isArray(snapshot.columns_id) ? snapshot.columns_id : [],
            };
          case 'grid_column':
            return { ...base, width_ratio: snapshot.width_ratio ?? null };
          case 'image':
            return {
              ...base,
              image: {
                token: snapshot.image?.token ?? '',
                name: snapshot.image?.name ?? '',
                caption: trimCaption(snapshot.image?.caption),
              },
            };
          case 'file':
            return {
              ...base,
              file: {
                name: snapshot.file?.name ?? '',
                token: snapshot.file?.token ?? '',
              },
            };
          case 'iframe':
            return {
              ...base,
              iframe: {
                height: snapshot.iframe?.height ?? null,
                component: {
                  url: snapshot.iframe?.component?.url ?? '',
                },
              },
            };
          case 'whiteboard':
            return {
              ...base,
              whiteboard: {
                caption: trimCaption(snapshot.caption),
              },
            };
          case 'diagram':
            return {
              ...base,
              diagram: {},
            };
          case 'isv':
            return {
              ...base,
              block_type_id: snapshot.block_type_id ?? '',
              data: safeJson(snapshot.data),
            };
          default:
            return base;
        }
      };

      const simplifyBlock = (block) => {
        if (!block) {
          return null;
        }

        const syncedChildren = Array.isArray(block?.innerBlockManager?.rootBlockModel?.children)
          ? block.innerBlockManager.rootBlockModel.children.map(simplifyBlock).filter(Boolean)
          : null;

        return {
          id: block.id ?? null,
          type: block.type ?? block?.snapshot?.type ?? '',
          record_id: block?.record?.id ?? '',
          zone_state: block?.zoneState
            ? {
                all_text: block.zoneState.allText ?? '',
                content: {
                  ops: simplifyOps(block.zoneState?.content?.ops ?? []),
                },
              }
            : null,
          snapshot: simplifySnapshot(block),
          children: Array.isArray(block.children)
            ? block.children.map(simplifyBlock).filter(Boolean)
            : [],
          synced_children: syncedChildren,
          is_all_data_ready: block?.isAllDataReady ?? null,
        };
      };

      const root = window.PageMain?.blockManager?.rootBlockModel;
      if (!root) {
        return null;
      }

      return {
        title: root?.zoneState?.allText ?? document.title ?? '',
        root: simplifyBlock(root),
      };
    }
    """

    def __init__(
            self,
            timeout_ms: int = 30000,
            scroll_rounds: int = 100,
            scroll_wait_ms: int = 400,
    ):
        self.timeout_ms = timeout_ms
        self.scroll_rounds = scroll_rounds
        self.scroll_wait_ms = scroll_wait_ms

    def extract_from_page(self, page: Page) -> BrowserDocumentModel:
        """从当前页面抽取文档模型。"""
        self._ensure_docx_page(page)
        self._prepare_page(page)
        payload = page.evaluate(self.SERIALIZE_BLOCK_TREE_JS)
        if not payload or not payload.get("root"):
            raise BrowserFallbackError("未能从当前页面提取飞书文档块树")
        return BrowserDocumentModel(
            title=str(payload.get("title") or "untitled").replace("\r", " ").replace("\n", " ").strip(),
            root=payload["root"],
        )

    def _ensure_docx_page(self, page: Page) -> None:
        """确认当前页面为新版 docx/wiki 页面。"""
        page.wait_for_function(
            "() => Boolean(window.PageMain || window.editor)",
            timeout=self.timeout_ms,
        )
        if page.evaluate("() => Boolean(window.editor && !window.PageMain)"):
            raise BrowserFallbackError("旧版 /doc/ 文档暂不支持浏览器回退导出")

    def _prepare_page(self, page: Page) -> None:
        """滚动页面，确保懒加载块尽量完成。"""
        if page.evaluate(self.WAIT_PAGE_READY_JS):
            return

        top = 0
        for _ in range(self.scroll_rounds):
            page.evaluate(
                """
                (nextTop) => {
                  const container = document.querySelector('#mainBox .bear-web-x-container');
                  if (container) {
                    container.scrollTo({ top: nextTop, behavior: 'instant' });
                  }
                }
                """,
                top,
            )
            page.wait_for_timeout(self.scroll_wait_ms)

            if page.evaluate(self.WAIT_PAGE_READY_JS):
                return

            top = page.evaluate(
                """
                () => {
                  const container = document.querySelector('#mainBox .bear-web-x-container');
                  return container ? container.scrollHeight : 0;
                }
                """
            )

        if not page.evaluate(self.WAIT_PAGE_READY_JS):
            raise BrowserFallbackError("页面仍有未加载完成的块，浏览器回退导出失败")
