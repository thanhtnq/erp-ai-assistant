"""Test the ERP database service layer."""
from api.services.erp_db import (
    query_sales_history,
    query_current_stock,
    query_duplicate_ap_invoices,
    query_new_vendor_high_value,
    query_inventory_anomalies,
    query_finance_anomalies,
)

masterfn = "demo2011mfn"
companyfn = "p11011004464072155"

print("=== Sales History (all time) ===")
rows = query_sales_history(masterfn, companyfn, days=0)


print(f"  {len(rows)} rows")
for r in rows[:5]:
    print(f"  SKU={r['sku']}, loc={r['location']}, qty={r['total_qty']}, amt={r['total_amount']}, orders={r['order_count']}")

print("\n=== Current Stock ===")
rows = query_current_stock(masterfn, companyfn)
print(f"  {len(rows)} rows")
for r in rows[:5]:
    print(f"  SKU={r['sku']}, desc={r['description']}, on_hand={r['on_hand_qty']}, value={r['stock_value']}")

print("\n=== Duplicate AP Invoices ===")
findings = query_duplicate_ap_invoices(masterfn, companyfn, limit=10)
print(f"  {len(findings)} findings")
for f in findings:
    print(f"  [{f['severity']}] {f['title']}: {f['description'][:100]}")

print("\n=== New Vendor High Value ===")
findings = query_new_vendor_high_value(masterfn, companyfn, limit=5)
print(f"  {len(findings)} findings")
for f in findings:
    print(f"  [{f['severity']}] {f['title']}: {f['description'][:100]}")

print("\n=== Inventory Anomalies ===")
findings = query_inventory_anomalies(masterfn, companyfn, limit=5)
print(f"  {len(findings)} findings")
for f in findings:
    print(f"  [{f['severity']}] {f['title']}: {f['description'][:100]}")

print("\n=== Finance Anomalies ===")
findings = query_finance_anomalies(masterfn, companyfn, limit=5)
print(f"  {len(findings)} findings")
for f in findings:
    print(f"  [{f['severity']}] {f['title']}: {f['description'][:100]}")

print("\n=== DONE ===")
