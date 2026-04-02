#!/usr/bin/env python3
import re

files = ['bot/handlers/user.py', 'bot/handlers/admin.py']

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换 <emoji id="..."> 为 <tg-emoji emoji-id="...">
    content = re.sub(r'<emoji id="([^"]+)">([^<]+)</emoji>', r'<tg-emoji emoji-id="\1">\2</tg-emoji>', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed {filepath}")

print("Done!")
