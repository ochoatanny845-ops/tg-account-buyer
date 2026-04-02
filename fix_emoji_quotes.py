#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复引号冲突 - 使用单引号包裹双引号字符串"""

import re

def fix_emoji_quotes(content):
    """修复 Emoji 标签中的引号冲突"""
    
    # 策略：将包含 <emoji id="..."> 的字符串改用单引号
    # 匹配模式：双引号字符串中包含 <emoji
    
    # 找到所有双引号字符串
    def replace_quotes(match):
        string = match.group(0)
        # 如果字符串包含 <emoji，则转换引号
        if '<emoji id=' in string:
            # 去掉外层双引号
            inner = string[1:-1]
            # 用单引号重新包裹
            return "'" + inner + "'"
        return string
    
    # 匹配双引号字符串（处理转义）
    content = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', replace_quotes, content)
    
    return content

files = [
    'bot/handlers/user.py',
    'bot/handlers/admin.py',
    'bot/keyboards/user_kb.py',
    'bot/keyboards/admin_kb.py',
]

for filepath in files:
    print(f"Fixing {filepath}...")
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    new_content = fix_emoji_quotes(content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  Done")

print("All fixed!")
