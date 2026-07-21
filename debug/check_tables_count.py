import re

# Check SQL schema
with open('scripts/create_erp_extract_tables.sql', encoding='utf-8') as f:
    content = f.read()
tables = re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', content)
print(f'SQL Schema: {len(tables)} tables')
for t in tables:
    print(f'  - {t}')

print()

# Check extract script
with open('scripts/extract_erp_to_sqlite.py', encoding='utf-8') as f:
    content = f.read()
mappings = re.findall(r'"sqlite": "(\w+)"', content)
print(f'Extract Script: {len(mappings)} table mappings')
for m in mappings:
    print(f'  - {m}')
