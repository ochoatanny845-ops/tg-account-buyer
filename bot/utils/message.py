#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
消息发送辅助函数 - 自动处理 Emoji 和 parse_mode
"""
from bot.utils.emoji import emoji as e


async def send_text(update_or_bot, text, **kwargs):
    """
    发送文本消息，自动添加 parse_mode='HTML'
    
    Args:
        update_or_bot: Update 对象或 Bot 对象
        text: 消息文本（可以使用 e() 函数）
        **kwargs: 其他参数（reply_markup 等）
    """
    # 确保有 parse_mode
    if 'parse_mode' not in kwargs:
        kwargs['parse_mode'] = 'HTML'
    
    # 判断是 Update 还是 Bot
    if hasattr(update_or_bot, 'message'):
        # 是 Update 对象
        return await update_or_bot.message.reply_text(text, **kwargs)
    else:
        # 是 Bot 对象，需要 chat_id
        chat_id = kwargs.pop('chat_id')
        return await update_or_bot.send_message(chat_id=chat_id, text=text, **kwargs)


# 便捷别名
reply = send_text
