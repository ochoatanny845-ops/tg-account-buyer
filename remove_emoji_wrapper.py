#!/usr/bin/env python3
import re

with open('bot/handlers/user.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# 查找所有 e('...') 或 e("...") 使用（贪婪匹配单个Emoji字符）
matches = re.findall(r'e\([\'"]([^\'"]+)[\'"]\)', content)
print(f"Found {len(matches)} uses of e()")
if matches:
    print("Emojis used:", set(matches))
    
    # 移除 e() 包装，直接使用 Emoji
    # 用更精确的正则替换
    content = re.sub(r'e\([\'"]([^\'"]+)[\'"]\)', r'"\1"', content)
    
    # 移除导入
    content = re.sub(r'from bot\.utils\.emoji import emoji as e\n', '', content)
    
    with open('bot/handlers/user.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Removed all e() wrappers and import")
else:
    print("No e() usage found")
