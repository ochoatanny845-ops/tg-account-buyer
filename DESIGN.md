# 📋 改进 Session 上传流程 - 设计文档

## 问题1：识别账号数量 + 收集 2FA 密码

### 方案A：要求提供 JSON 配置文件
用户上传 ZIP 时必须包含 `config.json`：
```json
{
  "sessions": [
    {
      "file": "account1.session",
      "phone": "+1234567890",
      "password": "2fa_password_here"
    }
  ]
}
```

### 方案B：上传后逐个询问密码（推荐）
1. 解压 ZIP，统计 `.session` 文件数量
2. 提示：发现 X 个账号，请逐个提供 2FA 密码
3. 用 ConversationHandler 逐个收集密码
4. 验证每个 Session + 密码

**采用方案B**：用户体验更好，不需要手动编辑 JSON

---

## 问题2：转发源文件（ZIP）给管理员

修改 `notify_admin_new_session`：
- 不发送 `.session` 文件
- 发送用户上传的原始 ZIP/RAR 文件
- 在 `context.user_data` 中保存 `archive_path`

---

## 实现步骤

1. 修改 `receive_session_file`：
   - 统计 `.session` 文件数量
   - 保存 `archive_path` 到 `context.user_data`
   - 如果只有 1 个，直接处理
   - 如果多个，进入密码收集流程

2. 新增状态 `WAITING_SESSION_PASSWORDS`

3. 修改 `process_session`：
   - 接受 `archive_path` 参数
   - 传递给 `notify_admin_new_session`

4. 修改 `notify_admin_new_session`：
   - 发送 `archive_path` 文件而不是 `.session`

---

开始实现...
