# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：drive.py
# @Date   ：2026/03/11 11:45
# @Author ：leemysw
# 2026/03/11 11:45   Create
# =====================================================
"""
[INPUT]: 依赖 base.py, lark_oapi
[OUTPUT]: 对外提供 DriveAPI
[POS]: SDK 云空间文件管理 API
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from typing import List, Optional

from lark_oapi.api.drive.v1 import (
    BaseMember,
    CreatePermissionMemberRequest,
    DeleteFileRequest,
    DeletePermissionMemberRequest,
    DeletePermissionMemberRequestBody,
    GetPermissionPublicRequest,
    ListFileRequest,
    ListPermissionMemberRequest,
    PatchPermissionPublicRequest,
    PermissionPublic,
    PermissionPublicRequest,
    UpdatePermissionMemberRequest,
)

from .base import SubModule


class DriveAPI(SubModule):
    """云空间文件管理 API。"""

    def list_files(
            self,
            access_token: str,
            folder_token: Optional[str] = None,
            page_size: int = 50,
            order_by: Optional[str] = None,
            direction: Optional[str] = None,
            option: Optional[str] = None,
    ) -> list:
        """列出云空间文件。"""
        files = []
        page_token: Optional[str] = None

        while True:
            builder = ListFileRequest.builder().page_size(page_size)
            if folder_token:
                builder = builder.folder_token(folder_token)
            if page_token:
                builder = builder.page_token(page_token)
            if order_by:
                builder = builder.order_by(order_by)
            if direction:
                builder = builder.direction(direction)
            if option:
                builder = builder.option(option)

            request = builder.build()
            option_obj = self._build_option(access_token)
            response = self.client.drive.v1.file.list(request, option_obj)

            if not response.success():
                self._log_error("drive.v1.file.list", response)
                raise RuntimeError("获取云空间文件列表失败")

            data = response.data
            if data and data.files:
                files.extend(data.files)

            if not data or not data.has_more:
                break
            page_token = data.next_page_token

        return files

    def delete_file(
            self,
            file_token: str,
            file_type: str,
            access_token: str,
    ) -> None:
        """删除云空间文件。"""
        request = (
            DeleteFileRequest.builder()
            .file_token(file_token)
            .type(file_type)
            .build()
        )
        option = self._build_option(access_token)
        response = self.client.drive.v1.file.delete(request, option)

        if not response.success():
            self._log_error("drive.v1.file.delete", response)
            raise RuntimeError(f"删除文件失败: {response.msg}")

    def get_public_permission(
            self,
            token: str,
            file_type: str,
            access_token: str,
    ) -> PermissionPublic:
        """获取文件公开权限。"""
        request = (
            GetPermissionPublicRequest.builder()
            .token(token)
            .type(file_type)
            .build()
        )
        option = self._build_option(access_token)
        response = self.client.drive.v1.permission_public.get(request, option)

        if not response.success():
            self._log_error("drive.v1.permission_public.get", response)
            raise RuntimeError("获取公开权限失败")

        return response.data.permission_public

    def update_public_permission(
            self,
            token: str,
            file_type: str,
            access_token: str,
            external_access: Optional[bool] = None,
            security_entity: Optional[str] = None,
            comment_entity: Optional[str] = None,
            share_entity: Optional[str] = None,
            link_share_entity: Optional[str] = None,
            invite_external: Optional[bool] = None,
    ) -> PermissionPublic:
        """更新文件公开权限。"""
        body_builder = PermissionPublicRequest.builder()

        if external_access is not None:
            body_builder = body_builder.external_access(external_access)
        if security_entity is not None:
            body_builder = body_builder.security_entity(security_entity)
        if comment_entity is not None:
            body_builder = body_builder.comment_entity(comment_entity)
        if share_entity is not None:
            body_builder = body_builder.share_entity(share_entity)
        if link_share_entity is not None:
            body_builder = body_builder.link_share_entity(link_share_entity)
        if invite_external is not None:
            body_builder = body_builder.invite_external(invite_external)

        request = (
            PatchPermissionPublicRequest.builder()
            .token(token)
            .type(file_type)
            .request_body(body_builder.build())
            .build()
        )
        option = self._build_option(access_token)
        response = self.client.drive.v1.permission_public.patch(request, option)

        if not response.success():
            self._log_error("drive.v1.permission_public.patch", response)
            raise RuntimeError(f"更新公开权限失败: {response.msg}")

        return response.data.permission_public

    def list_permission_members(
            self,
            token: str,
            file_type: str,
            access_token: str,
            fields: Optional[str] = None,
            perm_type: Optional[str] = None,
    ) -> List:
        """列出文件权限成员。"""
        builder = (
            ListPermissionMemberRequest.builder()
            .token(token)
            .type(file_type)
        )
        if fields:
            builder = builder.fields(fields)
        if perm_type:
            builder = builder.perm_type(perm_type)

        request = builder.build()
        option = self._build_option(access_token)
        response = self.client.drive.v1.permission_member.list(request, option)

        if not response.success():
            self._log_error("drive.v1.permission_member.list", response)
            raise RuntimeError("获取权限成员失败")

        return response.data.items or []

    def create_permission_member(
            self,
            token: str,
            file_type: str,
            access_token: str,
            member_id: str,
            member_type: str,
            perm: str,
            perm_type: str = "container",
            need_notification: bool = False,
    ):
        """新增文件权限成员。"""
        body = (
            BaseMember.builder()
            .member_id(member_id)
            .member_type(member_type)
            .perm(perm)
            .perm_type(perm_type)
            .type(file_type)
            .build()
        )
        request = (
            CreatePermissionMemberRequest.builder()
            .token(token)
            .type(file_type)
            .need_notification(need_notification)
            .request_body(body)
            .build()
        )
        option = self._build_option(access_token)
        response = self.client.drive.v1.permission_member.create(request, option)

        if not response.success():
            self._log_error("drive.v1.permission_member.create", response)
            raise RuntimeError(f"新增权限成员失败: {response.msg}")

        return response.data.member

    def update_permission_member(
            self,
            token: str,
            file_type: str,
            access_token: str,
            member_id: str,
            member_type: str,
            perm: str,
            perm_type: str = "container",
            need_notification: bool = False,
    ):
        """更新文件权限成员。"""
        body = (
            BaseMember.builder()
            .member_id(member_id)
            .member_type(member_type)
            .perm(perm)
            .perm_type(perm_type)
            .type(file_type)
            .build()
        )
        request = (
            UpdatePermissionMemberRequest.builder()
            .token(token)
            .type(file_type)
            .member_id(member_id)
            .need_notification(need_notification)
            .request_body(body)
            .build()
        )
        option = self._build_option(access_token)
        response = self.client.drive.v1.permission_member.update(request, option)

        if not response.success():
            self._log_error("drive.v1.permission_member.update", response)
            raise RuntimeError(f"更新权限成员失败: {response.msg}")

        return response.data.member

    def delete_permission_member(
            self,
            token: str,
            file_type: str,
            access_token: str,
            member_id: str,
            member_type: str,
            perm_type: str = "container",
    ) -> None:
        """删除文件权限成员。"""
        body = (
            DeletePermissionMemberRequestBody.builder()
            .type(file_type)
            .perm_type(perm_type)
            .build()
        )
        request = (
            DeletePermissionMemberRequest.builder()
            .token(token)
            .type(file_type)
            .member_id(member_id)
            .member_type(member_type)
            .request_body(body)
            .build()
        )
        option = self._build_option(access_token)
        response = self.client.drive.v1.permission_member.delete(request, option)

        if not response.success():
            self._log_error("drive.v1.permission_member.delete", response)
            raise RuntimeError(f"删除权限成员失败: {response.msg}")
