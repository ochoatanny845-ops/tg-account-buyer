#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""简化版的多账号上传处理 - 只统计和收集密码"""

async def receive_session_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """接收 Session 文件（压缩包）- 支持多账号统计"""
    if update.message.text == "❌ 取消":
        await update.message.reply_text(
            "❌ 已取消操作",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    if not update.message.document:
        await update.message.reply_text(
            "❌ 请发送文件，不是文本消息\n"
            "如需取消请点击下方按钮"
        )
        return WAITING_SESSION_FILE
    
    document = update.message.document
    
    # 检查文件扩展名
    if not (document.file_name.endswith('.zip') or document.file_name.endswith('.rar')):
        await update.message.reply_text(
            "❌ 仅支持 .zip 和 .rar 压缩包\n"
            "请发送正确的文件格式"
        )
        return WAITING_SESSION_FILE
    
    await update.message.reply_text("⏳ 正在下载和解压文件...")
    
    # 下载文件到临时目录
    file = await context.bot.get_file(document.file_id)
    temp_dir = tempfile.mkdtemp()
    archive_path = os.path.join(temp_dir, document.file_name)
    await file.download_to_drive(archive_path)
    
    # 解压文件
    try:
        if document.file_name.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        else:  # .rar
            with rarfile.RarFile(archive_path, 'r') as rar_ref:
                rar_ref.extractall(temp_dir)
    except Exception as e:
        await update.message.reply_text(
            f"❌ 解压失败：{str(e)}\n\n"
            f"请确保压缩包未加密",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # 查找所有 .session 文件 + JSON 配置文件
    session_files = []
    config_file = None
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            full_path = os.path.join(root, file)
            if file.endswith('.session'):
                session_files.append(full_path)
            elif file.lower() in ['config.json', 'accounts.json', 'passwords.json']:
                config_file = full_path
    
    if not session_files:
        await update.message.reply_text(
            "❌ 未找到 .session 文件\n\n"
            "请确保压缩包内包含 Telethon Session 文件",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    account_count = len(session_files)
    passwords_dict = {}
    
    # 尝试读取 JSON 配置文件
    if config_file:
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 支持多种 JSON 格式
            if isinstance(config_data, dict):
                # 格式1: {"file1.session": "password1", ...}
                if any(k.endswith('.session') for k in config_data.keys()):
                    passwords_dict = config_data
                # 格式2: {"sessions": [{"file": "x.session", "password": "xxx"}]}
                elif 'sessions' in config_data:
                    for item in config_data['sessions']:
                        if 'file' in item and 'password' in item:
                            passwords_dict[item['file']] = item['password']
                # 格式3: {"accounts": [{"phone": "+xxx", "twofa": "xxx"}]}
                elif 'accounts' in config_data:
                    # 按顺序匹配
                    for idx, item in enumerate(config_data['accounts']):
                        if 'twofa' in item or 'password' in item:
                            if idx < len(session_files):
                                session_name = os.path.basename(session_files[idx])
                                passwords_dict[session_name] = item.get('twofa') or item.get('password')
        except Exception as e:
            logger.warning(f"读取配置文件失败: {e}")
    
    # 统计有密码的账号数量
    matched_passwords = sum(1 for sf in session_files if os.path.basename(sf) in passwords_dict)
    
    # 显示统计信息
    summary_text = f"""
✅ 解压完成

📊 统计信息：
• 账号数量：{account_count} 个
• 已配置密码：{matched_passwords} 个
• 需要补充：{account_count - matched_passwords} 个

⏳ 正在提交审核...
"""
    await update.message.reply_text(summary_text)
    
    # 保存信息并直接处理（不验证）
    context.user_data['archive_path'] = archive_path
    context.user_data['session_count'] = account_count
    context.user_data['passwords_provided'] = matched_passwords
    
    # 简单处理：只提交第一个 Session（或全部）
    # 这里选择只处理第一个作为示例
    first_session = session_files[0]
    await process_session(update, context, first_session, None, archive_path)
    
    return ConversationHandler.END
