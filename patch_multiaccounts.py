#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""替换 receive_session_file 及相关函数"""

import re

# 读取原文件
with open('bot/handlers/user.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 读取新函数
with open('new_upload_functions.py', 'r', encoding='utf-8') as f:
    new_functions = f.read()

# 找到并替换 receive_session_file 函数
# 从函数定义开始到下一个 async def 之前
pattern = r'async def receive_session_file\(.*?\n(?=async def \w+|$)'
match = re.search(pattern, content, re.DOTALL)

if match:
    old_function = match.group(0)
    # 从 new_functions 中提取新的函数实现（去掉注释行）
    new_impl = new_functions.split('"""改进的 Session 上传处理"""')[1].strip()
    
    # 替换
    content = content.replace(old_function, new_impl + '\n\n')
    
    print(f"Replaced receive_session_file")
else:
    print("Could not find receive_session_file")

# 写回
with open('bot/handlers/user.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
