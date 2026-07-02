export function clampInt(value, fallback, min = 1, max = 365) {
  return Math.min(Math.max(Number.parseInt(value ?? fallback, 10) || fallback, min), max);
}

export function requireScope(args) {
  const masterfn = String(args.masterfn || '').trim();
  const companyfn = String(args.companyfn || '').trim();
  if (!masterfn || !companyfn) throw new Error('masterfn and companyfn are required');
  return { masterfn, companyfn };
}

export function analyticsResponse({ analysis, args, rows = [], total = null, warnings = [], assumptions = [], evidence = {} }) {
  const { masterfn, companyfn } = requireScope(args);
  return {
    ok: true,
    analysis,
    scope: { masterfn, companyfn },
    generated_at: new Date().toISOString(),
    period_days: clampInt(args.days, 90),
    total: total ?? rows.length,
    rows,
    warnings,
    assumptions,
    evidence,
    data_quality: {
      has_data: rows.length > 0,
      warning_count: warnings.length,
      status: rows.length ? (warnings.length ? 'partial' : 'complete') : 'no_data',
    },
  };
}

export function riskLevel(score) {
  const n = Number(score || 0);
  if (n >= 80) return 'critical';
  if (n >= 60) return 'high';
  if (n >= 35) return 'medium';
  return 'low';
}
