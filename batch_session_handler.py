#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量处理 Session 的新逻辑"""

async def receive_session_file_v2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """接收 Session 文件 - 批量处理版本"""
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
    
    # 下载和解压
    file = await context.bot.get_file(document.file_id)
    temp_dir = tempfile.mkdtemp()
    archive_path = os.path.join(temp_dir, document.file_name)
    await file.download_to_drive(archive_path)
    
    try:
        if document.file_name.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        else:
            with rarfile.RarFile(archive_path, 'r') as rar_ref:
                rar_ref.extractall(temp_dir)
    except Exception as e:
        await update.message.reply_text(
            f"❌ 解压失败：{str(e)}",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # 查找所有 Session
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
            "❌ 未找到 .session 文件",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    account_count = len(session_files)
    
    # 读取 JSON 密码配置（如果有）
    passwords_dict = {}
    if config_file:
        try:
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 支持多种格式
            if isinstance(config_data, dict):
                if any(k.endswith('.session') for k in config_data.keys()):
                    passwords_dict = config_data
                elif 'sessions' in config_data:
                    for item in config_data['sessions']:
                        if 'file' in item and 'password' in item:
                            passwords_dict[item['file']] = item['password']
                elif 'accounts' in config_data:
                    for idx, item in enumerate(config_data['accounts']):
                        if 'twofa' in item or 'password' in item:
                            if idx < len(session_files):
                                session_name = os.path.basename(session_files[idx])
                                passwords_dict[session_name] = item.get('twofa') or item.get('password')
        except Exception as e:
            logger.warning(f"读取配置失败: {e}")
    
    matched_passwords = sum(1 for sf in session_files if os.path.basename(sf) in passwords_dict)
    
    # 显示统计
    await update.message.reply_text(f"""
✅ 解压完成

📊 统计信息：
• 账号数量：{account_count} 个
• 已配置密码：{matched_passwords} 个

⏳ 正在验证并提交...
""")
    
    # 验证所有 Session 并收集信息
    user_id = update.effective_user.id
    valid_sessions = []
    
    for session_file in session_files:
        is_valid, phone, country_code, error = await validate_session(session_file)
        
        if is_valid:
            # 获取价格
            price, country_name, flag_emoji = db.get_price(country_code, Config.DEFAULT_PRICE)
            if not country_name:
                flag_emoji, country_name = get_country_info(country_code)
            
            # 重命名文件
            final_session_file = generate_session_filename(phone)
            try:
                if os.path.exists(final_session_file):
                    os.remove(final_session_file)
                    if os.path.exists(final_session_file + '-journal'):
                        os.remove(final_session_file + '-journal')
                
                import shutil
                shutil.move(session_file, final_session_file)
                if os.path.exists(session_file + '-journal'):
                    shutil.move(session_file + '-journal', final_session_file + '-journal')
                
                logger.info(f"Session 文件已移动: {final_session_file}")
            except Exception as e:
                logger.error(f"移动文件失败: {e}")
                if os.path.exists(session_file):
                    final_session_file = session_file
            
            # 创建数据库记录
            session_id = db.create_session_record(
                user_id=user_id,
                phone=phone,
                country_code=country_code,
                session_file=final_session_file,
                price=price
            )
            
            valid_sessions.append({
                'session_id': session_id,
                'phone': phone,
                'country_code': country_code,
                'country_name': country_name,
                'flag_emoji': flag_emoji,
                'price': price,
                'session_file': final_session_file
            })
        else:
            logger.error(f"Session 验证失败: {error}")
    
    valid_count = len(valid_sessions)
    total_price = sum(s['price'] for s in valid_sessions)
    
    # 通知用户
    await update.message.reply_text(f"""
✅ 提交完成

📊 处理结果：
• 成功：{valid_count} 个
• 失败：{account_count - valid_count} 个
• 总金额：{total_price} USDT

管理员正在审核中，请耐心等待...
""", reply_markup=main_menu_keyboard())
    
    # 发送一次通知给管理员（包含所有账号）
    if valid_sessions:
        await notify_admin_batch_sessions(
            context, user_id, valid_sessions, archive_path
        )
    
    return ConversationHandler.END


async def notify_admin_batch_sessions(context, user_id, sessions, archive_path):
    """批量通知管理员 - 一次性发送所有账号信息"""
    
    # 构建账号列表
    account_list = []
    for idx, s in enumerate(sessions, 1):
        account_list.append(
            f"{idx}. {s['flag_emoji']} {s['country_name']} | "
            f"<code>{s['phone']}</code> | "
            f"{s['price']} USDT"
        )
    
    total_price = sum(s['price'] for s in sessions)
    
    text = f"""
🆕 <b>新的批量 Session 待审核</b>

👤 提交用户：<code>{user_id}</code>
📊 账号数量：{len(sessions)} 个
💰 总金额：<b>{total_price} USDT</b>

📋 <b>账号列表：</b>
{''.join(account_list)}

📄 压缩包已发送到下方
"""
    
    # 生成审核按钮（批量操作）
    keyboard = [
        [
            InlineKeyboardButton(
                f"✅ 全部通过 +{total_price} USDT",
                callback_data=f"approve_batch:{','.join(str(s['session_id']) for s in sessions)}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ 拒绝全部",
                callback_data=f"reject_batch:{','.join(str(s['session_id']) for s in sessions)}"
            )
        ]
    ]
    
    try:
        # 发送文本消息
        await context.bot.send_message(
            chat_id=Config.ADMIN_GROUP_ID,
            text=text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # 发送压缩包
        if archive_path and os.path.exists(archive_path):
            await context.bot.send_document(
                chat_id=Config.ADMIN_GROUP_ID,
                document=open(archive_path, 'rb'),
                caption=f"批量 Session 压缩包 ({len(sessions)} 个账号)"
            )
    except Exception as e:
        logger.error(f"通知管理员失败: {e}")
