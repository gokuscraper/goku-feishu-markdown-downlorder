# 飞书资源模型

飞书云空间和知识库采用两套独立的资源管理体系。

## 资源架构图

![飞书资源架构](./feishu-resources.png)

## 资源定义

| 资源 | 标识 | 说明 |
|------|------|------|
| 云空间 | `root_token` | 管理所有云文档资源的容器（个人空间） |
| 文件夹 | `folder_token` | 管理文件和其它文件夹的容器 |
| 文件 | `file_token` | 各种类型文件的统称 |
| 文档 | `doc_token` | 飞书在线文档 |
| 电子表格 | `spreadsheet_token` | 飞书电子表格 |
| 多维表格 | `app_token` | 飞书多维表格 |
| 知识库 | `space_id` | 以树状目录管理文件的容器 |
| 节点 | `node_token` | 知识库中云文档资源的挂载点 |
| 评论 | `comment_id` | 飞书在线文档中的评论 |

## 两条路径

### 云空间路径

```
云空间 (root_token)
└── 文件夹 (folder_token)
    ├── 文档 (doc_token)
    ├── 电子表格 (spreadsheet_token)
    └── 多维表格 (app_token)
```

### 知识库路径

```
知识库 (space_id)
└── 节点 (node_token)
    ├── obj_type: docx → 使用 obj_token 导出
    ├── obj_type: sheet → 使用 obj_token 导出
    └── 子节点 (node_token)
```

## 关键理解

- **`node_token` 是挂载点**：一个 wiki 节点对应一个 `obj_token`（实际文档）
- **`obj_type` 决定处理方式**：`doc`、`docx`、`sheet`、`bitable` 等
- **URL 构建规则**：`https://xxx.feishu.cn/{obj_type}/{obj_token}`

## 本项目的处理逻辑

### 单文档导出 (`export`)

1. 解析 URL 获取 `doc_type` 和 `doc_id`
2. 如果是 wiki URL，先通过 `node_token` 获取实际的 `obj_token`
3. 根据 `obj_type` 调用对应的解析器

### 知识空间批量导出 (`export_wiki_space`)

1. 通过 `space_id` 获取空间名称
2. 遍历所有 `node_token`
3. 根据 `has_child` 决定创建目录还是导出文档
4. 递归处理子节点

## 参考链接

- [飞书开放平台 - 云文档概述](https://open.feishu.cn/document/ukTMukTMukTM/uczNzUjL3czM14yN3MTN)
- [飞书开放平台 - 知识库概述](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN)
