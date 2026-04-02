#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""改进的 Session 上传处理"""

# 完整的 receive_session_file 函数（支持多账号）

async def receive_session_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """接收 Session 文件（压缩包）- 支持多账号"""
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
    
    # 查找所有 .session 文件
    session_files = []
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith('.session'):
                session_files.append(os.path.join(root, file))
    
    if not session_files:
        await update.message.reply_text(
            "❌ 未找到 .session 文件\n\n"
            "请确保压缩包内包含 Telethon Session 文件",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # 保存到会话数据
    context.user_data['session_files'] = session_files
    context.user_data['archive_path'] = archive_path
    context.user_data['session_count'] = len(session_files)
    context.user_data['current_session_index'] = 0
    context.user_data['session_passwords'] = {}
    
    # 提示用户
    await update.message.reply_text(
        f"✅ 已解压完成\n\n"
        f"📊 发现 {len(session_files)} 个账号\n\n"
        f"⚠️ 请逐个提供 2FA 密码（如果没有设置，请发送 'skip'）\n\n"
        f"正在处理第 1/{len(session_files)} 个账号..."
    )
    
    # 开始收集密码
    return await ask_next_password(update, context)


async def ask_next_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """询问下一个 Session 的密码"""
    session_files = context.user_data.get('session_files', [])
    current_index = context.user_data.get('current_session_index', 0)
    
    if current_index >= len(session_files):
        # 所有密码收集完成，开始处理
        return await process_all_sessions(update, context)
    
    session_file = session_files[current_index]
    session_name = os.path.basename(session_file)
    
    await update.message.reply_text(
        f"🔐 Session {current_index + 1}/{len(session_files)}\n\n"
        f"文件：<code>{session_name}</code>\n\n"
        f"请输入该账号的 2FA 密码：\n"
        f"（如果未设置 2FA，请发送 'skip'）",
        parse_mode='HTML'
    )
    
    return WAITING_SESSION_PASSWORDS


async def receive_session_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """接收 Session 密码"""
    password = update.message.text.strip()
    
    if password.lower() == "cancel" or password == "❌ 取消":
        await update.message.reply_text(
            "❌ 已取消操作",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    session_files = context.user_data.get('session_files', [])
    current_index = context.user_data.get('current_session_index', 0)
    
    # 保存密码（skip 表示无密码）
    if password.lower() != 'skip':
        context.user_data['session_passwords'][current_index] = password
    
    # 移动到下一个
    context.user_data['current_session_index'] = current_index + 1
    
    # 继续询问或处理
    return await ask_next_password(update, context)


async def process_all_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理所有 Session"""
    session_files = context.user_data.get('session_files', [])
    session_passwords = context.user_data.get('session_passwords', {})
    archive_path = context.user_data.get('archive_path')
    
    await update.message.reply_text(
        f"⏳ 开始验证 {len(session_files)} 个账号..."
    )
    
    valid_count = 0
    invalid_count = 0
    
    for index, session_file in enumerate(session_files):
        password = session_passwords.get(index)
        
        # 验证 Session（使用密码）
        is_valid, phone, country_code, error = await validate_session_with_password(
            session_file, password
        )
        
        if is_valid:
            # 处理有效的 Session
            await process_session(update, context, session_file, phone, archive_path)
            valid_count += 1
        else:
            logger.error(f"Session {index+1} 验证失败: {error}")
            invalid_count += 1
    
    # 汇总结果
    await update.message.reply_text(
        f"✅ 处理完成\n\n"
        f"✅ 成功：{valid_count} 个\n"
        f"❌ 失败：{invalid_count} 个\n\n"
        f"管理员正在审核中，请耐心等待...",
        reply_markup=main_menu_keyboard()
    )
    
    return ConversationHandler.END
