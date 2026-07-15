Memo Admin — Recommended Columns

Goal: store memos linked to a company and optionally tied to an ERP document/context so admins can trace and search.

Recommended columns (explanation below):

- `id` BIGINT PK AUTO_INCREMENT / IDENTITY
- `companyfn` VARCHAR(64) NOT NULL  -- tenant/company
- `masterfn` VARCHAR(64) NULL       -- client/master identifier
- `created_by` VARCHAR(64) NULL     -- user id who created memo
- `created_at` DATETIME NULL        -- timestamp
- `content` TEXT                    -- full memo text
- `source_table` VARCHAR(64) NULL   -- e.g., scm_sal_main, prj_pbill_main
- `doc_number` VARCHAR(64) NULL     -- user-visible document number (`dnum_docnum` / `dnum_auto`)
- `module` VARCHAR(64) NULL         -- `cslmodule` / high-level module name
- `segment` VARCHAR(64) NULL        -- `cslsegm` or other submodule
- `var_50_001`..`var_50_008` VARCHAR(128) NULL -- reserved fields often used in audit (VAR_50_* mapping)
- `party_code` VARCHAR(64) NULL     -- customer/vendor code if relevant
- `email_add` VARCHAR(255) NULL     -- optional contact email
- `related_audit_id` BIGINT NULL    -- optional FK to `sys_sec_audit.id` if you keep audit rows

Indexes to consider:
- index on `companyfn` (fast tenant listing)
- composite index on (`companyfn`, `doc_number`)
- fulltext index on `content` for searching (MySQL/MSSQL full-text)

Mapping notes: many `sys_sec_audit` inserts use these fields. Storing `module`, `segment`, `doc_number`, and `VAR_50_*` provides enough context to correlate memo entries with audit events or ERP documents.

Storage size: `content` is TEXT; VAR_50 fields set to 128 chars to preserve their typical lengths.

If you prefer a minimal schema, keep only `id`, `companyfn`, `created_by`, `created_at`, `content`, and `doc_number`.
