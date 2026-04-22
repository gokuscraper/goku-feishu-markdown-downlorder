# feishu-docx

L1 | 飞书云文档导出 Markdown 工具

Python 3.11+ | lark-oapi + pydantic + typer + textual

<directory>
feishu_docx/
├── auth/       - OAuth 2.0 认证模块，自动获取 user_access_token
├── core/       - 核心解析逻辑，飞书 API 封装及文档解析器
├── schema/     - Pydantic 数据模型，Block 类型定义
├── cli/        - Typer 命令行接口
├── tui/        - Textual TUI 界面
└── utils/      - 工具函数，配置管理、临时文件存储
</directory>

<config>
pyproject.toml - 项目配置，hatch 构建后端
LICENSE        - MIT 开源协议
README.md      - 英文文档
README_zh.md   - 中文文档
</config>

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
