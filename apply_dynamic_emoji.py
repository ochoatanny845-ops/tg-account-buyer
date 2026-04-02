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
    
    # 确保所有 reply_text 都有 parse_mode='HTML'
    # 简单策略：在所有 reply_text( 后面没有 parse_mode 的地方添加
    lines = content.split('\n')
    new_lines = []
    
    for i, line in enumerate(lines):
        new_lines.append(line)
        
        # 如果这行包含 reply_text 且是多行调用的开始
        if 'reply_text(' in line and 'parse_mode' not in line:
            # 检查后续几行是否有 parse_mode
            has_parse_mode = False
            for j in range(i+1, min(i+10, len(lines))):
                if 'parse_mode' in lines[j]:
                    has_parse_mode = True
                    break
                if ')' in lines[j] and 'reply_text' not in lines[j]:
                    # 找到了结束的括号
                    break
            
            # 如果没有 parse_mode，需要添加
            # 但这个逻辑太复杂了，暂时手动处理
    
    content = '\n'.join(new_lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Processed {filepath}")

# 处理 user.py
process_file('bot/handlers/user.py')
print("Done!")
