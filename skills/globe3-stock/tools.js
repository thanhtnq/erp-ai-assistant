import { ormFetch } from '../_shared/orm-fetch.js';

// ── Tag mapping — add new document types here as needed ──────────────────────
//
// | tag_table_usage | Display name                      | Notes                         |
// |-----------------|-----------------------------------|-------------------------------|
// | stk_do          | Delivery Order                    | Phiếu xuất kho giao hàng      |
// | stk_doc         | Delivery Order Confirm            | Xác nhận phiếu xuất kho       |
// | stk_grn         | Goods Receipt                     | Phiếu nhập kho                |
// | stk_gvn         | Goods Valuation                   | Định giá hàng tồn             |
// | stk_adji        | Stock Adjustment (Incr Qnty)      | Điều chỉnh tồn kho (tăng)     |
// | stk_adjd        | Stock Adjustment (Decr Qnty)      | Điều chỉnh tồn kho (giảm)     |
// | stk_trnc        | Transfer Confirmation             | Xác nhận chuyển kho           |
// | stk_trnr        | Transfer Request                  | Yêu cầu chuyển kho            |
// | stk_retc        | Sales Return                      | Hàng bán trả lại              |
// | stk_retv        | Return To Vendor                  | Hàng mua trả lại              |
// | stk_asma        | Work Order In Progress            | Lệnh sản xuất đang thực hiện  |
// | stk_asmc        | Work Order Completion             | Hoàn thành lệnh sản xuất      |
// | stk_asmr        | Work Order Request                | Yêu cầu lệnh sản xuất        |
// | stk_reclas      | Item Reclassification With Cost   | Phân loại lại hàng hóa        |
// | stk_mi          | Material Stock In                 | Nhập nguyên vật liệu          |
// | stk_mw          | Material Stock Out                | Xuất nguyên vật liệu          |
// | stk_open        | Stock Opening Balance             | Tồn kho đầu kỳ                |
// | stk_take        | Stock Take                        | Kiểm kê kho                   |
// | stk_unm         | Reverse BOM / Unassemble          | Tháo rời thành phẩm           |
// | (add more)      |                                   |                               |
//
// Update TAG_DESCRIPTION below, then restart the skills server.

const TAG_DESCRIPTION =
  'stk_do=Delivery Order | ' +
  'stk_doc=Delivery Order Confirm | ' +
  'stk_grn=Goods Receipt | ' +
  'stk_gvn=Goods Valuation | ' +
  'stk_adji=Stock Adjustment Increase | ' +
  'stk_adjd=Stock Adjustment Decrease | ' +
  'stk_trnc=Transfer Confirmation | ' +
  'stk_trnr=Transfer Request | ' +
  'stk_retc=Sales Return | ' +
  'stk_retv=Return To Vendor | ' +
  'stk_asma=Work Order In Progress | ' +
  'stk_asmc=Work Order Completion | ' +
  'stk_asmr=Work Order Request | ' +
  'stk_reclas=Item Reclassification | ' +
  'stk_mi=Material Stock In | ' +
  'stk_mw=Material Stock Out | ' +
  'stk_open=Opening Balance | ' +
  'stk_take=Stock Take | ' +
  'stk_unm=Reverse BOM | ' +
  '(more types — see SKILL.md)';

const FILTER_PROPS = {
  tag_table_usage: {
    type: 'string',
    description: `Document type (optional for aggregate, required for list/count): ${TAG_DESCRIPTION}`,
  },
  party_code:       { type: 'string' },
  party_desc:       { type: 'string', description: 'Party name — text search (partial match).' },
  stkcode_code:     { type: 'string', description: 'Stock item code (exact match).' },
  date_from:        { type: 'string', description: 'YYYY-MM-DD or YYYY-MM (whole month).' },
  date_to:          { type: 'string', description: 'Exclusive end date, same format as date_from.' },
  staff_code:       { type: 'string' },
  location_code:    { type: 'string', description: 'Warehouse / location code.' },
  curr_short_forex: { type: 'string', description: 'Currency code, e.g. "SGD", "USD".' },
  tag_void_yn:      { type: 'string', description: '"n"=active (default), "y"=voided.' },
  balance_qnty_uom_stk_code:       { type: 'number' ,description: 'Quantity On Hand'},
};

export default [
  // ── list_stock_documents ───────────────────────────────────────────────────
  {
    name: 'list_stock_documents',
    description:
      `List Globe3 ERP stock/inventory documents with filters, sorting, and pagination. ` +
      `Supports all movement types via tag_table_usage: ${TAG_DESCRIPTION}.`,
    parameters: {
      type: 'object',
      properties: {
        filters: {
          type: 'object',
          properties: FILTER_PROPS,
        },
        sortField: { type: 'string', description: 'Sort by: date_trans, stkcode_code, location_code, balance_qnty_uom_stk_code, date_lastupdate.' },
        sortDir:   { type: 'string', description: 'ASC or DESC (default DESC).' },
        page:      { type: 'number', description: 'Page number (default 1).' },
        pageSize:  { type: 'number', description: 'Results per page (max 20, default 10).' },
      },
      required: ['filters'],
    },
    async func(args) {
      return ormFetch('list', 'stock', {
        masterfn:  args.masterfn,
        companyfn: args.companyfn,
        filters:   args.filters || {},
        sortField: args.sortField || 'date_trans',
        sortDir:   args.sortDir  || 'DESC',
        page:      args.page     || 1,
        pageSize:  Math.min(args.pageSize || 10, 20),
      });
    },
  },

  // ── get_stock_document ─────────────────────────────────────────────────────
  {
    name: 'get_stock_document',
    description:
      'Get a single Globe3 ERP stock document by uniquenum_pri. ' +
      'Works for any movement type — no tag_table_usage needed.',
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'The uniquenum_pri of the document.' },
      },
      required: ['id'],
    },
    async func(args) {
      return ormFetch('findById', 'stock', {
        masterfn:  args.masterfn,
        companyfn: args.companyfn,
        id:        args.id,
      });
    },
  },

  // ── count_stock_documents ──────────────────────────────────────────────────
  {
    name: 'count_stock_documents',
    description:
      `Count Globe3 ERP stock documents matching filters. Use for "how many" questions. ` +
      `Specify tag_table_usage: ${TAG_DESCRIPTION}.`,
    parameters: {
      type: 'object',
      properties: {
        filters: {
          type: 'object',
          properties: FILTER_PROPS,
          required: ['tag_table_usage'],
          description: 'Filter criteria. tag_table_usage is REQUIRED.',
        },
      },
      required: ['filters'],
    },
    async func(args) {
      return ormFetch('count', 'stock', {
        masterfn:  args.masterfn,
        companyfn: args.companyfn,
        filters:   args.filters || {},
      });
    },
  },

  // ── get_quantity_available ─────────────────────────────────────────────────
  {
    name: 'get_quantity_available',
    description:
      'Calculate Quantity Available per item by combining: ' +
      'Qty On Hand (stkm_main_all) + Open PO qty (scm_pur_data, pur_po not closed) ' +
      '- Open SO qty (scm_sal_data, sal_soe not closed). ' +
      'Returns a row per stkcode_code with qty_on_hand, qty_po, qty_so, qty_available.',
    parameters: {
      type: 'object',
      properties: {
        filters: {
          type: 'object',
          description: 'Filter criteria applied to all three data sources.',
          properties: {
            masterfn: {
              type: 'string',
              description: 'Master function / tenant identifier.',
            },
            companyfn: {
              type: 'string',
              description: 'Company code for data isolation.',
            },
            tag_void_yn: {
              type: 'string',
              description: '"n" = active records only (default), "y" = voided.',
            },
            stkcode_code: {
              type: 'string',
              description: 'Filter by specific stock item code (exact match).',
            },
            location_code: {
              type: 'string',
              description: 'Filter On Hand by warehouse / location code.',
            },
            date_from: {
              type: 'string',
              description: 'Filter PO/SO by transaction date from (YYYY-MM-DD).',
            },
            date_to: {
              type: 'string',
              description: 'Filter PO/SO by transaction date to (YYYY-MM-DD).',
            },
          },
        },
        sortField: {
          type: 'string',
          description: 'Sort by: qty_available, qty_on_hand, qty_po, qty_so, stkcode_code (default qty_available).',
        },
        sortDir: {
          type: 'string',
          description: 'ASC or DESC (default DESC).',
        },
        page:     { type: 'number', description: 'Page number (default 1).' },
        pageSize: { type: 'number', description: 'Results per page (max 50, default 20).' },
      },
      required: ['filters'],
    },
    async func(args) {
      return ormFetch('quantity_available', 'stock', {
        masterfn:  args.masterfn,
        companyfn: args.companyfn,
        filters: {
          tag_void_yn:   args.filters?.tag_void_yn  ?? 'n',
          stkcode_code:  args.filters?.stkcode_code,
          location_code: args.filters?.location_code,
          date_from:     args.filters?.date_from,
          date_to:       args.filters?.date_to,
        },
        sortField: args.sortField || 'qty_available',
        sortDir:   args.sortDir   || 'DESC',
        page:      args.page      || 1,
        pageSize:  Math.min(args.pageSize || 20, 50),
      });
    },
  },

  // ── aggregate_stock_documents ──────────────────────────────────────────────
  {
    name: 'aggregate_stock_documents',
    description:
      `Summarize Globe3 ERP stock movements — total quantity, value, count grouped ` +
      `by item, location, party, date, etc. ` +
      `tag_table_usage is OPTIONAL — omit it to query across ALL movement types (e.g. quantity on hand). ` +
      `Specify tag_table_usage only when filtering a specific movement type: ${TAG_DESCRIPTION}. Use for inventory reports and charts.`,
    parameters: {
      type: 'object',
      properties: {
        filters: {
          type: 'object',
          description: 'Filter criteria. tag_table_usage is OPTIONAL — omit for cross-type queries like quantity on hand.',
          properties: FILTER_PROPS,
        },
        func:    { type: 'string', description: 'Aggregate function: sum, count, avg, min, max (default sum).' },
        measure: { type: 'string', description: 'Column to aggregate: balance_qnty_uom_stk_code, amount_local, amount_forex.' },
        groupBy: { type: 'string', description: 'Group by: stkcode_code, location_code, party_code, party_desc, staff_code, curr_short_forex, date_trans. Omit for a single total.' },
        sortDir: { type: 'string', description: 'ASC or DESC (default DESC).' },
        limit:   { type: 'number', description: 'Max groups (default 10, max 50).' },
      },
      required: ['filters'],
    },
    async func(args) {
      return ormFetch('aggregate', 'stock', {
        masterfn:  args.masterfn,
        companyfn: args.companyfn,
        filters:   args.filters || {},
        func:      args.func    || 'sum',
        measure:   args.measure || 'balance_qnty_uom_stk_code',
        groupBy:   args.groupBy || '',
        sortDir:   args.sortDir || 'DESC',
        limit:     Math.min(args.limit || 10, 50),
      });
    },
  },
];
