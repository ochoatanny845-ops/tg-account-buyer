#!/usr/bin/env python3
import re

files = ['bot/handlers/user.py', 'bot/handlers/admin.py']

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 移除所有嵌套的 <emoji> 和 <tg-emoji> 标签
    # 策略：找到最内层的 tg-emoji，移除外层的所有包装
    
    # 先移除所有 <emoji id="..."> 开始标签
    content = re.sub(r'<emoji id="[^"]+?">', '', content)
    
    # 移除所有 </emoji> 结束标签
    content = re.sub(r'</emoji>', '', content)
    
    # 现在应该只剩下 <tg-emoji ...>...</tg-emoji>
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Cleaned {filepath}")

print("Done!")
