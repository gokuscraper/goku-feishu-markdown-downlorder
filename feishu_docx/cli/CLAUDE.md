# CLI 模块

命令行界面，基于 Typer 框架构建。

## 架构

```
cli/
├── main.py          # 入口 - 组装所有命令，创建 Typer 应用
├── common.py        # 共享工具 - get_credentials, normalize_folder_token
├── cmd_export.py    # 导出命令 - export, export-wechat, export_wiki_space
├── cmd_write.py     # 写入命令 - create, write, update
├── cmd_apaas.py     # APaaS 命令 - export_workspace_schema
├── cmd_auth.py      # 认证命令 - auth, tui
└── cmd_config.py    # 配置命令 - config set/show/clear
```

## 命令清单

| 命令 | 模块 | 说明 |
|------|------|------|
| `export` | cmd_export | 导出单个文档为 Markdown |
| `export-wechat` | cmd_export | 导出公众号文章为 Markdown |
| `export-wiki-space` | cmd_export | 批量导出知识空间 |
| `create` | cmd_write | 创建新文档 |
| `write` | cmd_write | 向文档追加内容 |
| `update` | cmd_write | 更新指定 Block |
| `export-workspace-schema` | cmd_apaas | 导出 APaaS 数据库结构 |
| `auth` | cmd_auth | OAuth 授权 |
| `tui` | cmd_auth | TUI 交互界面 |
| `config set/show/clear` | cmd_config | 配置管理 |

## 凭证优先级

`get_credentials()` 按以下顺序获取凭证：
1. 命令行参数 `--app-id`, `--app-secret`
2. 环境变量 `FEISHU_APP_ID`, `FEISHU_APP_SECRET`
3. 配置文件 `~/.config/feishu-docx/config.json`

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
