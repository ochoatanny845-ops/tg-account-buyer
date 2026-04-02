#!/usr/bin/env python3
import re

# 读取
with open('bot/handlers/user.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

with open('simplified_upload.py', 'r', encoding='utf-8') as f:
    new_func = f.read().split('"""简化版的多账号上传处理 - 只统计和收集密码"""')[1].strip()

# 找到并替换 receive_session_file 函数
pattern = r'async def receive_session_file\(update.*?\n(?=\nasync def \w+)'
match = re.search(pattern, content, re.DOTALL)

if match:
    content = content.replace(match.group(0), new_func + '\n')
    print("Replaced receive_session_file")
else:
    print("ERROR: Could not find receive_session_file")

with open('bot/handlers/user.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
