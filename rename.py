import os

replacements = [
    ("KinaHub", "RazorHub"),
    ("kinahub", "razorhub"),
    ("MerchantOS", "RazorHubSeller"),
    ("merchantos", "razorhubseller")
]

directories = [
    r"c:\Users\krbur\OneDrive\Desktop\AI\KinaHub-main\frontend\src",
    r"c:\Users\krbur\OneDrive\Desktop\AI\KinaHub-main\backend",
]

def replace_in_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = content
        for old, new in replacements:
            new_content = new_content.replace(old, new)
            
        if content != new_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated {filepath}")
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

def walk_and_replace():
    for d in directories:
        for root, dirs, files in os.walk(d):
            # Skip node_modules, venv, .git, etc.
            if "node_modules" in root or "venv" in root or ".git" in root or "__pycache__" in root or ".system_generated" in root:
                continue
                
            for file in files:
                if file.endswith((".ts", ".tsx", ".js", ".jsx", ".py", ".html", ".css", ".json", ".md")):
                    filepath = os.path.join(root, file)
                    replace_in_file(filepath)

if __name__ == "__main__":
    walk_and_replace()
