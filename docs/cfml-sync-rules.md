# CFML Sync Rules

The ColdFusion server serves AI assistant files from:

```text
D:\tnosystems\v50foldersetadmin\v50stringg3new\v50master\contentadmin
```

The source-controlled files live in:

```text
D:\Job\WebQuanLy\erp-ai-assistant\cfml-examples
```

## Rule

Edit files in `cfml-examples` first. After any change to CFML UI files, sync them to the ColdFusion `contentadmin` folder before testing in the browser.

Run one sync:

```powershell
.\scripts\sync_cfml_examples.ps1
```

Keep a watcher running while developing:

```powershell
.\scripts\sync_cfml_examples.ps1 -Watch
```

The script copies `.cfm`, `.css`, `.html`, and common image assets while preserving relative paths.

## API Key Rule

CFML files should read `AI_API_URL` and `CHAT_API_KEY` from the repo `.env` file:

```text
D:\Job\WebQuanLy\erp-ai-assistant\.env
```

Fallback defaults are only for local smoke tests:

```text
AI_API_URL=http://localhost:8000
CHAT_API_KEY=erp-ai-secret-key-change-me
```

If the browser shows "Cannot connect to AI server", check both:

1. `http://localhost:8000/health` responds.
2. The rendered CFML page has an `API_KEY` matching `.env`.

## ERP User Context Rule

Do not hard-code the active ERP user or company scope in the assistant UI. The
assistant must use the current ERP cookies:

```cfm
cookie.cookuserloginid
cookie.cookmfnunique
cookie.cookcfnunique
cookie.cooklang
```

The `cfparam` defaults in `ai_assistant.cfm` are only local fallback values for
development or missing-cookie smoke tests. In the ERP session, Lucee/ColdFusion
uses the real cookie values and does not overwrite them with the defaults.

Runtime mapping:

```text
cookuserloginid -> user_id
cookmfnunique   -> company_id and masterfn
cookcfnunique   -> companyfn
cooklang        -> lang
```

This is required so chat history, live ERP data queries, and permissions stay
scoped to the logged-in user and company.
