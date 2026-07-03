import pg from 'pg';
import { existsSync, readFileSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { analyticsResponse, clampInt, requireScope, riskLevel } from '../_shared/analytics-response.js';

const { Pool } = pg;
const __dir = dirname(fileURLToPath(import.meta.url));

const envPath = join(__dir, '..', '..', '.env');
if (existsSync(envPath)) {
  for (const raw of readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const at = line.indexOf('=');
    const key = line.slice(0, at).trim();
    let value = line.slice(at + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) value = value.slice(1, -1);
    if (!(key in process.env)) process.env[key] = value;
  }
}

let _pool;
function pool() {
  if (!_pool) _pool = new Pool({
    host: process.env.PG_HOST || 'localhost', port: +(process.env.PG_PORT || 5432),
    database: process.env.PG_DBNAME, user: process.env.PG_USER, password: process.env.PG_PASSWORD,
    max: 5, statement_timeout: 15000, connectionTimeoutMillis: 3000,
  });
  return _pool;
}
async function q(sql, params) { return (await pool().query(sql, params)).rows; }

const commonParams = (args, defaultDays = 90) => {
  const { masterfn, companyfn } = requireScope(args);
  return { masterfn, companyfn, days: clampInt(args.days, defaultDays), top: clampInt(args.top, 20, 1, 100) };
};

async function duplicateAp(args) {
  const { masterfn, companyfn, days, top } = commonParams(args, 365);
  const transactionType = args.transaction_type === 'payment' ? 'payment' : 'invoice';
  const sourceType = transactionType === 'payment' ? 'csh_paym' : 'pur_pi';
  const rows = await q(`
    WITH base AS (
      SELECT uniquenum_pri, dnum_auto, party_code, party_desc,
             COALESCE(NULLIF(REGEXP_REPLACE(LOWER(TRIM(COALESCE(dnum_reference,maint_dnum_docnum,dnum_auto,''))), '[^a-z0-9]', '', 'g'),''),'(missing)') normalized_reference,
             COALESCE(maint_curr_short,curr_short_forex,curr_short_local,'') currency,
             ABS(COALESCE(maint_amount_local,amount_local,0))::float amount_local,
             COALESCE(maint_date_trans,date_trans)::date transaction_date,
             COALESCE(dnum_reference,maint_dnum_docnum,dnum_auto,'') reference,
             maint_cslsegm source_type
      FROM gnl_maint_all
      WHERE masterfn=$1 AND companyfn=$2 AND tag_table_usage='paya' AND tag_void_yn='n'
        AND COALESCE(maint_date_trans,date_trans) >= CURRENT_DATE-($3::int*INTERVAL '1 day')
        AND COALESCE(maint_cslsegm,'') = $5
    ), grouped AS (
      SELECT party_code,MAX(party_desc) vendor,normalized_reference,currency,amount_local,
             COUNT(*)::int match_count,TO_CHAR(MIN(transaction_date),'YYYY-MM-DD') first_date,
             TO_CHAR(MAX(transaction_date),'YYYY-MM-DD') last_date,
             ARRAY_AGG(uniquenum_pri ORDER BY transaction_date) source_ids,
             ARRAY_AGG(dnum_auto ORDER BY transaction_date,dnum_auto) document_numbers,
             ARRAY_AGG(reference ORDER BY transaction_date,dnum_auto) references,
             JSON_AGG(JSON_BUILD_OBJECT('dnum_auto',dnum_auto,'date',TO_CHAR(transaction_date,'YYYY-MM-DD'),
               'reference',reference,'source_id',uniquenum_pri) ORDER BY transaction_date,dnum_auto) matched_records
      FROM base WHERE amount_local>0 AND normalized_reference<>'(missing)'
      GROUP BY party_code,normalized_reference,currency,amount_local HAVING COUNT(*)>1
    )
    SELECT *,LEAST(100,60+(match_count-2)*10)::int risk_score,
           'exact_vendor_reference_amount_currency' reason_code
    FROM grouped ORDER BY risk_score DESC,amount_local DESC LIMIT $4`, [masterfn, companyfn, days, top, sourceType]);
  for (const row of rows) row.risk_level = riskLevel(row.risk_score);
  return analyticsResponse({ analysis: 'duplicate_ap_transactions', args: { ...args, masterfn, companyfn, days }, rows,
    assumptions: [`Only non-void ${transactionType} rows (${sourceType}) with a non-empty normalized reference are evaluated.`, 'Flags are duplicate candidates requiring finance review.'],
    evidence: { rule_version: 'duplicate-ap-v2', transaction_type: transactionType, source_type: sourceType, exact_key: ['vendor','normalized_reference','currency','amount_local'] } });
}

async function demandHistory(args) {
  const { masterfn, companyfn, days, top } = commonParams(args, 180);
  const groupByLocation = args.group_by === 'location';
  const rows = await q(`
    SELECT d.stkcode_code sku,MAX(d.stkcode_desc) product,MAX(d.stkcate_desc) category,
           ${groupByLocation ? "COALESCE(NULLIF(d.location_code,''),'(unspecified)')" : "'(all)'"} location,
           DATE_TRUNC('week',m.date_trans)::date week_start,
           SUM(COALESCE(d.qnty_total,0))::float demand_qty,
           SUM(COALESCE(d.amount_local,0))::float revenue_local,
           COUNT(DISTINCT m.uniquenum_pri)::int document_count
    FROM scm_sal_main m JOIN scm_sal_data d ON d.masterfn=m.masterfn AND d.companyfn=m.companyfn
      AND d.uniquenum_pri=m.uniquenum_pri AND d.tag_table_usage=m.tag_table_usage
    WHERE m.masterfn=$1 AND m.companyfn=$2 AND m.tag_void_yn='n' AND d.tag_void_yn='n'
      AND m.tag_table_usage='sal_inv' AND m.date_trans>=CURRENT_DATE-($3::int*INTERVAL '1 day')
    GROUP BY d.stkcode_code,${groupByLocation ? "COALESCE(NULLIF(d.location_code,''),'(unspecified)')," : ''}DATE_TRUNC('week',m.date_trans)
    ORDER BY week_start DESC,demand_qty DESC LIMIT $4`, [masterfn, companyfn, days, top]);
  return analyticsResponse({ analysis: 'sku_demand_history', args: { ...args, masterfn, companyfn, days }, rows,
    warnings: groupByLocation ? [] : ['Location grouping was not requested; rows are company-wide.'],
    assumptions: ['Demand uses non-void Sales Invoice quantities. Returns/cancellations require signed document mapping before netting.'],
    evidence: { source_tables: ['scm_sal_main','scm_sal_data'], document_type: 'sal_inv', grain: groupByLocation ? 'sku_location_week' : 'sku_week' } });
}

async function replenishment(args) {
  const { masterfn, companyfn, days, top } = commonParams(args, 90);
  const serviceFactor = Math.min(Math.max(Number(args.service_factor || 1.65), 0), 3);
  const rows = await q(`
    WITH weekly AS (
      SELECT d.stkcode_code sku,DATE_TRUNC('week',m.date_trans) wk,SUM(COALESCE(d.qnty_total,0))::float qty
      FROM scm_sal_main m JOIN scm_sal_data d ON d.masterfn=m.masterfn AND d.companyfn=m.companyfn
       AND d.uniquenum_pri=m.uniquenum_pri AND d.tag_table_usage=m.tag_table_usage
      WHERE m.masterfn=$1 AND m.companyfn=$2 AND m.tag_void_yn='n' AND d.tag_void_yn='n'
       AND m.tag_table_usage='sal_inv' AND m.date_trans>=CURRENT_DATE-($3::int*INTERVAL '1 day')
      GROUP BY d.stkcode_code,DATE_TRUNC('week',m.date_trans)
    ), demand AS (
      SELECT sku,AVG(qty)::float/7 avg_daily,COALESCE(STDDEV_SAMP(qty),0)::float/SQRT(7) daily_stddev FROM weekly GROUP BY sku
    ), lead AS (
      SELECT stkcode_code sku,AVG(NULLIF(REGEXP_REPLACE(vendor_leadtime_days,'[^0-9.]','','g'),'')::numeric)::float configured_lead_days
      FROM stk_code_data WHERE masterfn=$1 AND companyfn=$2 AND tag_void_yn='n' GROUP BY stkcode_code
    )
    SELECT i.stkcode_code sku,i.stkcode_desc_english product,i.stkcate_desc category,
      COALESCE(i.stkm_qnty_total,0)::float stock_on_hand,ROUND(COALESCE(d.avg_daily,0)::numeric,2)::float avg_daily_demand,
      COALESCE(NULLIF(l.configured_lead_days,0),30)::float lead_days,
      ROUND(($5::float*COALESCE(d.daily_stddev,0)*SQRT(COALESCE(NULLIF(l.configured_lead_days,0),30)))::numeric,2)::float safety_stock,
      ROUND((COALESCE(d.avg_daily,0)*COALESCE(NULLIF(l.configured_lead_days,0),30)+$5::float*COALESCE(d.daily_stddev,0)*SQRT(COALESCE(NULLIF(l.configured_lead_days,0),30)))::numeric,2)::float reorder_point,
      GREATEST(0,CEIL(COALESCE(d.avg_daily,0)*(COALESCE(NULLIF(l.configured_lead_days,0),30)+30)+$5::float*COALESCE(d.daily_stddev,0)*SQRT(COALESCE(NULLIF(l.configured_lead_days,0),30))-COALESCE(i.stkm_qnty_total,0)))::float recommended_qty,
      CASE WHEN COALESCE(d.avg_daily,0)>0 THEN ROUND((COALESCE(i.stkm_qnty_total,0)/d.avg_daily)::numeric,1)::float END days_of_cover,
      CURRENT_DATE suggested_order_date,
      (CURRENT_DATE+CEIL(COALESCE(NULLIF(l.configured_lead_days,0),30))*INTERVAL '1 day')::date expected_receipt_date,
      COALESCE(i.amt_cost_mostrecent,i.amt_cost_stdnormal,0)::float unit_cost,
      ROUND((GREATEST(0,CEIL(COALESCE(d.avg_daily,0)*(COALESCE(NULLIF(l.configured_lead_days,0),30)+30)+$5::float*COALESCE(d.daily_stddev,0)*SQRT(COALESCE(NULLIF(l.configured_lead_days,0),30))-COALESCE(i.stkm_qnty_total,0)))*COALESCE(i.amt_cost_mostrecent,i.amt_cost_stdnormal,0))::numeric,2)::float estimated_order_value,
      LEAST(100,GREATEST(0,ROUND(100-(COALESCE(i.stkm_qnty_total,0)/NULLIF(COALESCE(d.avg_daily,0)*COALESCE(NULLIF(l.configured_lead_days,0),30),0)*100)))::int) stockout_risk_score
    FROM stk_code_main i JOIN demand d ON d.sku=i.stkcode_code LEFT JOIN lead l ON l.sku=i.stkcode_code
    WHERE i.masterfn=$1 AND i.companyfn=$2 AND i.tag_void_yn='n' AND COALESCE(i.tag_active_yn,'y')='y'
    ORDER BY recommended_qty DESC,days_of_cover ASC NULLS LAST LIMIT $4`, [masterfn, companyfn, days, top, serviceFactor]);
  return analyticsResponse({ analysis: 'inventory_replenishment', args: { ...args, masterfn, companyfn, days }, rows,
    warnings: ['Open PO, committed/backorder, MOQ, pack size and carrying-cost inputs are not yet included.', 'Company-level stock is used; authoritative location balance awaits ERP-owner confirmation.'],
    assumptions: [`Service factor=${serviceFactor}.`, 'Missing/zero configured lead time falls back to 30 days.', 'Target coverage is lead time plus 30 days.'],
    evidence: { formula_version: 'replenishment-v1', source_tables: ['scm_sal_main','scm_sal_data','stk_code_main','stk_code_data'] } });
}

async function movementAnomalies(args) {
  const { masterfn, companyfn, days, top } = commonParams(args, 90);
  const rows = await q(`
    WITH adjustments AS (
      SELECT m.uniquenum_pri,m.dnum_auto,m.date_trans,m.userid_cookie,m.location_code,m.tag_table_usage,
             d.stkcode_code sku,d.stkcode_desc product,d.qnty_uomstk::float qty,d.amount_local::float amount_local,
             AVG(ABS(d.qnty_uomstk)) OVER(PARTITION BY d.stkcode_code,m.location_code)::float avg_abs_qty,
             STDDEV_SAMP(ABS(d.qnty_uomstk)) OVER(PARTITION BY d.stkcode_code,m.location_code)::float std_abs_qty
      FROM scm_stk_main m JOIN scm_stk_data d ON d.masterfn=m.masterfn AND d.companyfn=m.companyfn
       AND d.uniquenum_pri=m.uniquenum_pri AND d.tag_table_usage=m.tag_table_usage
      WHERE m.masterfn=$1 AND m.companyfn=$2 AND m.tag_void_yn='n' AND d.tag_void_yn='n'
       AND m.tag_table_usage IN ('stk_adji','stk_adjd','stk_badji','stk_badjd')
       AND m.date_trans>=CURRENT_DATE-($3::int*INTERVAL '1 day')
    )
    SELECT *,CASE WHEN COALESCE(std_abs_qty,0)=0 THEN 50
      ELSE LEAST(100,ROUND(50+25*((ABS(qty)-avg_abs_qty)/NULLIF(std_abs_qty,0)))::int) END risk_score,
      'unusual_adjustment_quantity' reason_code
    FROM adjustments WHERE ABS(qty)>COALESCE(avg_abs_qty,0)+2*COALESCE(std_abs_qty,0)
    ORDER BY risk_score DESC,ABS(qty) DESC LIMIT $4`, [masterfn, companyfn, days, top]);
  for (const row of rows) row.risk_level = riskLevel(row.risk_score);
  return analyticsResponse({ analysis: 'inventory_movement_anomalies', args: { ...args, masterfn, companyfn, days }, rows,
    assumptions: ['V1 evaluates non-void stock-adjustment documents using SKU/location historical quantity outliers.', 'Alerts are investigation indicators, not proof of theft.'],
    evidence: { rule_version: 'stock-adjustment-zscore-v1', threshold: 'mean + 2 standard deviations' } });
}

async function financeAnomalies(args) {
  const { masterfn, companyfn, days, top } = commonParams(args, 365);
  const rows = await q(`
    WITH base AS (
      SELECT uniquenum_pri AS _source_id,dnum_auto AS document_no,party_code,party_desc,maint_cslsegm source_type,
        TO_CHAR(COALESCE(maint_date_trans,date_trans)::date,'YYYY-MM-DD') transaction_date,
        COALESCE(dnum_reference,maint_dnum_docnum,dnum_auto,'') reference,
        ABS(COALESCE(maint_amount_local,amount_local,0))::float amount_local,
        AVG(ABS(COALESCE(maint_amount_local,amount_local,0))) OVER(PARTITION BY party_code,maint_cslsegm)::float vendor_avg,
        STDDEV_SAMP(ABS(COALESCE(maint_amount_local,amount_local,0))) OVER(PARTITION BY party_code,maint_cslsegm)::float vendor_stddev,
        COUNT(*) OVER(PARTITION BY party_code)::int vendor_history_count
      FROM gnl_maint_all WHERE masterfn=$1 AND companyfn=$2 AND tag_table_usage='paya' AND tag_void_yn='n'
        AND COALESCE(maint_date_trans,date_trans)>=CURRENT_DATE-($3::int*INTERVAL '1 day')
    )
    SELECT *,CASE WHEN vendor_history_count<=2 THEN 65
      ELSE LEAST(100,ROUND(50+20*((amount_local-vendor_avg)/NULLIF(vendor_stddev,0)))::int) END risk_score,
      CASE WHEN vendor_history_count<=2 THEN 'new_vendor_high_value' ELSE 'vendor_amount_outlier' END reason_code
    FROM base WHERE amount_local>0 AND ((vendor_stddev>0 AND amount_local>vendor_avg+3*vendor_stddev)
      OR (vendor_history_count<=2 AND amount_local>vendor_avg))
    ORDER BY risk_score DESC,amount_local DESC LIMIT $4`, [masterfn,companyfn,days,top]);
  for (const row of rows) row.risk_level=riskLevel(row.risk_score);
  return analyticsResponse({analysis:'finance_transaction_anomalies',args:{...args,masterfn,companyfn,days},rows,
    assumptions:['Vendor/source amount outliers use a three-standard-deviation threshold.','Indicators require finance review and are not fraud conclusions.'],
    evidence:{rule_version:'ap-outlier-v1',source_table:'gnl_maint_all'}});
}

async function vendorRisk(args) {
  const { masterfn, companyfn, days, top } = commonParams(args, 365);
  const rows=await q(`
    WITH totals AS (
      SELECT party_code,MAX(party_desc) vendor,COUNT(*)::int transaction_count,
        SUM(ABS(COALESCE(maint_amount_local,amount_local,0)))::float total_amount,
        MAX(COALESCE(maint_date_trans,date_trans))::date last_transaction
      FROM gnl_maint_all WHERE masterfn=$1 AND companyfn=$2 AND tag_table_usage='paya' AND tag_void_yn='n'
        AND COALESCE(maint_date_trans,date_trans)>=CURRENT_DATE-($3::int*INTERVAL '1 day')
      GROUP BY party_code
    ), grand AS (SELECT SUM(total_amount) grand_total FROM totals)
    SELECT t.*,CASE WHEN g.grand_total=0 THEN 0 ELSE ROUND((t.total_amount/g.grand_total*100)::numeric,2)::float END payment_share_pct,
      LEAST(100,ROUND(CASE WHEN g.grand_total=0 THEN 0 ELSE t.total_amount/g.grand_total*100 END)::int*2)::int risk_score,
      'payment_concentration' reason_code
    FROM totals t CROSS JOIN grand g ORDER BY payment_share_pct DESC LIMIT $4`,[masterfn,companyfn,days,top]);
  for(const row of rows) row.risk_level=riskLevel(row.risk_score);
  return analyticsResponse({analysis:'vendor_risk_indicators',args:{...args,masterfn,companyfn,days},rows,
    warnings:['Vendor bank, tax/contact sharing and master-change history are unavailable in the confirmed source mapping.'],
    assumptions:['V1 reports payment concentration only; concentration is not evidence of fraud.'],evidence:{rule_version:'vendor-concentration-v1'}});
}

async function advancedForecast(args) {
  const { masterfn, companyfn, days, top }=commonParams(args,180);
  const horizon=clampInt(args.horizon_days,30,1,180);
  const rows=await q(`
    WITH weekly AS (
      SELECT d.stkcode_code sku,MAX(d.stkcode_desc) product,MAX(d.stkcate_desc) category,
        DATE_TRUNC('week',m.date_trans) wk,SUM(COALESCE(d.qnty_total,0))::float qty
      FROM scm_sal_main m JOIN scm_sal_data d ON d.masterfn=m.masterfn AND d.companyfn=m.companyfn
       AND d.uniquenum_pri=m.uniquenum_pri AND d.tag_table_usage=m.tag_table_usage
      WHERE m.masterfn=$1 AND m.companyfn=$2 AND m.tag_void_yn='n' AND d.tag_void_yn='n' AND m.tag_table_usage='sal_inv'
       AND m.date_trans>=CURRENT_DATE-($3::int*INTERVAL '1 day') GROUP BY d.stkcode_code,DATE_TRUNC('week',m.date_trans)
    ), stats AS (
      SELECT sku,MAX(product) product,MAX(category) category,COUNT(*)::int observed_weeks,
       AVG(qty)::float weekly_avg,COALESCE(STDDEV_SAMP(qty),0)::float weekly_stddev,
       REGR_SLOPE(qty,EXTRACT(EPOCH FROM wk)/604800)::float weekly_trend,
       (ARRAY_AGG(qty ORDER BY wk DESC))[1]::float last_week_actual
      FROM weekly GROUP BY sku
    )
    SELECT *,GREATEST(0,ROUND(((weekly_avg+COALESCE(weekly_trend,0))*($5::float/7))::numeric,2))::float forecast_qty,
      GREATEST(0,ROUND(((weekly_avg-1.96*weekly_stddev)*($5::float/7))::numeric,2))::float forecast_lower,
      GREATEST(0,ROUND(((weekly_avg+1.96*weekly_stddev)*($5::float/7))::numeric,2))::float forecast_upper,
      CASE WHEN weekly_avg=0 THEN NULL ELSE ROUND((ABS(last_week_actual-weekly_avg)/weekly_avg*100)::numeric,2)::float END backtest_ape_pct,
      CASE WHEN observed_weeks>=12 THEN 'medium' WHEN observed_weeks>=6 THEN 'low' ELSE 'insufficient' END confidence
    FROM stats ORDER BY forecast_qty DESC LIMIT $4`,[masterfn,companyfn,days,top,horizon]);
  return analyticsResponse({analysis:'advanced_demand_forecast',args:{...args,masterfn,companyfn,days},rows,
    warnings:['Confidence is heuristic until ERP-owner-approved backtesting thresholds are defined.','Location-level fallback awaits authoritative stock/location mapping.'],
    assumptions:[`Forecast horizon=${horizon} days.`,'Trend-adjusted weekly mean with 95% variability interval; not a guaranteed outcome.'],
    evidence:{method_version:'trend-weekly-v1',history_days:days,horizon_days:horizon}});
}

async function expiryRisk(args) {
  const {masterfn,companyfn,days,top}=commonParams(args,90);
  const rows=await q(`
    SELECT stkcode_code sku,MAX(batchnum_code) batch,MAX(location_code) location,MAX(bin_code) bin,
      date_expiry::date expiry_date,MAX(balance_qnty_uom_stk_code)::float balance_qty,
      MAX(value_unitcost_local)::float unit_cost,
      GREATEST(0,MAX(balance_qnty_uom_stk_code))*COALESCE(MAX(value_unitcost_local),0)::float estimated_writeoff_value,
      (date_expiry::date-CURRENT_DATE)::int days_to_expiry,
      CASE WHEN date_expiry<CURRENT_DATE THEN 95 WHEN date_expiry<=CURRENT_DATE+INTERVAL '30 days' THEN 80 ELSE 55 END risk_score,
      'expiry_writeoff_risk' reason_code
    FROM stkm_main_all WHERE masterfn=$1 AND companyfn=$2 AND tag_void_yn='n' AND tag_stkm_valid_yn='y'
      AND date_expiry>CURRENT_DATE-INTERVAL '10 years' AND date_expiry<CURRENT_DATE+INTERVAL '10 years'
      AND date_expiry<=CURRENT_DATE+($3::int*INTERVAL '1 day') AND COALESCE(balance_qnty_uom_stk_code,0)>0
    GROUP BY stkcode_code,date_expiry ORDER BY risk_score DESC,estimated_writeoff_value DESC LIMIT $4`,[masterfn,companyfn,days,top]);
  for(const row of rows) row.risk_level=riskLevel(row.risk_score);
  return analyticsResponse({analysis:'expiry_writeoff_risk',args:{...args,masterfn,companyfn,days},rows,
    warnings:['Sentinel expiry dates outside ±10 years are excluded. Batch balance semantics require cross-client validation.'],
    assumptions:['Positive latest ledger balance is treated as at-risk quantity.'],evidence:{rule_version:'expiry-risk-v1'}});
}

async function shrinkageIndicators(args) {
  const {masterfn,companyfn,days,top}=commonParams(args,90);
  const rows=await q(`
    SELECT d.stkcode_code sku,MAX(d.stkcode_desc) product,m.location_code,
      SUM(CASE WHEN m.tag_table_usage IN ('stk_adjd','stk_badjd') THEN ABS(COALESCE(d.qnty_uomstk,d.qnty_total,0)) ELSE 0 END)::float decrease_adjustment_qty,
      SUM(CASE WHEN m.tag_table_usage IN ('stk_adji','stk_badji') THEN ABS(COALESCE(d.qnty_uomstk,d.qnty_total,0)) ELSE 0 END)::float increase_adjustment_qty,
      COUNT(DISTINCT m.uniquenum_pri)::int adjustment_documents,
      GREATEST(0,SUM(CASE WHEN m.tag_table_usage IN ('stk_adjd','stk_badjd') THEN ABS(COALESCE(d.qnty_uomstk,d.qnty_total,0)) ELSE 0 END)-
        SUM(CASE WHEN m.tag_table_usage IN ('stk_adji','stk_badji') THEN ABS(COALESCE(d.qnty_uomstk,d.qnty_total,0)) ELSE 0 END))::float unexplained_decrease_indicator,
      'net_negative_adjustments' reason_code
    FROM scm_stk_main m JOIN scm_stk_data d ON d.masterfn=m.masterfn AND d.companyfn=m.companyfn
     AND d.uniquenum_pri=m.uniquenum_pri AND d.tag_table_usage=m.tag_table_usage
    WHERE m.masterfn=$1 AND m.companyfn=$2 AND m.tag_void_yn='n' AND d.tag_void_yn='n'
     AND m.tag_table_usage IN ('stk_adji','stk_adjd','stk_badji','stk_badjd')
     AND m.date_trans>=CURRENT_DATE-($3::int*INTERVAL '1 day')
    GROUP BY d.stkcode_code,m.location_code HAVING SUM(CASE WHEN m.tag_table_usage IN ('stk_adjd','stk_badjd') THEN ABS(COALESCE(d.qnty_uomstk,d.qnty_total,0)) ELSE 0 END)>
      SUM(CASE WHEN m.tag_table_usage IN ('stk_adji','stk_badji') THEN ABS(COALESCE(d.qnty_uomstk,d.qnty_total,0)) ELSE 0 END)
    ORDER BY unexplained_decrease_indicator DESC LIMIT $4`,[masterfn,companyfn,days,top]);
  return analyticsResponse({analysis:'stock_shrinkage_indicators',args:{...args,masterfn,companyfn,days},rows,
    warnings:['V1 reconciles stock adjustments only; receipts/issues/transfers require signed stock-equation mapping.'],
    assumptions:['Net negative adjustments are investigation indicators, not proven shrinkage or theft.'],evidence:{rule_version:'net-adjustment-v1'}});
}

async function skuDetail(args) {
  const { masterfn, companyfn } = requireScope(args);
  const skuCode = String(args.sku_code || '').trim();
  if (!skuCode) throw new Error('sku_code is required');
  const rows = await q(`
    SELECT i.stkcode_code sku,i.stkcode_desc_english product,i.stkgrp_desc product_group,
      i.stkcate_desc category,i.brand_desc brand,i.uom_stk_code stock_uom,
      COALESCE(i.stkm_qnty_total,0)::float stock_on_hand,
      COALESCE(i.level_min,0)::float minimum_level,COALESCE(i.level_max,0)::float maximum_level,
      COALESCE(i.level_reorder,0)::float configured_reorder_level,
      COALESCE(i.amt_cost_mostrecent,i.amt_cost_stdnormal,0)::float unit_cost,
      COALESCE(i.amt_price_stdnormal,0)::float standard_price,
      CASE WHEN COALESCE(i.tag_active_yn,'y')='y' THEN 'Active' ELSE 'Inactive' END status,
      CASE WHEN COALESCE(i.tag_batch_ctrl_yn,'n')='y' THEN 'Yes' ELSE 'No' END batch_controlled,
      CASE WHEN COALESCE(i.tag_serial_ctrl_yn,'n')='y' THEN 'Yes' ELSE 'No' END serial_controlled,
      v.vendor_count,ROUND(v.avg_lead_days::numeric,1)::float average_vendor_lead_days,v.location_count
    FROM stk_code_main i LEFT JOIN (
      SELECT stkcode_code,COUNT(DISTINCT party_code)::int vendor_count,
        AVG(NULLIF(REGEXP_REPLACE(vendor_leadtime_days,'[^0-9.]','','g'),'')::numeric)::float avg_lead_days,
        COUNT(DISTINCT location_code)::int location_count
      FROM stk_code_data WHERE masterfn=$1 AND companyfn=$2 AND tag_void_yn='n' GROUP BY stkcode_code
    ) v ON v.stkcode_code=i.stkcode_code
    WHERE i.masterfn=$1 AND i.companyfn=$2 AND i.tag_void_yn='n' AND UPPER(i.stkcode_code)=UPPER($3)
    LIMIT 1`,[masterfn,companyfn,skuCode]);
  return analyticsResponse({analysis:'sku_detail',args:{...args,masterfn,companyfn,days:1},rows,
    warnings: rows.length && Number(rows[0].configured_reorder_level||0)===0 ? ['Configured reorder level is zero; use dynamic replenishment analysis for a calculated reorder point.'] : [],
    assumptions:['Stock on hand is the company-level total from stk_code_main.'],
    evidence:{source_tables:['stk_code_main','stk_code_data'],sku_code:skuCode}});
}

export default [
  { name: 'detect_duplicate_ap_transactions', description: 'Find explainable exact duplicate AP invoice or payment candidates in live scoped ERP data.', parameters: { type:'object', properties:{ days:{type:'number'},top:{type:'number'},transaction_type:{type:'string',description:'invoice (default) or payment'} } }, func: duplicateAp },
  { name: 'get_sku_demand_history', description: 'Return realtime weekly SKU demand history by company or location.', parameters: { type:'object', properties:{ days:{type:'number'},top:{type:'number'},group_by:{type:'string'} } }, func: demandHistory },
  { name: 'recommend_inventory_replenishment', description: 'Calculate explainable dynamic safety stock, reorder point and recommended quantity.', parameters: { type:'object', properties:{ days:{type:'number'},top:{type:'number'},service_factor:{type:'number'} } }, func: replenishment },
  { name: 'detect_inventory_movement_anomalies', description: 'Find unusual stock adjustment quantities by SKU and location.', parameters: { type:'object', properties:{ days:{type:'number'},top:{type:'number'} } }, func: movementAnomalies },
  { name: 'detect_finance_transaction_anomalies', description: 'Find explainable AP vendor/source amount outliers and new-vendor high values.', parameters:{type:'object',properties:{days:{type:'number'},top:{type:'number'}}},func:financeAnomalies },
  { name: 'detect_vendor_risk_indicators', description: 'Rank available vendor risk indicators and disclose unavailable checks.', parameters:{type:'object',properties:{days:{type:'number'},top:{type:'number'}}},func:vendorRisk },
  { name: 'forecast_sku_demand_advanced', description: 'Realtime trend and variability demand forecast with confidence and simple backtest evidence.', parameters:{type:'object',properties:{days:{type:'number'},horizon_days:{type:'number'},top:{type:'number'}}},func:advancedForecast },
  { name: 'detect_expiry_writeoff_risk', description: 'Find batch/SKU stock balances approaching expiry and estimate write-off exposure.', parameters:{type:'object',properties:{days:{type:'number'},top:{type:'number'}}},func:expiryRisk },
  { name: 'detect_stock_shrinkage_indicators', description: 'Find net negative stock-adjustment indicators by SKU and location.', parameters:{type:'object',properties:{days:{type:'number'},top:{type:'number'}}},func:shrinkageIndicators },
  { name: 'get_sku_realtime_detail', description: 'Return current scoped ERP master, stock, price, control and vendor lead-time details for one exact SKU code.', parameters:{type:'object',properties:{sku_code:{type:'string'}},required:['sku_code']},func:skuDetail },
];
