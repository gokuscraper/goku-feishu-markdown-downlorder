# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：wiki.py
# @Date   ：2026/01/29 15:10
# @Author ：leemysw
# 2026/02/01 18:30   Refactor - 组合模式重构
# =====================================================
"""
[INPUT]: 依赖 base.py, lark_oapi
[OUTPUT]: 对外提供 WikiAPI
[POS]: SDK 知识库相关 API
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from lark_oapi.api.wiki.v2 import *

from feishu_docx.utils.console import get_console
from .base import SubModule

console = get_console()


class WikiAPI(SubModule):
    """Wiki 知识库 API"""

    def get_node_metadata(self, node_token: str, access_token: str) -> Optional[Node]:
        """获取知识库节点元数据"""
        request = (
            GetNodeSpaceRequest.builder()
            .token(node_token)
            .obj_type("wiki")
            .build()
        )
        option = self._build_option(access_token)
        response: GetNodeSpaceResponse = self.client.wiki.v2.space.get_node(request, option)

        if not response.success():
            self._log_error("wiki.v2.space.get_node", response)
            raise RuntimeError("获取知识库节点失败")

        return response.data.node

    def get_space_nodes(
            self,
            space_id: str,
            access_token: str,
            parent_node_token: Optional[str] = None,
            page_size: int = 50,
            page_token: Optional[str] = None,
    ) -> Optional[ListSpaceNodeResponseBody]:
        """获取知识空间子节点列表"""

        request: ListSpaceNodeRequest = ListSpaceNodeRequest.builder() \
            .space_id(space_id) \
            .build()

        request.add_query("page_size", str(page_size))
        if page_token:
            request.add_query("page_token", page_token)
        if parent_node_token:
            request.add_query("parent_node_token", parent_node_token)

        option = self._build_option(access_token)
        response: ListSpaceNodeResponse = self.client.wiki.v2.space_node.list(request, option)

        if not response.success():
            self._log_error("wiki.v2.spaces.nodes.list", response)
            raise RuntimeError("获取知识空间子节点列表失败")

        return response.data

    def get_all_space_nodes(
            self,
            space_id: str,
            access_token: str,
            parent_node_token: Optional[str] = None,
    ) -> List[Node]:
        """获取知识空间下的所有子节点"""
        all_nodes = []
        page_token = None
        has_more = True

        while has_more:
            result = self.get_space_nodes(
                space_id=space_id,
                access_token=access_token,
                parent_node_token=parent_node_token,
                page_token=page_token,
            )
            if not result:
                break

            all_nodes.extend(result.items or [])
            has_more = result.has_more
            page_token = result.page_token

        return all_nodes

    def get_node_by_token(
            self,
            token: str,
            access_token: str,
            obj_type: str = "wiki",
    ) -> Optional[Node]:
        """获取知识空间节点信息"""

        # 构造请求对象
        request: GetNodeSpaceRequest = GetNodeSpaceRequest.builder() \
            .token(token) \
            .obj_type(obj_type) \
            .build()

        # 发起请求
        option = self._build_option(access_token)
        response: GetNodeSpaceResponse = self.client.wiki.v2.space.get_node(request, option)

        if not response.success():
            self._log_error("wiki.v2.spaces.get_node", response)
            raise RuntimeError("获取知识空间节点信息失败")

        return response.data.node

    def get_space_info(
            self,
            space_id: str,
            access_token: str,
    ) -> Optional[Space]:
        """
        获取知识空间信息

        Args:
            space_id: 知识空间 ID
            access_token: 访问凭证

        Returns:
            dict: 包含 name, description 等字段
        """

        request: GetSpaceRequest = GetSpaceRequest.builder() \
            .space_id(space_id) \
            .build()

        option = self._build_option(access_token)
        response: GetSpaceResponse = self.client.wiki.v2.space.get(request, option)

        if not response.success():
            self._log_error("wiki.v2.spaces.get", response)
            raise RuntimeError("获取知识空间信息失败")

        return response.data.space
