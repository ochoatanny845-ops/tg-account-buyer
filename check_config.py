import os
from dotenv import load_dotenv

load_dotenv()

print("=== 配置检查 ===")
print(f"BOT_TOKEN: {os.getenv('BOT_TOKEN')[:20]}... (已隐藏)")
print(f"API_ID: {os.getenv('API_ID')}")
print(f"API_HASH: {os.getenv('API_HASH')[:10]}... (已隐藏)")
print(f"ADMIN_GROUP_ID: {os.getenv('ADMIN_GROUP_ID')}")
print(f"ADMIN_USER_IDS: {os.getenv('ADMIN_USER_IDS')}")
