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

## API Host and Key Rule

CFML files must use `host_api_url` as the single API host variable. Do not hard-code a
deployment IP such as `124.155.214.47:8297` inside the main synced CFML files.

Local source defaults are only for local smoke tests:

```cfm
host_api_url = "http://localhost:8000";
```

Deployment servers should override this in a deploy-only file named:

```text
contentadmin\inc_ai_host_config.cfm
```

Example production override:

```cfm
<cfscript>
	host_api_url = "http://124.155.214.47:8297";
	// Optional if the deployed API key differs from local:
	// ai_api_key = "production-api-key";
</cfscript>
```

The sync script copies files from `cfml-examples`, but it does not create or require
`inc_ai_host_config.cfm`. Keep that file on the ColdFusion server so future local syncs
do not overwrite the deploy host.

Runtime aliases:

```cfm
analytics_api_url = host_api_url;
ai_api_url = host_api_url;
```

CFML files should keep `CHAT_API_KEY` / `ai_api_key` server-side only. The repo `.env`
still documents local Python settings:

```text
D:\Job\WebQuanLy\erp-ai-assistant\.env
```

Fallback defaults are only for local smoke tests:

```text
host_api_url=http://localhost:8000
CHAT_API_KEY=erp-ai-secret-key-change-me
```

If the browser shows "Cannot connect to AI server", check servers in this order:

1. `#host_api_url#/health` responds for the FastAPI app. For local source this is
   `http://localhost:8000/health`; for the deployed server use the value in
   `inc_ai_host_config.cfm`.
2. `inc_ajax_ai_assistant.cfm?action=skills_healthcheck_local` responds for the local skills demo server on port `3001`.
3. `inc_ajax_ai_assistant.cfm?action=skills_healthcheck_host` responds for the deployed skills server from `SKILLS_SERVER_URL`.
4. The rendered CFML page has an `API_KEY` matching `.env`.

When a healthcheck fails, fix that server first before testing the chat stream.

If a direct request to the CFML page returns `User Login Time-out`, that is an ERP session issue, not an AI server issue. Test the page from an authenticated ERP browser session so the current cookies are available.

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
