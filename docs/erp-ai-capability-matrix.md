# ERP AI Assistant Capability Matrix

Assessment of the current repo against the requirement list in the image.
This is a practical coverage view for development and testing.

## Summary

- The assistant already covers step-by-step ERP guidance for sales, purchase, inventory, finance, CRM, HR, project, and general topics.
- Session history is now scoped and paginated.
- Image rendering for step-by-step answers is supported in the CFML frontend.
- The repo does **not yet** provide the product-level AI features listed in the image, such as invoice OCR, journal suggestions, anomaly detection, or InvoiceNow accreditation checks.

## Coverage Table

| ID | Requirement | Status | Current coverage | Gap |
|---|---|---|---|---|
| 100.01 | Core Finance Module Features | Partial | GL, AR, AP, and bank-reconciliation guidance exist in the assistant knowledge layer; finance-related query skills are present. | No full budgeting/forecasting workflow and no live finance transaction automation. |
| 100.02 | InvoiceNow-Ready Solution Provider Accreditation | Not yet | No accreditation or IMDA listing logic is present in the repo. | Accreditation is an external compliance state and is not verified by the assistant. |
| 100.03 | AI Features | Partial | The assistant itself is AI-driven and answers ERP questions. | Product-level AI feature coverage is incomplete and not tied to a formal product capability layer yet. |
| 100.04 | AI Automated Invoice Processing | Not yet | No invoice OCR / auto-match / approval route implementation is present. | Missing invoice capture pipeline. |
| 100.05 | AI Automated Journal Entry Suggestions | Not yet | No journal suggestion engine or posting recommendation workflow is present. | Missing accounting suggestion logic. |
| 100.06 | AI Anomaly Detection and Fraud Prevention | Not yet | No transaction anomaly or duplicate payment detection pipeline is present. | Missing monitoring and alerting logic. |
| 100.07 | Other AI Features | Not yet | No extra AI feature registry is defined. | Needs explicit product definition. |
| 102.01 | Procurement & Purchasing Features | Partial | Purchase-order browsing and purchasing guidance exist. | No full procurement workflow automation. |
| 102.02 | Procurement & Purchasing Features Detail | Partial | PO / supplier / confirmation data paths exist, and the assistant can guide workflows. | Missing complete end-to-end procurement execution checks. |
| 102.03 | Warehouse & Inventory Features | Partial | Inventory guidance and stock lookup logic exist. | No full warehouse execution layer. |
| 102.04 | Warehouse & Inventory Features Detail | Partial | Reorder and replenishment analysis are partially covered by current skills and query helpers. | Multi-location warehouse operations are not fully modeled. |
| 102.05 | AI Features | Partial | SCM/forecasting related code exists in the repo. | Not yet exposed as a productized AI capability with clear coverage. |
| 102.06 | AI Demand Forecasting | Partial | SCM training/forecasting code exists for scoped analysis. | Needs clearer runtime integration and test coverage. |
| 102.07 | AI Replenishment Recommendations | Partial | Inventory reorder logic is present in the query/skill layer. | Needs stronger explanation and productized output. |
| 102.08 | AI Stock Anomaly Detection | Not yet | No stock anomaly detection pipeline is present. | Missing detection model and alerts. |
| 102.09 | Other AI Features | Not yet | No additional AI feature backlog is defined. | Needs product definition. |

## Suggested Test Questions

Use these questions to verify the assistant:

1. What can you help with?
2. Does the system support InvoiceNow accreditation?
3. Do you have AI invoice OCR?
4. Can you suggest journal entries?
5. Can you detect duplicate payments or fraud?
6. Do you support demand forecasting for inventory?
7. Can you recommend replenishment quantities?
8. Can you explain the finance, purchasing, and inventory coverage in Vietnamese?
