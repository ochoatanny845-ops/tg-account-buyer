#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram 账号收购机器人 - 主程序
"""
import sys
import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from bot.config import Config
from bot.handlers.user import (
    start, view_prices, my_balance,
    start_login, receive_phone, receive_code, receive_password,
    start_upload_session, receive_session_file,
    start_withdrawal, set_trc20_address, receive_trc20, receive_amount,
    cancel,
    WAITING_PHONE, WAITING_CODE, WAITING_PASSWORD, WAITING_SESSION_FILE, WAITING_TRC20, WAITING_AMOUNT
)
from bot.handlers.admin import (
    admin_prices, admin_setprice,
    handle_session_review, handle_withdrawal_confirm, handle_withdrawal_review
)

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    force=True,
    stream=sys.stdout  # 强制输出到标准输出
)

# 禁用输出缓冲
import sys
sys.stdout.reconfigure(line_buffering=True)

# 确保所有相关模块的日志都是 INFO 级别
logging.getLogger('bot.handlers.user').setLevel(logging.INFO)
logging.getLogger('bot.utils.validator').setLevel(logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def error_handler(update: object, context) -> None:
    """错误处理"""
    logger.error(f"Exception while handling an update: {context.error}")


def main():
    """主函数"""
    # 验证配置
    is_valid, message = Config.validate()
    if not is_valid:
        logger.error(f"配置验证失败：\n{message}")
        logger.error("请检查 .env 文件并确保所有必需的配置已填写")
        return
    
    logger.info("配置验证通过，开始启动机器人...")
    
    # 创建 sessions 目录
    if not os.path.exists(Config.SESSION_DIR):
        os.makedirs(Config.SESSION_DIR)
        logger.info(f"创建 Session 目录: {Config.SESSION_DIR}")
    
    # 创建应用
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # ===================
    # 用户命令处理器
    # ===================
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # ===================
    # 用户按钮处理器
    # ===================
    application.add_handler(MessageHandler(
        filters.Regex("^💰 查看价格$"),
        view_prices
    ))
    application.add_handler(MessageHandler(
        filters.Regex("^💵 我的余额$"),
        my_balance
    ))
    
    # ===================
    # 接码登录会话处理器
    # ===================
    login_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📱 接码登录$"), start_login)
        ],
        states={
            WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
            WAITING_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_code)],
            WAITING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_password)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ 取消$"), cancel)
        ],
    )
    application.add_handler(login_conv_handler)
    
    # ===================
    # 上传 Session 会话处理器
    # ===================
    upload_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^📤 上传 Session$"), start_upload_session)
        ],
        states={
            WAITING_SESSION_FILE: [
                MessageHandler(filters.Document.ALL, receive_session_file),
                MessageHandler(filters.TEXT, receive_session_file),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ 取消$"), cancel)
        ],
    )
    application.add_handler(upload_conv_handler)
    
    # ===================
    # 设置 TRC20 地址会话处理器
    # ===================
    trc20_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^⚙️ 设置地址$"), set_trc20_address)
        ],
        states={
            WAITING_TRC20: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_trc20)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ 取消$"), cancel)
        ],
    )
    application.add_handler(trc20_conv_handler)
    
    # ===================
    # 提现会话处理器
    # ===================
    withdrawal_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^💸 申请提现$"), start_withdrawal)
        ],
        states={
            WAITING_TRC20: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_trc20)],
            WAITING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            MessageHandler(filters.Regex("^❌ 取消$"), cancel)
        ],
    )
    application.add_handler(withdrawal_conv_handler)
    
    # ===================
    # 管理员命令处理器
    # ===================
    application.add_handler(CommandHandler("price", admin_prices))
    application.add_handler(CommandHandler("setprice", admin_setprice))
    
    # ===================
    # 回调查询处理器
    # ===================
    application.add_handler(CallbackQueryHandler(
        handle_session_review,
        pattern="^(approve_session|reject_session):"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_withdrawal_confirm,
        pattern="^(withdraw_confirm|withdraw_cancel)"
    ))
    application.add_handler(CallbackQueryHandler(
        handle_withdrawal_review,
        pattern="^(approve_withdrawal|reject_withdrawal):"
    ))
    
    # ===================
    # 错误处理器
    # ===================
    application.add_error_handler(error_handler)
    
    # ===================
    # 启动机器人
    # ===================
    logger.info("🚀 机器人启动成功！")
    logger.info(f"📋 配置信息：")
    logger.info(f"   - 管理员群组: {Config.ADMIN_GROUP_ID}")
    logger.info(f"   - 管理员用户: {Config.ADMIN_USER_IDS}")
    logger.info(f"   - 最低提现: {Config.MIN_WITHDRAWAL} USDT")
    logger.info(f"   - 提现手续费: {Config.WITHDRAWAL_FEE} USDT")
    logger.info(f"   - 默认价格: {Config.DEFAULT_PRICE} USDT")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
