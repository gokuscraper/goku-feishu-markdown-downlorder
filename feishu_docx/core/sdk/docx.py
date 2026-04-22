# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：docx.py
# @Date   ：2026/03/11 11:20
# @Author ：leemysw
# 2026/02/01 18:35   Refactor - 组合模式重构
# 2026/03/11 11:20   Normalize create block payload with SDK Block
# =====================================================
"""
[INPUT]: 依赖 base.py, lark_oapi
[OUTPUT]: 对外提供 DocxAPI
[POS]: SDK 云文档 CRUD API
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

import copy
import json
from typing import List, Optional

from lark_oapi.api.docx.v1 import Block, ListDocumentBlockRequest, ListDocumentBlockResponse

from feishu_docx.utils.console import get_console
from .base import SubModule

console = get_console()


class DocxAPI(SubModule):
    """云文档 API"""

    @staticmethod
    def _normalize_block_for_create(block: dict) -> Block:
        """将 dict 形式的块清洗为创建接口可接受的 SDK Block 对象。"""
        block_data = copy.deepcopy(block)
        for key in ["block_id", "parent_id", "children", "comment_ids"]:
            block_data.pop(key, None)
        if isinstance(block_data.get("table"), dict):
            block_data["table"].pop("cells", None)
        return Block(block_data)

    def _normalize_create_children(self, children: List[dict]) -> List[Block]:
        """统一转换创建请求中的 children。"""
        normalized_children: List[Block] = []
        for child in children:
            if isinstance(child, Block):
                normalized_children.append(child)
            else:
                normalized_children.append(self._normalize_block_for_create(child))
        return normalized_children

    def get_document_info(self, document_id: str, access_token: str) -> dict:
        """获取云文档基本信息"""
        from lark_oapi.api.docx.v1 import GetDocumentRequest, GetDocumentResponse

        request = GetDocumentRequest.builder().document_id(document_id).build()
        option = self._build_option(access_token)
        response: GetDocumentResponse = self.client.docx.v1.document.get(request, option)

        if not response.success():
            self._log_error("docx.v1.document.get", response)
            return {"document_id": document_id, "title": document_id}

        doc = response.data.document
        return {
            "document_id": doc.document_id,
            "revision_id": doc.revision_id,
            "title": doc.title or document_id,
        }

    def get_block_list(self, document_id: str, access_token: str) -> List[Block]:
        """获取文档所有 Block"""
        has_more = True
        page_token = None
        blocks = []

        while has_more:
            request = (
                ListDocumentBlockRequest.builder()
                .document_id(document_id)
                .page_size(500)
                .document_revision_id(-1)
                .build()
            )
            if page_token:
                request.add_query("page_token", page_token)

            option = self._build_option(access_token)
            response: ListDocumentBlockResponse = self.client.docx.v1.document_block.list(request, option)

            if not response.success():
                self._log_error("docx.v1.document_block.list", response)
                raise RuntimeError("获取文档 Block 列表失败")

            has_more = response.data.has_more
            page_token = response.data.page_token
            blocks.extend(response.data.items)

        return blocks

    def get_block_children(self, document_id: str, block_id: str, access_token: str) -> List[Block]:
        """获取指定 Block 的子 Block"""
        from lark_oapi.api.docx.v1 import (
            GetDocumentBlockChildrenRequest,
            GetDocumentBlockChildrenResponse,
        )

        has_more = True
        page_token = None
        blocks: List[Block] = []

        while has_more:
            request = (
                GetDocumentBlockChildrenRequest.builder()
                .document_id(document_id)
                .block_id(block_id)
                .document_revision_id(-1)
                .page_size(500)
                .with_descendants(False)
                .build()
            )
            if page_token:
                request.add_query("page_token", page_token)

            option = self._build_option(access_token)
            response: GetDocumentBlockChildrenResponse = (
                self.client.docx.v1.document_block_children.get(request, option)
            )

            if not response.success():
                self._log_error("docx.v1.document_block_children.get", response)
                raise RuntimeError("获取 Block 子列表失败")

            has_more = response.data.has_more
            page_token = response.data.page_token
            blocks.extend(response.data.items)

        return blocks

    def create_document(self, title: str, access_token: str, folder_token: Optional[str] = None) -> dict:
        """创建空白文档"""
        from lark_oapi.api.docx.v1 import (
            CreateDocumentRequest,
            CreateDocumentRequestBody,
            CreateDocumentResponse,
        )

        body = CreateDocumentRequestBody.builder().title(title)
        if folder_token:
            body = body.folder_token(folder_token)

        request = CreateDocumentRequest.builder().request_body(body.build()).build()
        option = self._build_option(access_token)
        response: CreateDocumentResponse = self.client.docx.v1.document.create(request, option)

        if not response.success():
            self._log_error("docx.v1.document.create", response)
            raise RuntimeError(f"创建文档失败: {response.msg}")

        doc = response.data.document
        return {
            "document_id": doc.document_id,
            "revision_id": doc.revision_id,
            "title": doc.title,
        }

    def create_blocks(
            self,
            document_id: str,
            block_id: str,
            children: List[dict],
            access_token: str,
            index: int = -1,
    ) -> List[dict]:
        """在指定 Block 下创建子 Block"""
        from lark_oapi.api.docx.v1 import (
            CreateDocumentBlockChildrenRequest,
            CreateDocumentBlockChildrenRequestBody,
            CreateDocumentBlockChildrenResponse,
        )
        all_created_children = []
        chunk_size = 50
        current_index = index
        normalized_children = self._normalize_create_children(children)

        for i in range(0, len(normalized_children), chunk_size):
            chunk = normalized_children[i: i + chunk_size]
            body_builder = CreateDocumentBlockChildrenRequestBody.builder().children(chunk)
            if current_index >= 0:
                body_builder = body_builder.index(current_index)

            request = (
                CreateDocumentBlockChildrenRequest.builder()
                .document_id(document_id)
                .block_id(block_id)
                .document_revision_id(-1)
                .request_body(body_builder.build())
                .build()
            )
            option = self._build_option(access_token)

            response: CreateDocumentBlockChildrenResponse = (
                self.client.docx.v1.document_block_children.create(request, option)
            )

            if not response.success():
                self._log_error("docx.v1.document_block_children.create", response)
                raise RuntimeError(f"创建 Block 失败: {response.msg}")

            try:
                data = json.loads(response.raw.content)
                created = data.get("data", {}).get("children", [])
                all_created_children.extend(created)
            except json.JSONDecodeError:
                pass

            if current_index >= 0:
                current_index += len(chunk)

        return all_created_children

    def update_block(self, document_id: str, block_id: str, update_body: dict, access_token: str) -> dict:
        """更新单个 Block 内容"""
        from lark_oapi.api.docx.v1 import (
            PatchDocumentBlockRequest,
            PatchDocumentBlockResponse,
        )

        request = (
            PatchDocumentBlockRequest.builder()
            .document_id(document_id)
            .block_id(block_id)
            .document_revision_id(-1)
            .request_body(update_body)
            .build()
        )
        option = self._build_option(access_token)
        response: PatchDocumentBlockResponse = self.client.docx.v1.document_block.patch(request, option)

        if not response.success():
            self._log_error("docx.v1.document_block.patch", response)
            raise RuntimeError(f"更新 Block 失败: {response.msg}")

        data = json.loads(response.raw.content)
        return data.get("data", {}).get("block", {})

    def replace_image(self, document_id: str, block_id: str, file_token: str, access_token: str) -> dict:
        """替换图片内容"""
        from lark_oapi.api.docx.v1 import (
            PatchDocumentBlockRequest,
            PatchDocumentBlockResponse,
            ReplaceImageRequest,
            UpdateBlockRequest,
        )

        request = (
            PatchDocumentBlockRequest.builder()
            .document_id(document_id)
            .block_id(block_id)
            .document_revision_id(-1)
            .request_body(
                UpdateBlockRequest.builder()
                .replace_image(ReplaceImageRequest.builder().token(file_token).build())
                .build()
            )
            .build()
        )
        option = self._build_option(access_token)
        response: PatchDocumentBlockResponse = self.client.docx.v1.document_block.patch(request, option)

        if not response.success():
            self._log_error("docx.v1.document_block.patch.replace_image", response)
            raise RuntimeError(f"替换图片失败: {response.msg}")

        data = json.loads(response.raw.content)
        return data.get("data", {}).get("block", {})

    def batch_update_blocks(self, document_id: str, requests: List[dict], access_token: str) -> List[dict]:
        """批量更新多个 Block"""
        from lark_oapi.api.docx.v1 import (
            BatchUpdateDocumentBlockRequest,
            BatchUpdateDocumentBlockRequestBody,
            BatchUpdateDocumentBlockResponse,
        )

        request = (
            BatchUpdateDocumentBlockRequest.builder()
            .document_id(document_id)
            .document_revision_id(-1)
            .request_body(BatchUpdateDocumentBlockRequestBody.builder().requests(requests).build())
            .build()
        )
        option = self._build_option(access_token)
        response: BatchUpdateDocumentBlockResponse = (
            self.client.docx.v1.document_block.batch_update(request, option)
        )

        if not response.success():
            self._log_error("docx.v1.document_block.batch_update", response)
            raise RuntimeError(f"批量更新 Block 失败: {response.msg}")

        data = json.loads(response.raw.content)
        return data.get("data", {}).get("blocks", [])

    def delete_block(self, document_id: str, block_id: str, access_token: str) -> None:
        """删除指定的 Block"""
        requests = [{"delete_block": {"block_id": block_id}}]
        self.batch_update_blocks(document_id, requests, access_token)

    def convert_markdown(self, markdown_content: str, access_token: str) -> List[dict]:
        """将 Markdown 转换为飞书 Block 结构"""
        from lark_oapi.api.docx.v1 import (
            ConvertDocumentRequest,
            ConvertDocumentRequestBody,
            ConvertDocumentResponse,
        )

        request = (
            ConvertDocumentRequest.builder()
            .request_body(
                ConvertDocumentRequestBody.builder()
                .content_type("markdown")
                .content(markdown_content)
                .build()
            )
            .build()
        )
        option = self._build_option(access_token)
        response: ConvertDocumentResponse = self.client.docx.v1.document.convert(request, option)

        if not response.success():
            self._log_error("docx.v1.document.convert", response)
            raise RuntimeError(f"Markdown 转换失败: {response.msg}")

        data = json.loads(response.raw.content)
        return data.get("data", {}).get("blocks", [])

    def delete_blocks(
            self, document_id: str, block_id: str, start_index: int, end_index: int, access_token: str
    ) -> bool:
        """删除指定范围的子 Block"""
        from lark_oapi.api.docx.v1 import (
            BatchDeleteDocumentBlockChildrenRequest,
            BatchDeleteDocumentBlockChildrenRequestBody,
            BatchDeleteDocumentBlockChildrenResponse,
        )

        request = (
            BatchDeleteDocumentBlockChildrenRequest.builder()
            .document_id(document_id)
            .block_id(block_id)
            .document_revision_id(-1)
            .request_body(
                BatchDeleteDocumentBlockChildrenRequestBody.builder()
                .start_index(start_index)
                .end_index(end_index)
                .build()
            )
            .build()
        )
        option = self._build_option(access_token)
        response: BatchDeleteDocumentBlockChildrenResponse = (
            self.client.docx.v1.document_block_children.batch_delete(request, option)
        )

        if not response.success():
            self._log_error("docx.v1.document_block_children.batch_delete", response)
            return False

        return True

    def clear_document(
            self,
            document_id: str,
            access_token: str,
            batch_size: int = 200,
            max_rounds: int = 20,
    ) -> int:
        """清空文档根节点下的所有子 Block"""
        deleted_total = 0
        rounds = 0

        while rounds < max_rounds:
            rounds += 1
            blocks = self.get_block_list(document_id, access_token)
            if not blocks:
                break

            block_map = {b.block_id: b for b in blocks if getattr(b, "block_id", None)}
            root_block = block_map.get(document_id)
            if not root_block:
                root_block = next((b for b in blocks if getattr(b, "block_type", None) == 1), None)
            if not root_block:
                break

            root_id = root_block.block_id or document_id
            children = root_block.children or []
            if not children:
                break

            delete_count = min(len(children), batch_size)
            ok = self.delete_blocks(
                document_id=document_id,
                block_id=root_id,
                start_index=0,
                end_index=delete_count,
                access_token=access_token,
            )
            if not ok:
                break

            deleted_total += delete_count

        return deleted_total
