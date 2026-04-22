# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：styles.py
# @Date   ：2025/01/10 16:30
# @Author ：leemysw
# 2025/01/10 16:30   Create
# =====================================================
"""
[INPUT]: 无
[OUTPUT]: 对外提供 APP_CSS 样式字符串
[POS]: tui 模块的 CSS 样式定义
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

# ==============================================================================
# TUI CSS 样式
# ==============================================================================
APP_CSS = """
Screen {
    background: #0d1117;
}

/* ===== 顶部标题区 ===== */
#header {
    height: auto;
    background: #0d1117;
    padding: 0 1;
    margin-bottom: 1;
}

#logo {
    color: #58a6ff;
    text-align: center;
    height: 4;
}

#desc-line {
    text-align: center;
    color: #8b949e;
    height: 2;
}

#info-line {
    text-align: center;
    color: #484f58;
    height: 1;
}

/* ===== 主内容 ===== */
#content {
    height: 1fr;
    padding: 0 1;
}

/* ===== 左侧配置面板 ===== */
#left-panel {
    width: 50;
    min-width: 45;
    height: 100%;
    border: round #30363d;
    padding: 1;
}

.panel-title {
    color: #58a6ff;
    text-style: bold;
}

.separator {
    color: #30363d;
}

.field-row {
    height: 1;
}

.field-label {
    width: 9;
    color: #8b949e;
}

.field-value {
    color: #c9d1d9;
}

.field-prompt {
    color: #58a6ff;
    width: 3;
}

.field-input {
    background: transparent;
    border: none;
    padding: 0;
    height: 1;
    color: #58a6ff;
}

.field-input:focus {
    border: none;
    background: #21262d;
}

.field-input > .input--placeholder {
    color: #484f58;
}

/* ===== 状态颜色 ===== */
.status-ok { color: #3fb950; }
.status-warn { color: #d29922; }
.status-error { color: #f85149; }

/* ===== 进度区域 ===== */
#progress-section {
    height: auto;
    margin-top: 1;
    border-top: solid #30363d;
    padding-top: 1;
}

#progress-text {
    color: #8b949e;
    height: 1;
}

#progress-bar {
    width: 100%;
    height: 1;
    margin-top: 1;
}

#progress-bar Bar {
    width: 1fr;
}

#progress-bar .bar--bar {
    color: #58a6ff;
    background: #21262d;
}

#progress-bar .bar--complete {
    color: #3fb950;
}

/* ===== 右侧日志面板 ===== */
#right-panel {
    width: 1fr;
    height: 100%;
    margin-left: 1;
    border: round #30363d;
    padding: 1;
}

#log-view {
    height: 1fr;
    background: transparent;
    border: none;
    scrollbar-size: 1 1;
}

/* ===== 底部 ===== */
Footer {
    background: #161b22;
}

Footer > .footer--key {
    color: #58a6ff;
    background: transparent;
}
"""
