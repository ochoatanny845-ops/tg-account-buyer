#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复引号冲突 - 将 HTML 标签替换为 e() 函数调用"""

import re

filepath = 'bot/handlers/user.py'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 查找所有 "<tg-emoji emoji-id="...">X</tg-emoji>" 模式
# 替换为 f"{e('X')}"

# 模式：在双引号字符串内的 tg-emoji 标签
pattern = r'<tg-emoji emoji-id="([^"]+)">([^<]+)</tg-emoji>'

def replace_with_function(match):
    emoji_id = match.group(1)
    emoji_char = match.group(2)
    return f"{{e('{emoji_char}')}}"

# 替换
content = re.sub(pattern, replace_with_function, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Fixed {filepath}")
