-- Read-only normalized source for the scheduled Fraud Detection Engine.
-- Review the use of date_post as immutable creation/post timestamp with the ERP owner.
-- Run using a PostgreSQL role allowed to create views, then grant SELECT to the API role.

CREATE OR REPLACE VIEW fraud_transaction_source AS
SELECT
    m.masterfn::text,
    m.companyfn::text,
    ('sales:' || COALESCE(m.cslsegm, m.tag_table_usage, 'unknown') || ':' ||
      COALESCE(NULLIF(m.uniquenum_pri, ''), m.idcode::text))::text AS transaction_id,
    COALESCE(NULLIF(m.userid_cookie, ''), 'system')::text AS user_id,
    COALESCE(m.date_trans, m.date_post)::timestamp AS occurred_at,
    m.date_post::timestamp AS created_at,
    COALESCE(m.nettot_local, m.amount_local, 0)::numeric AS amount,
    COALESCE(m.pct_discount, 0)::numeric AS discount,
    CASE WHEN m.cslsegm = 'sal_cn' THEN 1 ELSE 0 END::integer AS refund_count,
    CASE WHEN m.tag_void_yn = 'y' THEN 1 ELSE 0 END::integer AS void_count,
    GREATEST(COALESCE(m.dnum_revision, 0), 0)::integer AS invoice_modifications,
    jsonb_build_object(
      'module', 'sales', 'document_type', COALESCE(m.cslsegm, m.tag_table_usage),
      'document_no', m.dnum_auto, 'currency', m.curr_short_local,
      'is_void', m.tag_void_yn, 'revision', m.dnum_revision
    ) AS metadata
FROM scm_sal_main m
WHERE m.tag_deleted_yn = 'n'
  AND m.masterfn IS NOT NULL AND m.companyfn IS NOT NULL
  AND m.userid_cookie IS NOT NULL AND m.date_post IS NOT NULL
  AND m.cslsegm IN ('sal_inv', 'sal_cn', 'sal_soc', 'sal_soe')

UNION ALL

SELECT
    m.masterfn::text,
    m.companyfn::text,
    ('purchase:' || COALESCE(m.cslsegm, m.tag_table_usage, 'unknown') || ':' ||
      COALESCE(NULLIF(m.uniquenum_pri, ''), m.idcode::text))::text AS transaction_id,
    COALESCE(NULLIF(m.userid_cookie, ''), 'system')::text AS user_id,
    COALESCE(m.date_trans, m.date_post)::timestamp AS occurred_at,
    m.date_post::timestamp AS created_at,
    COALESCE(m.nettot_local, m.amount_local, 0)::numeric AS amount,
    COALESCE(m.pct_discount, 0)::numeric AS discount,
    CASE WHEN m.cslsegm = 'pur_cn' THEN 1 ELSE 0 END::integer AS refund_count,
    CASE WHEN m.tag_void_yn = 'y' THEN 1 ELSE 0 END::integer AS void_count,
    GREATEST(COALESCE(m.dnum_revision, 0), 0)::integer AS invoice_modifications,
    jsonb_build_object(
      'module', 'purchase', 'document_type', COALESCE(m.cslsegm, m.tag_table_usage),
      'document_no', m.dnum_auto, 'currency', m.curr_short_local,
      'is_void', m.tag_void_yn, 'revision', m.dnum_revision
    ) AS metadata
FROM scm_pur_main m
WHERE m.tag_deleted_yn = 'n'
  AND m.masterfn IS NOT NULL AND m.companyfn IS NOT NULL
  AND m.userid_cookie IS NOT NULL AND m.date_post IS NOT NULL
  AND m.cslsegm IN ('pur_pi', 'pur_cn', 'pur_poc', 'pur_po');

COMMENT ON VIEW fraud_transaction_source IS
  'Tenant-scoped normalized transaction events for rule-based fraud indicators; read only.';

-- Execute separately with the actual least-privilege API role:
-- GRANT SELECT ON fraud_transaction_source TO <erp_ai_readonly_role>;
