# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：contact.py
# @Date   ：2026/01/29 15:23
# @Author ：leemysw
# 2026/02/01 18:30   Refactor - 组合模式重构
# =====================================================
"""
[INPUT]: 依赖 base.py, lark_oapi
[OUTPUT]: 对外提供 ContactAPI
[POS]: SDK 联系人/用户相关 API
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from lark_oapi.api.contact.v3 import GetUserRequest, GetUserResponse
from .base import SubModule


class ContactAPI(SubModule):
    """联系人/用户 API"""

    def get_user_name(self, user_id: str, access_token: str) -> str:
        """获取用户名称"""
        request = (
            GetUserRequest.builder()
            .user_id(user_id)
            .user_id_type("open_id")
            .build()
        )
        option = self._build_option(access_token)
        response: GetUserResponse = self.client.contact.v3.user.get(request, option)

        if not response.success():
            self._log_error("contact.v3.user.get", response)
            return user_id

        return response.data.user.name
