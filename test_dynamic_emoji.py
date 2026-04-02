#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试动态 Emoji"""

import os
from telegram import Bot
import asyncio

BOT_TOKEN = os.getenv('BOT_TOKEN', '8165838018:AAGfIdgxJnXJrLECxqtZTAc0Ie-XqOk0sck')
YOUR_CHAT_ID = 5991190607

async def test_emoji():
    bot = Bot(token=BOT_TOKEN)
    
    # 测试1：普通文本
    await bot.send_message(
        chat_id=YOUR_CHAT_ID,
        text="测试1：普通 Emoji 💰"
    )
    
    # 测试2：使用 tg-emoji 标签
    await bot.send_message(
        chat_id=YOUR_CHAT_ID,
        text='测试2：动态 Emoji <tg-emoji emoji-id="5377505475015235101">💰</tg-emoji>',
        parse_mode='HTML'
    )
    
    # 测试3：多个动态 Emoji
    await bot.send_message(
        chat_id=YOUR_CHAT_ID,
        text='测试3：多个 <tg-emoji emoji-id="5377505475015235101">💰</tg-emoji> <tg-emoji emoji-id="5332724926216428039">📱</tg-emoji> <tg-emoji emoji-id="5449683594425410231">📤</tg-emoji>',
        parse_mode='HTML'
    )
    
    print("✓ 所有测试消息已发送！")

if __name__ == '__main__':
    asyncio.run(test_emoji())
