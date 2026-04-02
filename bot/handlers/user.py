#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户功能处理器
"""
import os
import logging
import zipfile
import rarfile
import tempfile
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.config import Config
from bot.database import Database
from bot.keyboards.user_kb import main_menu_keyboard, cancel_keyboard, withdrawal_confirm_keyboard
from bot.keyboards.admin_kb import session_review_keyboard
from bot.utils.validator import (
    validate_session,
    validate_session_with_password,
    send_verification_code,
    login_with_code,
    login_with_password,
    generate_session_filename
)
from bot.utils.country import get_country_info, format_price_list
from bot.utils.emoji import emoji as e

logger = logging.getLogger(__name__)

# 会话状态
WAITING_PHONE, WAITING_CODE, WAITING_PASSWORD, WAITING_SESSION_FILE, WAITING_SESSION_PASSWORDS, WAITING_TRC20, WAITING_AMOUNT = range(7)

# 初始化数据库
db = Database(Config.DATABASE_URL)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """开始命令"""
    user = update.effective_user
    
    # 创建用户
    db.create_user(user.id, user.username)
    
    welcome_text = f"""
👋 欢迎使用 Telegram 账号收购机器人！

🎯 <b>我们收购：</b>
• 已开启 2FA 的 Telegram 账号
• 支持全球各国家/地区账号

💰 <b>快速开始：</b>
1. 点击"💰 查看价格"查看收购价格
2. 点击"📱 接码登录"或"📤 上传 Session"提交账号
3. 等待管理员审核（通常 1-24 小时）
4. 审核通过后余额自动到账
5. 达到提现金额即可申请提现

📝 <b>提现说明：</b>
• 最低提现：{Config.MIN_WITHDRAWAL} USDT
• 手续费：{Config.WITHDRAWAL_FEE} USDT
• 支付方式：TRC20

有任何问题请联系管理员 @your_admin
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )


async def view_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看价格"""
    prices = db.get_all_prices()
    
    if not prices:
        text = f"""
📋 <b>当前收购价格</b>

默认价格：<b>{Config.DEFAULT_PRICE} USDT</b>

💡 <i>所有开启 2FA 的账号均按默认价格收购
管理员可根据市场行情随时调整价格</i>
"""
    else:
        # 转换为元组格式
        price_tuples = [(p.country_code, p.country_name, p.flag_emoji, p.price) for p in prices]
        text = format_price_list(price_tuples)
        text += f"\n💡 <i>未列出的国家按默认价格 {Config.DEFAULT_PRICE} USDT 收购</i>"
    
    await update.message.reply_text(text, parse_mode='HTML')


async def my_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """我的余额"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ 用户不存在，请先发送 /start")
        return
    
    text = f"""
💵 <b>我的余额</b>

当前余额：<b>{user.balance:.2f} USDT</b>
TRC20 地址：<code>{user.trc20_address or '未设置'}</code>

{'✅ 可以提现' if user.balance >= Config.MIN_WITHDRAWAL else f'❌ 余额不足（最低 {Config.MIN_WITHDRAWAL} USDT）'}

💡 使用"⚙️ 设置地址"按钮可以修改 TRC20 地址
"""
    
    await update.message.reply_text(text, parse_mode='HTML')


async def start_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """开始接码登录流程"""
    logger.info(f"[DEBUG] start_login 被调用，用户ID: {update.effective_user.id}")
    await update.message.reply_text(
        "📱 <b>接码登录</b>\n\n"
        "请发送您的手机号（包含国家区号）\n"
        "例如：+86 13800138000\n\n"
        "⚠️ <b>注意：</b>\n"
        "• 账号必须已开启 2FA\n"
        "• 登录后会生成 Session 文件\n"
        "• 发送 /cancel 取消操作",
        parse_mode='HTML',
        reply_markup=cancel_keyboard()
    )
    return WAITING_PHONE


async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """接收手机号"""
    logger.info(f"[DEBUG] receive_phone 被调用，收到文本: {update.message.text}")
    phone = update.message.text.strip()
    
    if phone == "❌ 取消":
        await update.message.reply_text(
            "❌ 已取消操作",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # 清理手机号格式（移除空格、横线等）
    phone_cleaned = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # 确保以 + 开头
    if not phone_cleaned.startswith('+'):
        phone_cleaned = '+' + phone_cleaned
    
    logger.info(f"用户输入手机号: {phone} -> 清理后: {phone_cleaned}")
    
    # 保存手机号
    context.user_data['phone'] = phone_cleaned
    context.user_data['session_file'] = generate_session_filename(phone_cleaned)
    
    await update.message.reply_text("⏳ 正在发送验证码...")
    
    # 立即发送验证码
    success, phone_code_hash, error = await send_verification_code(phone_cleaned, context.user_data['session_file'])
    
    if not success:
        await update.message.reply_text(
            f"❌ {error}\n\n"
            f"请检查手机号格式或重试",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # 保存 phone_code_hash
    context.user_data['phone_code_hash'] = phone_code_hash
    
    await update.message.reply_text(
        f"📲 验证码已发送到 <code>{phone_cleaned}</code>\n\n"
        f"请输入收到的验证码：",
        parse_mode='HTML'
    )
    return WAITING_CODE


async def receive_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """接收验证码"""
    logger.info(f"[DEBUG] receive_code 被调用，收到验证码")
    code = update.message.text.strip()
    phone = context.user_data.get('phone')
    session_file = context.user_data.get('session_file')
    phone_code_hash = context.user_data.get('phone_code_hash')
    
    if not phone or not session_file or not phone_code_hash:
        logger.error(f"[DEBUG] 会话状态丢失: phone={phone}, session_file={session_file}, phone_code_hash={phone_code_hash}")
        await update.message.reply_text(
            "❌ 会话已过期，请重新开始",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    logger.info(f"[DEBUG] 准备登录: phone={phone}, code={code}")
    await update.message.reply_text("⏳ 正在验证...")
    
    # 尝试使用验证码登录
    success, needs_password, error = await login_with_code(phone, code, phone_code_hash, session_file)
    
    if success:
        # 登录成功，不需要密码（账号未开启 2FA）
        await update.message.reply_text(
            "❌ 账号未开启 2FA\n\n"
            "我们只收购已开启 2FA 的账号\n"
            "请先开启 2FA 后再提交",
            reply_markup=main_menu_keyboard()
        )
        # 删除 Session 文件
        try:
            os.remove(session_file)
            os.remove(session_file + '-journal')
        except:
            pass
        return ConversationHandler.END
    
    if needs_password:
        # 需要 2FA 密码
        await update.message.reply_text(
            "🔐 <b>需要 2FA 密码</b>\n\n"
            "请输入您的 2FA 密码（云密码）：",
            parse_mode='HTML'
        )
        return WAITING_PASSWORD
    
    # 验证码错误
    await update.message.reply_text(
        f"❌ {error}\n\n"
        f"请重新开始",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END


async def receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """接收 2FA 密码"""
    password = update.message.text.strip()
    phone = context.user_data.get('phone')
    session_file = context.user_data.get('session_file')
    
    if not phone or not session_file:
        await update.message.reply_text(
            "❌ 会话已过期，请重新开始",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    await update.message.reply_text("⏳ 正在验证 2FA 密码...")
    
    # 使用密码登录
    success, error = await login_with_password(phone, password, session_file)
    
    if not success:
        await update.message.reply_text(
            f"❌ {error}\n\n"
            f"请重新开始",
            reply_markup=main_menu_keyboard()
        )
        # 删除 Session 文件
        try:
            os.remove(session_file)
            os.remove(session_file + '-journal')
        except:
            pass
        return ConversationHandler.END
    
    # 登录成功，处理 Session
    await process_session(update, context, session_file, phone)
    
    return ConversationHandler.END


async def start_upload_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """开始上传 Session 流程"""
    await update.message.reply_text(
        "📤 <b>上传 Session 文件</b>\n\n"
        "请发送您的 Session 压缩包：\n"
        "• 支持 .zip 和 .rar 格式\n"
        "• 压缩包内应包含 .session 文件\n\n"
        "⚠️ <b>注意：</b>\n"
        "• 仅支持 Telethon Session 文件\n"
        "• 账号必须已开启 2FA\n"
        "• 发送 /cancel 取消操作",
        parse_mode='HTML',
        reply_markup=cancel_keyboard()
    )
    return WAITING_SESSION_FILE


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
    
    # 保存信息
    context.user_data['archive_path'] = archive_path
    context.user_data['session_count'] = account_count
    context.user_data['passwords_provided'] = matched_passwords
    
    # 处理所有 Session 文件
    success_count = 0
    for session_file in session_files:
        try:
            await process_session(update, context, session_file, None, archive_path)
            success_count += 1
        except Exception as e:
            logger.error(f"处理 Session 失败: {session_file}, {e}")
    
    # 显示最终结果
    result_text = f"""
✅ 提交完成

📊 处理结果：
• 成功提交：{success_count} 个
• 失败：{account_count - success_count} 个

管理员正在审核中，请耐心等待...
"""
    await update.message.reply_text(result_text, reply_markup=main_menu_keyboard())
    
    return ConversationHandler.END

async def process_session(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                         session_file: str, phone: str = None, archive_path: str = None):
    """处理 Session 文件（接码登录和上传共用）"""
    user_id = update.effective_user.id
    
    # 验证 Session
    is_valid, detected_phone, country_code, error = await validate_session(session_file)
    
    if not is_valid:
        await update.message.reply_text(
            f"❌ Session 验证失败\n\n"
            f"原因：{error}\n\n"
            f"请确保账号已开启 2FA",
            reply_markup=main_menu_keyboard()
        )
        # 删除无效文件
        try:
            os.remove(session_file)
        except:
            pass
        return
    
    phone = phone or detected_phone
    
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
        
        # 使用 shutil.move 移动文件
        import shutil
        shutil.move(session_file, final_session_file)
        logger.info(f"Session 文件已移动: {final_session_file}")
        
        # 同时移动 journal 文件（如果存在）
        if os.path.exists(session_file + '-journal'):
            shutil.move(session_file + '-journal', final_session_file + '-journal')
            
    except Exception as e:
        logger.error(f"移动 Session 文件失败: {e}")
        # 如果移动失败，检查原文件是否仍然存在
        if os.path.exists(session_file):
            final_session_file = session_file
            logger.info(f"使用原始 Session 文件: {session_file}")
        else:
            logger.error(f"Session 文件丢失: {session_file}")
    
    # 创建 Session 记录
    session_id = db.create_session_record(
        user_id=user_id,
        phone=phone,
        country_code=country_code,
        session_file=final_session_file,
        price=price
    )
    
    # 通知用户
    await update.message.reply_text(
        f"✅ <b>Session 已提交审核</b>\n\n"
        f"📱 手机号：<code>{phone}</code>\n"
        f"{flag_emoji} 国家：{country_name} <code>{country_code}</code>\n"
        f"💰 预计收购价：<b>{price} USDT</b>\n\n"
        f"⏳ 管理员正在审核中，请耐心等待...",
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )
    
    # 发送到管理员群组
    await notify_admin_new_session(context, session_id, user_id, phone, country_code, 
                                   country_name, flag_emoji, price, final_session_file, archive_path)


async def notify_admin_new_session(context: ContextTypes.DEFAULT_TYPE, session_id: int,
                                   user_id: int, phone: str, country_code: str,
                                   country_name: str, flag_emoji: str, price: float,
                                   session_file: str, archive_path: str = None):
    """通知管理员有新的 Session 待审核"""
    text = f"""
🆕 <b>新的 Session 待审核</b>

📋 <b>Session 信息：</b>
• ID: <code>{session_id}</code>
• 提交用户: <code>{user_id}</code>
• 手机号: <code>{phone}</code>
• {flag_emoji} 国家: {country_name} <code>{country_code}</code>
• 💰 收购价: <b>{price} USDT</b>

📄 Session 文件: <code>{session_file}</code>
"""
    
    keyboard = session_review_keyboard(session_id, price)
    
    try:
        # 发送到管理员群组
        await context.bot.send_message(
            chat_id=Config.ADMIN_GROUP_ID,
            text=text,
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        # 如果有压缩文件，发送压缩文件；否则发送 Session 文件
        if archive_path and os.path.exists(archive_path):
            await context.bot.send_document(
                chat_id=Config.ADMIN_GROUP_ID,
                document=open(archive_path, 'rb'),
                caption=f"Session 压缩包 #{session_id}"
            )
        elif os.path.exists(session_file):
            await context.bot.send_document(
                chat_id=Config.ADMIN_GROUP_ID,
                document=open(session_file, 'rb'),
                caption=f"Session 文件 #{session_id}"
            )
    except Exception as e:
        logger.error(f"通知管理员失败: {e}")


async def set_trc20_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """设置 TRC20 地址"""
    await update.message.reply_text(
        "⚙️ <b>设置 TRC20 地址</b>\n\n"
        "请发送您的 TRC20 收款地址：\n\n"
        "⚠️ 地址格式：以 T 开头，长度 34 位",
        parse_mode='HTML',
        reply_markup=cancel_keyboard()
    )
    return WAITING_TRC20


async def start_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """开始提现流程"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ 用户不存在，请先发送 /start")
        return ConversationHandler.END
    
    if user.balance < Config.MIN_WITHDRAWAL:
        await update.message.reply_text(
            f"❌ 余额不足\n\n"
            f"当前余额：{user.balance:.2f} USDT\n"
            f"最低提现：{Config.MIN_WITHDRAWAL} USDT",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    if not user.trc20_address:
        await update.message.reply_text(
            "请先设置您的 TRC20 地址\n\n"
            "请发送您的 TRC20 地址：",
            reply_markup=cancel_keyboard()
        )
        return WAITING_TRC20
    
    # 已有地址，直接询问金额
    await update.message.reply_text(
        f"💸 <b>申请提现</b>\n\n"
        f"当前余额：<b>{user.balance:.2f} USDT</b>\n"
        f"手续费：<b>{Config.WITHDRAWAL_FEE} USDT</b>\n"
        f"TRC20 地址：<code>{user.trc20_address}</code>\n\n"
        f"请输入提现金额（最低 {Config.MIN_WITHDRAWAL} USDT）：",
        parse_mode='HTML',
        reply_markup=cancel_keyboard()
    )
    return WAITING_AMOUNT


async def receive_trc20(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """接收 TRC20 地址"""
    address = update.message.text.strip()
    
    if address == "❌ 取消":
        await update.message.reply_text(
            "❌ 已取消操作",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # 简单验证 TRC20 地址格式
    if not address.startswith('T') or len(address) != 34:
        await update.message.reply_text(
            "❌ TRC20 地址格式不正确\n"
            "地址应以 T 开头，长度为 34 位\n\n"
            "请重新输入："
        )
        return WAITING_TRC20
    
    # 保存地址
    user_id = update.effective_user.id
    db.set_trc20_address(user_id, address)
    
    await update.message.reply_text(
        f"✅ TRC20 地址已设置\n\n"
        f"地址：<code>{address}</code>\n\n"
        f"您可以随时修改地址",
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )
    
    return ConversationHandler.END


async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """接收提现金额"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    text = update.message.text.strip()
    
    if text == "❌ 取消":
        await update.message.reply_text(
            "❌ 已取消操作",
            reply_markup=main_menu_keyboard()
        )
        return ConversationHandler.END
    
    try:
        amount = float(text)
    except:
        await update.message.reply_text(
            "❌ 金额格式不正确\n"
            "请输入数字，例如：10 或 15.5"
        )
        return WAITING_AMOUNT
    
    if amount < Config.MIN_WITHDRAWAL:
        await update.message.reply_text(
            f"❌ 金额不能低于 {Config.MIN_WITHDRAWAL} USDT"
        )
        return WAITING_AMOUNT
    
    total = amount + Config.WITHDRAWAL_FEE
    
    if total > user.balance:
        await update.message.reply_text(
            f"❌ 余额不足\n\n"
            f"提现金额：{amount} USDT\n"
            f"手续费：{Config.WITHDRAWAL_FEE} USDT\n"
            f"需要总额：{total} USDT\n"
            f"当前余额：{user.balance} USDT\n\n"
            f"请输入较小的金额："
        )
        return WAITING_AMOUNT
    
    # 显示确认信息
    text = f"""
💸 <b>提现确认</b>

提现金额：<b>{amount} USDT</b>
手续费：<b>{Config.WITHDRAWAL_FEE} USDT</b>
实际到账：<b>{amount} USDT</b>
剩余余额：<b>{user.balance - total:.2f} USDT</b>

TRC20 地址：
<code>{user.trc20_address}</code>

⚠️ 请仔细核对地址，确认无误后点击下方按钮
"""
    
    keyboard = withdrawal_confirm_keyboard(amount, Config.WITHDRAWAL_FEE)
    
    await update.message.reply_text(
        text,
        parse_mode='HTML',
        reply_markup=keyboard
    )
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """取消操作"""
    await update.message.reply_text(
        "❌ 已取消操作",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """开始命令"""
    user = update.effective_user
    
    # 创建用户
    db.create_user(user.id, user.username)
    
    welcome_text = f"""
👋 欢迎使用 Telegram 账号收购机器人！

🎯 <b>我们收购：</b>
• 已开启 2FA 的 Telegram 账号
• 支持全球各国家/地区账号

💰 <b>快速开始：</b>
1. 点击"💰 查看价格"查看收购价格
2. 点击"📱 接码登录"或"📤 上传 Session"提交账号
3. 等待管理员审核（通常 1-24 小时）
4. 审核通过后余额自动到账
5. 达到提现金额即可申请提现

📝 <b>提现说明：</b>
• 最低提现：{Config.MIN_WITHDRAWAL} USDT
• 手续费：{Config.WITHDRAWAL_FEE} USDT
• 支付方式：TRC20

有任何问题请联系管理员 @your_admin
"""
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )


async def view_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看价格"""
    prices = db.get_all_prices()
    
    if not prices:
        text = f"""
📋 <b>当前收购价格</b>

默认价格：<b>{Config.DEFAULT_PRICE} USDT</b>

💡 <i>所有开启 2FA 的账号均按默认价格收购
管理员可根据市场行情随时调整价格</i>
"""
    else:
        # 转换为元组格式
        price_tuples = [(p.country_code, p.country_name, p.flag_emoji, p.price) for p in prices]
        text = format_price_list(price_tuples)
        text += f"\n💡 <i>未列出的国家按默认价格 {Config.DEFAULT_PRICE} USDT 收购</i>"
    
    await update.message.reply_text(text, parse_mode='HTML')


async def my_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """我的余额"""
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        await update.message.reply_text("❌ 用户不存在，请先发送 /start")
        return
    
    text = f"""
💵 <b>我的余额</b>

当前余额：<b>{user.balance:.2f} USDT</b>
TRC20 地址：<code>{user.trc20_address or '未设置'}</code>

{'✅ 可以提现' if user.balance >= Config.MIN_WITHDRAWAL else f'❌ 余额不足（最低 {Config.MIN_WITHDRAWAL} USDT）'}
"""
    
    await update.message.reply_text(text, parse_mode='HTML')


