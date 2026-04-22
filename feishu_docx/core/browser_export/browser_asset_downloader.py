# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：browser_asset_downloader.py
# @Date   ：2026/03/30 20:25
# @Author ：leemysw
# 2026/03/30 20:25   Create
# =====================================================
"""浏览器资源下载器。"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from playwright.sync_api import Page
except ImportError:  # pragma: no cover - 按需导入
    Page = Any  # type: ignore[misc,assignment]


class BrowserAssetDownloader:
    """下载浏览器页面中的图片、附件、白板和图表资源。"""

    DOWNLOAD_ASSET_JS = """
    async (asset) => {
      const findBlock = (block, targetId) => {
        if (!block) {
          return null;
        }
        if (block.id === targetId) {
          return block;
        }

        const children = Array.isArray(block.children) ? block.children : [];
        for (const child of children) {
          const found = findBlock(child, targetId);
          if (found) {
            return found;
          }
        }

        const syncedChildren = Array.isArray(block?.innerBlockManager?.rootBlockModel?.children)
          ? block.innerBlockManager.rootBlockModel.children
          : [];
        for (const child of syncedChildren) {
          const found = findBlock(child, targetId);
          if (found) {
            return found;
          }
        }

        return null;
      };

      const toBase64 = async (blob) => {
        return await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => {
            const result = String(reader.result || '');
            const index = result.indexOf(',');
            resolve(index >= 0 ? result.slice(index + 1) : result);
          };
          reader.onerror = () => reject(reader.error);
          reader.readAsDataURL(blob);
        });
      };

      const extensionFromMime = (mimeType, fallback) => {
        const mapping = {
          'image/png': '.png',
          'image/jpeg': '.jpg',
          'image/jpg': '.jpg',
          'image/gif': '.gif',
          'image/webp': '.webp',
          'image/svg+xml': '.svg',
          'application/pdf': '.pdf',
        };
        return mapping[mimeType] || fallback;
      };

      const buildFileUrl = (token, recordId) => {
        const hostname = window.globalConfig?.drive_api?.[0];
        if (!hostname) {
          throw new Error('Failed to resolve file download url');
        }

        const url = new URL('https://' + hostname + '/space/api/box/stream/download/all/' + token);
        url.searchParams.set('mount_node_token', recordId);
        url.searchParams.set('mount_point', 'docx_file');
        url.searchParams.set(
          'synced_block_host_token',
          window.location.pathname.split('/').at(-1) ?? '',
        );
        url.searchParams.set('synced_block_host_type', '22');
        return url.toString();
      };

      const blobFromImage = async (block) => {
        const image = block?.snapshot?.image;
        if (!image || !block?.imageManager?.fetch) {
          return null;
        }

        const sources = await new Promise((resolve, reject) => {
          block.imageManager
            .fetch({ token: image.token, isHD: true, fuzzy: false }, {}, resolve)
            .catch(reject);
        });

        if (!sources?.src) {
          return null;
        }

        const response = await fetch(sources.src, { credentials: 'include' });
        if (!response.ok) {
          throw new Error('image download failed');
        }

        const blob = await response.blob();
        const fallbackExt = extensionFromMime(blob.type || '', '.png');
        return {
          base64: await toBase64(blob),
          file_name: image.name || `image-${block.id}${fallbackExt}`,
        };
      };

      const blobFromFile = async (block) => {
        const file = block?.snapshot?.file;
        if (!file?.token) {
          return null;
        }

        const response = await fetch(
          buildFileUrl(file.token, block?.record?.id ?? ''),
          {
            method: 'GET',
            credentials: 'include',
          },
        );
        if (!response.ok) {
          throw new Error('file download failed');
        }

        const blob = await response.blob();
        const fallbackExt = extensionFromMime(blob.type || '', '');
        return {
          base64: await toBase64(blob),
          file_name: file.name || `file-${block.id}${fallbackExt}`,
        };
      };

      const blobFromWhiteboard = async (block) => {
        if (!block?.whiteboardBlock) {
          return null;
        }

        const padding = 24;
        const ratio = window.devicePixelRatio || 1;
        const backgroundColor = '#ffffff';

        const toCanvasBlob = async (canvas) => {
          return await new Promise((resolve) => {
            canvas.toBlob(resolve, 'image/png');
          });
        };

        let ratioApp = block.whiteboardBlock?.abilityKit?.getRatioApp?.();
        if (ratioApp?.app) {
          const bounds = ratioApp.app.application.nodeManager.getNodesBounds();
          bounds.maxX += padding;
          bounds.minX -= padding;
          bounds.maxY += padding;
          bounds.minY -= padding;
          const canvas = ratioApp.app.renderManager.getImageOffscreenCanvas(
            bounds,
            ratio,
            backgroundColor,
          );
          if (!canvas) {
            return null;
          }
          const blob = await toCanvasBlob(canvas);
          if (!blob) {
            return null;
          }
          return {
            base64: await toBase64(blob),
            file_name: `whiteboard-${block.id}.png`,
          };
        }

        ratioApp = block.whiteboardBlock?.isolateEnv?.getRatioApp?.();
        const wrapper = await ratioApp?.ratioAppProxy?.getOriginImageDataByNodeId?.(
          padding,
          [''],
          false,
          ratio,
        );
        if (!wrapper?.data) {
          return null;
        }

        const imageData = wrapper.data;
        const canvas = document.createElement('canvas');
        canvas.width = imageData.width;
        canvas.height = imageData.height;
        const ctx = canvas.getContext('2d');
        if (!ctx) {
          wrapper.release?.();
          return null;
        }
        ctx.putImageData(imageData, 0, 0);
        const blob = await toCanvasBlob(canvas);
        wrapper.release?.();
        if (!blob) {
          return null;
        }
        return {
          base64: await toBase64(blob),
          file_name: `whiteboard-${block.id}.png`,
        };
      };

      const blobFromDiagram = async (block) => {
        const blockView = block?.blockManager?.getBlockViewByBlockId?.(block.id);
        const svgElement = blockView?.getSvg?.();
        if (!svgElement) {
          return null;
        }

        const svgText = new XMLSerializer().serializeToString(svgElement);
        const blob = new Blob([svgText], { type: 'image/svg+xml' });
        return {
          base64: await toBase64(blob),
          file_name: `diagram-${block.id}.svg`,
        };
      };

      const root = window.PageMain?.blockManager?.rootBlockModel;
      if (!root) {
        return null;
      }

      const block = findBlock(root, asset.block_id);
      if (!block) {
        return null;
      }

      switch (asset.asset_type) {
        case 'image':
          return await blobFromImage(block);
        case 'file':
          return await blobFromFile(block);
        case 'whiteboard':
          return await blobFromWhiteboard(block);
        case 'diagram':
          return await blobFromDiagram(block);
        default:
          return null;
      }
    }
    """

    def __init__(self):
        self._used_names: set[str] = set()

    def download(self, page: Page, model: Any, assets_dir: Path, markdown: str) -> str:
        """下载所有资源并回写 Markdown 路径。"""
        assets = self._collect_assets(model.root)
        if not assets:
            return markdown

        # 每次导出前重置文件名占用集合，避免跨文档导出时污染命名。
        self._used_names.clear()
        assets_dir.mkdir(parents=True, exist_ok=True)
        rewritten = markdown
        for asset in assets:
            relative_path = self._download_single_asset(page, asset, assets_dir)
            if not relative_path:
                continue
            rewritten = rewritten.replace(asset["placeholder"], relative_path)
        return rewritten

    def _download_single_asset(self, page: Page, asset: dict[str, Any], assets_dir: Path) -> str | None:
        """下载单个资源并返回相对路径。"""
        payload = page.evaluate(self.DOWNLOAD_ASSET_JS, asset)
        if not payload or not payload.get("base64") or not payload.get("file_name"):
            return None

        filename = self._unique_filename(self._sanitize_filename(str(payload["file_name"])))
        target_path = assets_dir / filename
        target_path.write_bytes(self._decode_base64(str(payload["base64"])))
        return f"{assets_dir.name}/{filename}"

    def _collect_assets(self, block: dict[str, Any]) -> list[dict[str, Any]]:
        """递归收集资源块。"""
        assets: list[dict[str, Any]] = []
        block_type = block.get("type") or ""
        block_id = block.get("id")
        if block_type in {"image", "file", "whiteboard", "diagram"} and block_id is not None:
            assets.append(
                {
                    "asset_type": block_type,
                    "block_id": block_id,
                    "placeholder": f"browser-asset://{block_type}/{block_id}",
                }
            )

        for child in self._iter_children(block):
            assets.extend(self._collect_assets(child))
        return assets

    def _unique_filename(self, filename: str) -> str:
        """生成唯一文件名。"""
        candidate = filename
        index = 1
        stem, suffix = self._split_filename(filename)
        while candidate in self._used_names:
            candidate = f"{stem}-{index}{suffix}"
            index += 1
        self._used_names.add(candidate)
        return candidate

    @staticmethod
    def _split_filename(filename: str) -> tuple[str, str]:
        dot_index = filename.rfind(".")
        if dot_index == -1:
            return filename, ""
        return filename[:dot_index], filename[dot_index:]

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        sanitized = re.sub(r'[<>:"/\\\\|?*]', "_", name).strip(". ")
        return sanitized or "asset.bin"

    @staticmethod
    def _decode_base64(content: str) -> bytes:
        import base64

        return base64.b64decode(content.encode("utf-8"))

    @staticmethod
    def _iter_children(block: dict[str, Any]) -> list[dict[str, Any]]:
        synced_children = block.get("synced_children")
        if isinstance(synced_children, list) and synced_children:
            return synced_children
        children = block.get("children")
        if isinstance(children, list):
            return children
        return []
