#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修改 user.py 以支持转发 ZIP 文件"""

import re

# 读取文件
with open('bot/handlers/user.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 1. 修改 process_session 函数签名，添加 archive_path 参数
old_sig = r'async def process_session\(update: Update, context: ContextTypes\.DEFAULT_TYPE, \s*session_file: str, phone: str = None\):'
new_sig = 'async def process_session(update: Update, context: ContextTypes.DEFAULT_TYPE, \n                         session_file: str, phone: str = None, archive_path: str = None):'
content = re.sub(old_sig, new_sig, content, flags=re.MULTILINE)

# 2. 修改 notify_admin_new_session 调用，传递 archive_path
old_call = r'await notify_admin_new_session\(context, session_id, user_id, phone, country_code, \s*country_name, flag_emoji, price, final_session_file\)'
new_call = 'await notify_admin_new_session(context, session_id, user_id, phone, country_code, \n                                   country_name, flag_emoji, price, final_session_file, archive_path)'
content = re.sub(old_call, new_call, content, flags=re.MULTILINE)

# 3. 修改 notify_admin_new_session 函数签名
old_notify_sig = r'async def notify_admin_new_session\(context: ContextTypes\.DEFAULT_TYPE, session_id: int,\s*user_id: int, phone: str, country_code: str,\s*country_name: str, flag_emoji: str, price: float,\s*session_file: str\):'
new_notify_sig = '''async def notify_admin_new_session(context: ContextTypes.DEFAULT_TYPE, session_id: int,
                                   user_id: int, phone: str, country_code: str,
                                   country_name: str, flag_emoji: str, price: float,
                                   session_file: str, archive_path: str = None):'''
content = re.sub(old_notify_sig, new_notify_sig, content, flags=re.MULTILINE)

# 4. 修改发送文件逻辑
old_send = r'# 如果有 Session 文件，也发送文件\s*if os\.path\.exists\(session_file\):\s*await context\.bot\.send_document\(\s*chat_id=Config\.ADMIN_GROUP_ID,\s*document=open\(session_file, \'rb\'\),\s*caption=f"Session 文件 #\{session_id\}"\s*\)'
new_send = '''# 如果有压缩文件，发送压缩文件；否则发送 Session 文件
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
            )'''
content = re.sub(old_send, new_send, content, flags=re.MULTILINE | re.DOTALL)

# 5. 修改 receive_session_file，保存并传递 archive_path
old_process_call = r'await process_session\(update, context, session_file, None\)'
new_process_call = 'await process_session(update, context, session_file, None, archive_path)'
content = re.sub(old_process_call, new_process_call, content)

# 写回文件
with open('bot/handlers/user.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
