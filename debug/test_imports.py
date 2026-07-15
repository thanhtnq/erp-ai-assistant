"""Test all imports work correctly."""
from api.services.erp_db import (
    query_sales_history,
    query_current_stock,
    query_duplicate_ap_invoices,
    query_new_vendor_high_value,
    query_inventory_anomalies,
    query_finance_anomalies,
)
print("All imports OK")
