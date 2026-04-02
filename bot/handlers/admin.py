#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员功能处理器
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from bot.config import Config
from bot.database import Database
from bot.keyboards.admin_kb import withdrawal_review_keyboard
from bot.utils.country import get_country_info, format_price_list

logger = logging.getLogger(__name__)

# 初始化数据库
db = Database(Config.DATABASE_URL)


def admin_only(func):
    """管理员权限装饰器"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not Config.is_admin(user_id):
            await update.message.reply_text("❌ 您没有权限执行此操作")
            return
        return await func(update, context)
    return wrapper


@admin_only
async def admin_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看所有价格"""
    prices = db.get_all_prices()
    
    if not prices:
        text = f"📋 <b>当前收购价格</b>\n\n默认价格：<b>{Config.DEFAULT_PRICE} USDT</b>\n\n暂无自定义价格"
    else:
        price_tuples = [(p.country_code, p.country_name, p.flag_emoji, p.price) for p in prices]
        text = format_price_list(price_tuples)
        text += f"\n\n💡 默认价格：{Config.DEFAULT_PRICE} USDT"
    
    text += "\n\n使用方法：\n<code>/setprice +86 1.5</code> - 设置中国账号价格为 1.5 USDT"
    
    await update.message.reply_text(text, parse_mode='HTML')


@admin_only
async def admin_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """设置价格"""
    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ 用法错误\n\n"
            "正确用法：\n"
            "<code>/setprice +86 1.5</code>\n"
            "<code>/setprice +1 0.8</code>",
            parse_mode='HTML'
        )
        return
    
    country_code = context.args[0]
    if not country_code.startswith('+'):
        country_code = '+' + country_code
    
    try:
        price = float(context.args[1])
    except:
        await update.message.reply_text("❌ 价格格式错误，请输入数字")
        return
    
    if price < 0:
        await update.message.reply_text("❌ 价格不能为负数")
        return
    
    # 获取国家信息
    flag_emoji, country_name = get_country_info(country_code)
    
    # 设置价格
    db.set_price(country_code, country_name, flag_emoji, price)
    
    await update.message.reply_text(
        f"✅ 价格设置成功\n\n"
        f"{flag_emoji} {country_name} <code>{country_code}</code>\n"
        f"收购价格：<b>{price} USDT</b>",
        parse_mode='HTML'
    )


async def handle_session_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 Session 审核回调"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if not Config.is_admin(user_id):
        await query.answer("❌ 您没有权限执行此操作", show_alert=True)
        return
    
    if data.startswith("approve_session:"):
        session_id = int(data.split(":")[1])
        
        # 获取 Session 信息
        session = db.get_session_record(session_id)
        if not session:
            await query.edit_message_text("❌ Session 不存在")
            return
        
        # 审核通过
        db.approve_session(session_id, user_id)
        
        # 获取用户余额
        user = db.get_user(session.user_id)
        
        # 更新消息
        await query.edit_message_text(
            f"{query.message.text}\n\n"
            f"✅ <b>已通过审核</b>\n"
            f"审核人：<code>{user_id}</code>\n"
            f"用户余额：<b>{user.balance:.2f} USDT</b>",
            parse_mode='HTML'
        )
        
        # 通知用户
        try:
            await context.bot.send_message(
                chat_id=session.user_id,
                text=f"✅ <b>账号审核通过</b>\n\n"
                     f"📱 手机号：<code>{session.phone}</code>\n"
                     f"💰 收购价：<b>{session.price} USDT</b>\n"
                     f"💵 当前余额：<b>{user.balance:.2f} USDT</b>\n\n"
                     f"余额已到账，感谢您的信任！",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"通知用户失败: {e}")
    
    elif data.startswith("reject_session:"):
        parts = data.split(":")
        session_id = int(parts[1])
        reason_code = parts[2]
        
        reason_map = {
            "no_2fa": "未开启 2FA",
            "other": "其他原因"
        }
        reason = reason_map.get(reason_code, "未知原因")
        
        # 获取 Session 信息
        session = db.get_session_record(session_id)
        if not session:
            await query.edit_message_text("❌ Session 不存在")
            return
        
        # 审核拒绝
        db.reject_session(session_id, user_id, reason)
        
        # 更新消息
        await query.edit_message_text(
            f"{query.message.text}\n\n"
            f"❌ <b>已拒绝</b>\n"
            f"审核人：<code>{user_id}</code>\n"
            f"拒绝原因：{reason}",
            parse_mode='HTML'
        )
        
        # 通知用户
        try:
            await context.bot.send_message(
                chat_id=session.user_id,
                text=f"❌ <b>账号审核未通过</b>\n\n"
                     f"📱 手机号：<code>{session.phone}</code>\n"
                     f"拒绝原因：{reason}\n\n"
                     f"如有疑问请联系管理员",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"通知用户失败: {e}")


async def handle_withdrawal_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理提现确认回调"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if data.startswith("withdraw_confirm:"):
        amount = float(data.split(":")[1])
        
        # 获取用户信息
        user = db.get_user(user_id)
        if not user or not user.trc20_address:
            await query.edit_message_text("❌ 用户信息错误")
            return
        
        total = amount + Config.WITHDRAWAL_FEE
        
        if total > user.balance:
            await query.edit_message_text(
                f"❌ 余额不足\n\n"
                f"需要：{total} USDT\n"
                f"当前：{user.balance} USDT"
            )
            return
        
        # 创建提现记录
        withdrawal_id = db.create_withdrawal(
            user_id=user_id,
            amount=amount,
            fee=Config.WITHDRAWAL_FEE,
            trc20_address=user.trc20_address
        )
        
        # 通知用户
        await query.edit_message_text(
            f"✅ <b>提现申请已提交</b>\n\n"
            f"申请编号：<code>{withdrawal_id}</code>\n"
            f"提现金额：<b>{amount} USDT</b>\n"
            f"手续费：<b>{Config.WITHDRAWAL_FEE} USDT</b>\n"
            f"剩余余额：<b>{user.balance:.2f} USDT</b>\n\n"
            f"⏳ 管理员正在处理，请耐心等待...",
            parse_mode='HTML'
        )
        
        # 通知管理员
        admin_text = f"""
<tg-emoji emoji-id="5233326571099534068">💸</tg-emoji> <b>新的提现申请</b>

📋 <b>申请信息：</b>
• 申请编号：<code>{withdrawal_id}</code>
• 用户 ID：<code>{user_id}</code>
• 用户名：@{user.username or 'N/A'}
• 提现金额：<b>{amount} USDT</b>
• 手续费：<b>{Config.WITHDRAWAL_FEE} USDT</b>
• 实际支付：<b>{amount} USDT</b>

💳 <b>TRC20 地址：</b>
<code>{user.trc20_address}</code>

<tg-emoji emoji-id="5447644880824181073">⚠️</tg-emoji> 请手动转账后点击下方按钮确认
"""
        
        keyboard = withdrawal_review_keyboard(withdrawal_id)
        
        try:
            await context.bot.send_message(
                chat_id=Config.ADMIN_GROUP_ID,
                text=admin_text,
                parse_mode='HTML',
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"通知管理员失败: {e}")
    
    elif data == "withdraw_cancel":
        await query.edit_message_text("❌ 已取消提现")


async def handle_withdrawal_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理提现审核回调"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if not Config.is_admin(user_id):
        await query.answer("❌ 您没有权限执行此操作", show_alert=True)
        return
    
    if data.startswith("approve_withdrawal:"):
        withdrawal_id = int(data.split(":")[1])
        
        # 获取提现信息
        withdrawal = db.get_withdrawal(withdrawal_id)
        if not withdrawal:
            await query.edit_message_text("❌ 提现记录不存在")
            return
        
        # 完成提现
        db.complete_withdrawal(withdrawal_id, user_id)
        
        # 更新消息
        await query.edit_message_text(
            f"{query.message.text}\n\n"
            f"✅ <b>已完成支付</b>\n"
            f"处理人：<code>{user_id}</code>",
            parse_mode='HTML'
        )
        
        # 通知用户
        try:
            await context.bot.send_message(
                chat_id=withdrawal.user_id,
                text=f"✅ <b>提现已完成</b>\n\n"
                     f"申请编号：<code>{withdrawal_id}</code>\n"
                     f"提现金额：<b>{withdrawal.amount} USDT</b>\n"
                     f"TRC20 地址：<code>{withdrawal.trc20_address}</code>\n\n"
                     f"请查收钱包，感谢使用！",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"通知用户失败: {e}")
    
    elif data.startswith("reject_withdrawal:"):
        withdrawal_id = int(data.split(":")[1])
        
        # 获取提现信息
        withdrawal = db.get_withdrawal(withdrawal_id)
        if not withdrawal:
            await query.edit_message_text("❌ 提现记录不存在")
            return
        
        # 退回余额
        db.update_balance(withdrawal.user_id, withdrawal.amount + withdrawal.fee)
        
        # 更新消息
        await query.edit_message_text(
            f"{query.message.text}\n\n"
            f"❌ <b>已拒绝</b>\n"
            f"处理人：<code>{user_id}</code>\n"
            f"余额已退回",
            parse_mode='HTML'
        )
        
        # 通知用户
        try:
            await context.bot.send_message(
                chat_id=withdrawal.user_id,
                text=f"❌ <b>提现申请被拒绝</b>\n\n"
                     f"申请编号：<code>{withdrawal_id}</code>\n"
                     f"金额已退回您的账户\n\n"
                     f"如有疑问请联系管理员",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"通知用户失败: {e}")
