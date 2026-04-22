# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：models.py
# @Date   ：2025/01/09 18:30
# @Author ：leemysw
# 2025/01/09 18:30   Create
# =====================================================
"""
[INPUT]: 依赖 pydantic 的数据验证框架
[OUTPUT]: 对外提供飞书 Block 类型枚举
[POS]: schema 模块的核心定义，被 parsers 依赖
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from enum import Enum, IntEnum


# ==============================================================================
# 枚举类型
# ==============================================================================
class TableMode(Enum):
    """表格输出模式"""
    MARKDOWN = "md"
    HTML = "html"


class SheetValueMode(Enum):
    """电子表格单元格值导出模式"""
    DISPLAY = "display"
    FORMULA = "formula"


class BlockType(IntEnum):
    """飞书文档 Block 类型枚举"""
    PAGE = 1  # 页面 Block
    TEXT = 2  # 文本 Block
    HEADING1 = 3  # 标题 1 Block
    HEADING2 = 4  # 标题 2 Block
    HEADING3 = 5  # 标题 3 Block
    HEADING4 = 6  # 标题 4 Block
    HEADING5 = 7  # 标题 5 Block
    HEADING6 = 8  # 标题 6 Block
    HEADING7 = 9  # 标题 7 Block
    HEADING8 = 10  # 标题 8 Block
    HEADING9 = 11  # 标题 9 Block
    BULLET = 12  # 无序列表 Block
    ORDERED = 13  # 有序列表 Block
    CODE = 14  # 代码块 Block
    QUOTE = 15  # 引用 Block
    TODO = 17  # 待办事项 Block
    BITABLE = 18  # 多维表格 Block
    CALLOUT = 19  # 高亮块 Block
    CHAT_CARD = 20  # 会话卡片 Block
    DIAGRAM = 21  # 流程图 & UML Block
    DIVIDER = 22  # 分割线 Block
    FILE = 23  # 文件 Block
    GRID = 24  # 分栏 Block
    GRID_COLUMN = 25  # 分栏列 Block
    IFRAME = 26  # 内嵌 Block
    IMAGE = 27  # 图片 Block
    ISV = 28  # 开放平台小组件 Block
    MINDNOTE = 29  # 思维笔记 Block
    SHEET = 30  # 电子表格 Block
    TABLE = 31  # 表格 Block
    TABLE_CELL = 32  # 表格单元格 Block
    VIEW = 33  # 视图 Block
    QUOTE_CONTAINER = 34  # 引用容器 Block
    TASK = 35  # 任务 Block
    OKR = 36  # OKR Block
    OKR_OBJECTIVE = 37  # OKR Objective Block
    OKR_KEY_RESULT = 38  # OKR Key Result Block
    OKR_PROGRESS = 39  # OKR Progress Block
    ADD_ONS = 40  # 新版文档小组件 Block
    JIRA_ISSUE = 41  # Jira 问题 Block
    WIKI_CATALOG = 42  # Wiki 子页面列表 Block（旧版）
    BOARD = 43  # 画板 Block
    AGENDA = 44  # 议程 Block
    AGENDA_ITEM = 45  # 议程项 Block
    AGENDA_ITEM_TITLE = 46  # 议程项标题 Block
    AGENDA_ITEM_CONTENT = 47  # 议程项内容 Block
    LINK_PREVIEW = 48  # 链接预览 Block
    SOURCE_SYNCED = 49  # 源同步块
    REFERENCE_SYNCED = 50  # 引用同步块
    SUB_PAGE_LIST = 51  # Wiki 子页面列表(新版)
    AI_TEMPLATE = 52  # AI 模板
    REFERENCE_BLOCK = 53  # 引用 Block
