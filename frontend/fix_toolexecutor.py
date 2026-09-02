import re

file_path = r"c:\Users\krbur\OneDrive\Desktop\KinaHub-main\frontend\src\dokkany\services\ai\toolExecutor.ts"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace $${ with ₹${
content = re.sub(r'\$\$\{', r'₹${', content)

# Replace "$xxx" with "₹xxx"
content = re.sub(r'"\$(\d+(?:,\d+)*(?:\.\d+)?)"', r'"₹\1"', content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated toolExecutor.ts")
