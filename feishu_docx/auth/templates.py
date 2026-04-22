# !/usr/bin/env python
# -*- coding: utf-8 -*-
# =====================================================
# @File   ：templates.py
# @Date   ：2025/01/11 16:40
# @Author ：leemysw
# 2025/01/11 16:40   Create
# =====================================================
"""
OAuth 页面 HTML 模板

[INPUT]: None
[OUTPUT]: 对外提供 SUCCESS_HTML, ERROR_HTML 模板
[POS]: auth 模块的 UI 模板，与 oauth.py 分离关注点
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

# ==============================================================================
# 共享样式
# ==============================================================================
BASE_STYLE = """
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', sans-serif;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #0a0a0a;
    color: #fafafa;
}

.container {
    width: 100%;
    max-width: 400px;
    padding: 0 24px;
}

.card {
    background: #141414;
    border: 1px solid #262626;
    border-radius: 12px;
    padding: 40px 32px;
    text-align: center;
}

.logo {
    font-size: 20px;
    font-weight: 600;
    letter-spacing: -0.5px;
    margin-bottom: 32px;
}

.icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    margin: 0 auto 20px;
}

.icon svg {
    width: 24px;
    height: 24px;
    stroke-width: 2.5;
    fill: none;
}

h1 {
    font-size: 18px;
    font-weight: 500;
    color: #fafafa;
    margin-bottom: 8px;
}

.desc {
    font-size: 14px;
    color: #737373;
    line-height: 1.5;
    margin-bottom: 20px;
}

.divider {
    height: 1px;
    background: #262626;
    margin: 0 -32px 20px;
}

.hint {
    font-size: 13px;
    color: #525252;
}

.hint kbd, .hint code {
    display: inline-block;
    background: #1f1f1f;
    border: 1px solid #333;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 11px;
    font-family: inherit;
    color: #737373;
    margin: 0 1px;
}

.footer {
    margin-top: 24px;
    font-size: 12px;
    color: #404040;
}

.footer a {
    color: #525252;
    text-decoration: none;
}

.footer a:hover {
    color: #737373;
}
"""

# ==============================================================================
# 成功页面样式
# ==============================================================================
SUCCESS_STYLE = BASE_STYLE + """
.logo { color: #fafafa; }
.icon { background: #166534; }
.icon svg { stroke: #22c55e; }

.features {
    display: flex;
    justify-content: center;
    gap: 24px;
    margin-bottom: 24px;
}

.feature {
    font-size: 13px;
    color: #a3a3a3;
}
"""

# ==============================================================================
# 失败页面样式
# ==============================================================================
ERROR_STYLE = BASE_STYLE + """
.logo { color: #737373; }
.icon { background: #7f1d1d; }
.icon svg { stroke: #ef4444; }

.error-code {
    font-size: 12px;
    color: #525252;
    background: #1a1a1a;
    border: 1px solid #262626;
    border-radius: 6px;
    padding: 8px 12px;
    font-family: 'SF Mono', Consolas, monospace;
    margin-bottom: 24px;
}
"""

# ==============================================================================
# 成功页面 HTML
# ==============================================================================
SUCCESS_HTML = f"""
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>feishu-docx · 授权成功</title>
    <style>{SUCCESS_STYLE}</style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">feishu-docx</div>
            
            <div class="icon">
                <svg viewBox="0 0 24 24">
                    <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            
            <h1>授权成功</h1>
            <p class="desc">您的飞书账号已完成授权，现在可以导出文档了</p>
            
            <div class="divider"></div>
            
            <div class="features">
                <span class="feature">云文档</span>
                <span class="feature">电子表格</span>
                <span class="feature">多维表格</span>
            </div>
            
            <p class="hint">关闭此页面 <kbd>⌘</kbd><kbd>W</kbd></p>
        </div>
        
        <div class="footer">
            <a href="https://github.com/leemysw/feishu-docx">GitHub</a> · by leemysw
        </div>
    </div>
</body>
</html>
"""


# ==============================================================================
# 失败页面 HTML 生成器
# ==============================================================================
def get_error_html(error: str, error_desc: str) -> str:
    """生成错误页面 HTML"""
    return f"""
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>feishu-docx · 授权失败</title>
    <style>{ERROR_STYLE}</style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">feishu-docx</div>
            
            <div class="icon">
                <svg viewBox="0 0 24 24">
                    <path d="M18 6L6 18M6 6l12 12" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            
            <h1>授权失败</h1>
            <p class="desc">{error_desc}</p>
            
            <div class="error-code">{error}</div>
            
            <div class="divider"></div>
            
            <p class="hint">重新运行 <code>feishu-docx auth</code></p>
        </div>
        
        <div class="footer">
            <a href="https://github.com/leemysw/feishu-docx/issues">报告问题</a> · by leemysw
        </div>
    </div>
</body>
</html>
"""
