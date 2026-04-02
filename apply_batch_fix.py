#!/usr/bin/env python3
import re

# 读取文件
with open('bot/handlers/user.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 读取新函数
with open('batch_session_handler.py', 'r', encoding='utf-8') as f:
    new_code = f.read()

# 提取 receive_session_file_v2 函数
new_func = re.search(r'async def receive_session_file_v2.*?(?=\n\nasync def )', new_code, re.DOTALL).group(0)

# 替换函数名
new_func = new_func.replace('receive_session_file_v2', 'receive_session_file')

# 提取 notify_admin_batch_sessions 函数
notify_func = re.search(r'async def notify_admin_batch_sessions.*$', new_code, re.DOTALL).group(0)

# 找到并替换 receive_session_file
pattern = r'async def receive_session_file\(.*?\n(?=\nasync def \w+)'
match = re.search(pattern, content, re.DOTALL)

if match:
    # 替换
    content = content.replace(match.group(0), new_func + '\n')
    
    # 在 process_session 后面添加 notify_admin_batch_sessions
    # 找到 process_session 函数结束的位置
    process_end = content.find('\nasync def notify_admin_new_session')
    if process_end > 0:
        content = content[:process_end] + '\n\n' + notify_func + '\n' + content[process_end:]
    
    print("Replaced receive_session_file and added notify_admin_batch_sessions")
else:
    print("ERROR: Could not find receive_session_file")

# 写回
with open('bot/handlers/user.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
