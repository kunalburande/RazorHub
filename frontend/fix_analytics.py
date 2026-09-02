import re

file_path = r"c:\Users\krbur\OneDrive\Desktop\KinaHub-main\frontend\src\dokkany\components\AnalyticsCharts.tsx"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Add import if missing
if 'formatCurrency' not in content:
    content = content.replace(
        'import type { Product } from "../interfaces";',
        'import type { Product } from "../interfaces";\nimport { formatCurrency } from "../utils/productUtils";'
    )

content = content.replace(
    '${donutSlices[hoveredSlice].totalValue.toLocaleString(',
    '{formatCurrency(donutSlices[hoveredSlice].totalValue)}'
)
# Note: we need to handle the newlines in the original code, or just use regex.

# Replace various currency usages
replacements = [
    (r'\$\n\s*\{donutSlices\[hoveredSlice\]\.totalValue\.toLocaleString\(\n\s*"en-US",\n\s*\)\}', r'{formatCurrency(donutSlices[hoveredSlice].totalValue)}'),
    (r'\$\{totalCatalogWorth\.toLocaleString\("en-US"\)\}', r'{formatCurrency(totalCatalogWorth)}'),
    (r'\(\$\{topValuedCategory\?\.totalValue\.toLocaleString\("en-US"\)\}\)', r'({topValuedCategory ? formatCurrency(topValuedCategory.totalValue) : ""})'),
    (r'\$\{cat\.totalValue\.toLocaleString\("en-US"\)\}', r'{formatCurrency(cat.totalValue)}'),
    (r'\$\{cat\.avgPrice\.toLocaleString\("en-US"\)\}', r'{formatCurrency(cat.avgPrice)}'),
    
    # Also in toolExecutor.ts? Let's just fix AnalyticsCharts first.
]

for pattern, repl in replacements:
    content = re.sub(pattern, repl, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Updated AnalyticsCharts.tsx")
