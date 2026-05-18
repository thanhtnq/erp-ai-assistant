---
name: globe3-project-master
description: Project master data — search, browse, and analyze project records
---

# Globe3 Project Module

Use this skill when the user asks about projects, project codes, project lists, or project master data.

## Key Facts

- Description column is `desc_english` (NOT `projcode_desc`)
- Table uses `tag_table_usage = 'projcode'` discriminator
- This is a master/setup table, not transaction data

## Available Tools

- **lookup_project** — Search projects by code, name, or status.
- **get_project** — Retrieve a single project by ID.
- **count_projects** — Count matching projects.

## Filter Fields

- `projcode_code` — project code
- `desc_english` — project name (text search)
- `tag_active_yn` — active status (y/n)

## User-Facing Language

Say "Project" not `set_cnpj_main`. Say "Project Code" not `projcode_code`.
