# TUI 模块

飞书文档导出器的终端用户界面（TUI）。

## 结构

```
tui/
├── __init__.py     - 模块入口，导出 FeishuDocxApp
├── app.py          - 主应用类，包含 UI 布局和事件处理
├── constants.py    - 常量：Logo、版本、作者信息
└── styles.py       - CSS 样式定义
```

## 文件职责

- **app.py**: 主应用逻辑，包括 compose、actions、事件处理、后台任务
- **constants.py**: ASCII Logo、版本号、作者、仓库地址
- **styles.py**: Textual CSS 样式，定义颜色、布局、进度条等

## 使用

```python
from feishu_docx.tui import FeishuDocxApp

app = FeishuDocxApp()
app.run()
```

## 快捷键

| 键 | 功能 |
|---|---|
| Enter | 导出 |
| Ctrl+S | 保存配置 |
| Ctrl+L | 清空日志 |
| Ctrl+Z | 撤回输入 |
| q | 退出 |

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
