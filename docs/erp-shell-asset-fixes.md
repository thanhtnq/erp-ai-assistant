# ERP Shell Asset Fixes

These fixes apply to the Lucee-served ERP shell outside this repo:

```text
D:\tnosystems\v50foldersetadmin\v50stringg3new
```

Run:

```powershell
.\scripts\apply_erp_shell_asset_fixes.ps1
```

What it fixes:

- Adds a jQuery 3 compatibility shim to `folder_jquery/jquery.jcarousel.min.js`.
  - Restores `$.fn.size()` used by old jCarousel `0.2.7`.
  - Adds a small `$.browser` fallback used by the same plugin.
- Creates `folder_style/font-awesome.min.css` fallback so legacy pages stop returning 404.
- Fixes `style_appmenu.css` in `folder_style_i` and `folder_style_j` so `Grad_TabGrey.gif` points to the real `folder_graphics/graphics_main_all` location.

Backups are written next to modified files as `.bak_codex` before patching.
