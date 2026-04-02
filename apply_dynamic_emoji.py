#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动替换消息文本中的 Emoji 为动态版本"""

import re
from bot.utils.emoji import EMOJI_IDS

def replace_emojis_in_text(text):
    """将文本中的 Emoji 替换为动态版本的 HTML 标签"""
    for emoji_char, emoji_id in EMOJI_IDS.items():
        if emoji_char in text:
            # 替换为 HTML 格式
            html_emoji = f'<emoji id="{emoji_id}">{emoji_char}</emoji>'
            text = text.replace(emoji_char, html_emoji)
    return text

def process_file(filepath):
    """处理文件中的所有字符串"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # 查找所有多行字符串（用三引号包裹）
    def replace_in_multiline_string(match):
        original = match.group(0)
        # 提取引号和内容
        quotes = match.group(1)  # """ or '''
        inner = match.group(2)
        
        # 替换 Emoji
        new_inner = replace_emojis_in_text(inner)
        
        return quotes + new_inner + quotes
    
    # 替换三引号字符串中的 Emoji
    content = re.sub(r'("""|\'\'\')(.*?)\1', replace_in_multiline_string, content, flags=re.DOTALL)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Processed {filepath}")

# 处理所有文件
files = [
    'bot/handlers/user.py',
    'bot/handlers/admin.py'
]

for f in files:
    try:
        process_file(f)
    except Exception as e:
        print(f"Error processing {f}: {e}")

print("Done!")
