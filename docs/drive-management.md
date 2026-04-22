# 云空间管理

`feishu-docx drive` 用于管理飞书云空间中的文件、公开权限和成员权限。

## 云空间类型

飞书会根据访问凭证类型区分云空间：

- `tenant_access_token`：应用云空间
- `user_access_token`：个人云空间

应用云空间中的资源通常不能直接通过飞书 UI 管理，需要通过 Drive/File API 管理。

## 常用命令

### 列出文件

```bash
# 列出应用云空间中的 docx
feishu-docx drive ls --auth-mode tenant --type docx

# 列出个人云空间中的 docx
feishu-docx drive ls --auth-mode oauth --type docx

# 列出某个文件夹中的所有文件
feishu-docx drive ls --folder "https://xxx.feishu.cn/drive/folder/fldcnXXXXXX"
```

### 删除单个文件

```bash
feishu-docx drive rm "https://xxx.feishu.cn/docx/ABC123"
feishu-docx drive rm ABC123 --type docx
```

### 查看和修改公开权限

```bash
# 查看公开权限
feishu-docx drive perm-show "https://xxx.feishu.cn/docx/ABC123"

# 修改公开权限
feishu-docx drive perm-set "https://xxx.feishu.cn/docx/ABC123" \
  --share-entity anyone_can_view \
  --link-share-entity anyone_readable
```

### 管理权限成员

```bash
# 查看权限成员
feishu-docx drive perm-members "https://xxx.feishu.cn/docx/ABC123"

# 新增权限成员
feishu-docx drive perm-add "https://xxx.feishu.cn/docx/ABC123" \
  --member-id ou_xxx \
  --member-type open_id \
  --perm edit

# 更新权限成员
feishu-docx drive perm-update "https://xxx.feishu.cn/docx/ABC123" \
  --member-id ou_xxx \
  --member-type open_id \
  --perm full_access

# 删除权限成员
feishu-docx drive perm-rm "https://xxx.feishu.cn/docx/ABC123" \
  --member-id ou_xxx \
  --member-type open_id
```

### 批量清空

```bash
# 清空根目录下所有 docx
feishu-docx drive clear --type docx

# 清空指定文件夹
feishu-docx drive clear --folder "https://xxx.feishu.cn/drive/folder/fldcnXXXXXX"
```

`drive clear` 是高风险操作，默认会执行两次确认：

1. 展示待删除范围和样本
2. `yes/no` 确认
3. 输入 `CLEAR` 再次确认

`--force` 只会跳过输入 `CLEAR`，仍然保留第一次确认。

## 参数说明

- `--auth-mode tenant`：管理应用云空间
- `--auth-mode oauth`：管理个人云空间
- `--type`：限制资源类型，如 `docx`、`sheet`、`bitable`、`wiki`、`folder`
- `--folder`：指定文件夹 URL 或 token
- `-t/--token`：直接使用现成 access token

## 建议

- 日常列举和权限检查优先使用 `drive ls`、`perm-show`、`perm-members`
- 批量删除前先使用 `drive ls` 确认过滤条件
- 管理应用自动创建的文档时，优先使用 `--auth-mode tenant`
