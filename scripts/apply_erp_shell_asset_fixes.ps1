param(
  [string]$ErpRoot = "D:\tnosystems\v50foldersetadmin\v50stringg3new"
)

$ErrorActionPreference = "Stop"

$jqueryCarousel = Join-Path $ErpRoot "folder_jquery\jquery.jcarousel.min.js"
$fontAwesome    = Join-Path $ErpRoot "folder_style\font-awesome.min.css"
$styleFiles     = @(
  (Join-Path $ErpRoot "folder_style_i\style_appmenu.css"),
  (Join-Path $ErpRoot "folder_style_j\style_appmenu.css")
)

if (Test-Path -LiteralPath $jqueryCarousel) {
  $text = Get-Content -LiteralPath $jqueryCarousel -Raw
  if ($text -notmatch "ERP compatibility shim for jQuery 3") {
    Copy-Item -LiteralPath $jqueryCarousel -Destination ($jqueryCarousel + ".bak_codex") -Force
    $shim = "/* ERP compatibility shim for jQuery 3+. */`r`n" +
      "(function(w){var jq=w.jQuery;if(!jq)return;if(!jq.fn.size){jq.fn.size=function(){return this.length;};}if(!jq.browser){var ua=(w.navigator&&w.navigator.userAgent||'').toLowerCase();jq.browser={safari:/safari/.test(ua)&&!/chrome|chromium|android/.test(ua),webkit:/webkit/.test(ua),mozilla:/mozilla/.test(ua)&&!/webkit/.test(ua),msie:/msie|trident/.test(ua)};}})(window);`r`n"
    Set-Content -LiteralPath $jqueryCarousel -Value ($shim + $text) -Encoding UTF8
    Write-Host "Patched jCarousel compatibility shim"
  } else {
    Write-Host "jCarousel compatibility shim already present"
  }
}

if (-not (Test-Path -LiteralPath $fontAwesome)) {
  $faCss = @'
/* Local Font Awesome fallback for ERP shell.
   Prevents 404 when legacy pages request folder_style/font-awesome.min.css.
   Replace with the full Font Awesome package if icon fonts are required. */
.fa,.fas,.far,.fab{display:inline-block;font-style:normal;font-variant:normal;text-rendering:auto;line-height:1}
.fa:before,.fas:before,.far:before,.fab:before{font-family:Arial,sans-serif}
.fa-home:before{content:"⌂"}.fa-bars:before{content:"☰"}.fa-search:before{content:"⌕"}.fa-folder:before{content:"□"}.fa-user:before{content:"●"}.fa-cog:before,.fa-gear:before{content:"⚙"}.fa-eye:before{content:"◉"}.fa-filter:before{content:"▽"}.fa-times:before,.fa-close:before{content:"×"}.fa-sign-out:before{content:"↪"}.fa-bookmark:before{content:"▮"}.fa-link:before{content:"🔗"}
'@
  Set-Content -LiteralPath $fontAwesome -Value $faCss -Encoding UTF8
  Write-Host "Created font-awesome fallback"
} else {
  Write-Host "font-awesome file already exists"
}

foreach ($file in $styleFiles) {
  if (-not (Test-Path -LiteralPath $file)) { continue }
  $text = Get-Content -LiteralPath $file -Raw
  $newText = $text -replace "\.\./\.\./folder_graphics/#fldrgraphic#/Grad_TabGrey\.gif", "../folder_graphics/graphics_main_all/Grad_TabGrey.gif"
  if ($newText -ne $text) {
    Copy-Item -LiteralPath $file -Destination ($file + ".bak_codex") -Force
    Set-Content -LiteralPath $file -Value $newText -Encoding UTF8
    Write-Host "Patched graphics path in $file"
  } else {
    Write-Host "No graphics path change needed in $file"
  }
}
