#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""替换所有 Emoji 为动态会员 Emoji"""

import re
from emoji_map import EMOJI_MAP

def replace_emoji_in_text(text):
    """将文本中的 Emoji 替换为自定义 Emoji 标签"""
    for emoji, emoji_id in EMOJI_MAP.items():
        # 替换为 <emoji id="xxx">fallback</emoji> 格式
        text = text.replace(emoji, f'<emoji id="{emoji_id}">{emoji}</emoji>')
    return text

def process_file(filename):
    """处理单个文件"""
    print(f"Processing {filename}...")
    
    with open(filename, 'r', encoding='utf-8-sig') as f:
        content = f.read()
    
    # 统计替换次数
    count = 0
    for emoji in EMOJI_MAP.keys():
        count += content.count(emoji)
    
    if count == 0:
        print(f"  No emoji found in {filename}")
        return
    
    # 替换 Emoji
    new_content = replace_emoji_in_text(content)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  Replaced {count} emojis in {filename}")

# 需要处理的文件列表
files_to_process = [
    'bot/handlers/user.py',
    'bot/handlers/admin.py',
    'bot/keyboards/user_kb.py',
    'bot/keyboards/admin_kb.py',
]

for file in files_to_process:
    try:
        process_file(file)
    except FileNotFoundError:
        print(f"  File not found: {file}")
    except Exception as e:
        print(f"  Error processing {file}: {e}")

print("\nDone!")
