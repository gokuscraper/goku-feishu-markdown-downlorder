# SDK Module

L2 | 父级: ../CLAUDE.md

飞书 API 封装，使用组合模式组织各功能模块。

## 成员清单

| 文件 | 职责 |
|------|------|
| `__init__.py` | 入口，FeishuSDK 组合各子模块 + 向后兼容方法 |
| `base.py` | SDKCore (核心) + SubModule (子模块基类) |
| `contact.py` | ContactAPI - 联系人/用户 |
| `wiki.py` | WikiAPI - 知识库 |
| `docx.py` | DocxAPI - 云文档 CRUD |
| `media.py` | MediaAPI - 图片/附件/画板 |
| `sheet.py` | SheetAPI - 电子表格 |
| `bitable.py` | BitableAPI - 多维表格 |
| `apaas.py` | APaaSAPI - APaaS 数据平台 |

## 架构

```
FeishuSDK (组合)
├── _core: SDKCore     # 共享资源 (client, temp_dir, token_type)
├── contact: ContactAPI    # 通过 property 延迟初始化
├── wiki: WikiAPI
├── docx: DocxAPI
├── media: MediaAPI
├── sheet: SheetAPI
├── bitable: BitableAPI
└── apaas: APaaSAPI
```

## Token 类型

- `tenant`: tenant_access_token（默认，自建应用直接获取）
- `user`: user_access_token（需用户 OAuth 授权）

## Usage

```python
sdk = FeishuSDK()

# 组合模式访问（推荐）
sdk.wiki.get_node_metadata(node_token, token)
sdk.docx.create_document(title, token)
sdk.media.get_image(file_token, token)
sdk.sheet.get_spreadsheet_info(token, access_token)
sdk.bitable.get_bitable_info(app_token, access_token)

# 向后兼容方法（保留）
sdk.get_user_name(user_id, token)
sdk.get_document_info(doc_id, token)
```

[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
