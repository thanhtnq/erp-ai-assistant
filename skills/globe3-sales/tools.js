import { ormFetch } from '../_shared/orm-fetch.js';

// ── Tag mapping — add new document types here as needed ──────────────────────
//
// | tag_table_usage | Display name        | Notes                    |
// |-----------------|---------------------|--------------------------|
// | sal_inv         | Sales Invoice       | Hóa đơn bán hàng         |
// | (add more)      |                     |                          |
//
// Update TAG_DESCRIPTION below, then restart the skills server.

const TAG_DESCRIPTION =
  'sal_inv=Sales Invoice | ' +
  'sal_quo=Sales Quotation | ' +
  'sal_soe=Sales Order | ' +
  'sal_soc=Sales Order Confirmation | ' +
  'sal_rta=Retail Sales | ' +
  'sal_dn=Sales Debit Note | ' +
  'sal_cn=Sales Credit Note | ' +
  'sal_fma=Pro Forma Invoice | '
'(more types — see SKILL.md)';

const FILTER_PROPS = {
  tag_table_usage: {
    type: 'string',
    description: `Document type (REQUIRED): ${TAG_DESCRIPTION}`,
  },
  party_code: { type: 'string' },
  party_desc: { type: 'string', description: 'Text search (partial match).' },
  date_from: { type: 'string', description: 'YYYY-MM-DD or YYYY-MM (whole month).' },
  date_to: { type: 'string', description: 'Exclusive end date, same format as date_from.' },
  staff_code: { type: 'string' },
  dnum_auto: { type: 'string', description: 'Document number (partial match).' },
  dnum_reference: { type: 'string' },
  location_code: { type: 'string' },
  curr_short_forex: { type: 'string', description: 'Currency code, e.g. "SGD", "USD".' },
  tag_void_yn: { type: 'string', description: '"n"=active (default), "y"=voided.' },
  amount_min: { type: 'number' },
  amount_max: { type: 'number' },
};

export default [
  // ── list_sales_documents ───────────────────────────────────────────────────
  {
    name: 'list_sales_documents',
    description:
      `List Globe3 ERP sales documents with filters, sorting, and pagination. ` +
      `Use when the user asks to list/show/find documents, document numbers, rows, or details. ` +
      `If the user says "do not count", "don't count", "not count", or "I don't want count", prefer this tool. ` +
      `Supports all document types via tag_table_usage: ${TAG_DESCRIPTION}.`,
    parameters: {
      type: 'object',
      properties: {
        filters: {
          type: 'object',
          properties: FILTER_PROPS,
          required: ['tag_table_usage'],
          description: 'Filter criteria. tag_table_usage is REQUIRED.',
        },
        sortField: { type: 'string', description: 'Sort by: date_trans, dnum_auto, party_code, amount_forex, amount_local, date_lastupdate.' },
        sortDir: { type: 'string', description: 'ASC or DESC (default DESC).' },
        page: { type: 'number', description: 'Page number (default 1).' },
        pageSize: { type: 'number', description: 'Results per page (max 20, default 10).' },
      },
      required: ['filters'],
    },
    async func(args) {
      return ormFetch('list', 'sales', {
        masterfn: args.masterfn,
        companyfn: args.companyfn,
        filters: args.filters || {},
        sortField: args.sortField || 'date_trans',
        sortDir: args.sortDir || 'DESC',
        page: args.page || 1,
        pageSize: Math.min(args.pageSize || 10, 20),
      });
    },
  },

  // ── get_sales_document ─────────────────────────────────────────────────────
  {
    name: 'get_sales_document',
    description:
      'Get a single Globe3 ERP sales document by uniquenum_pri. ' +
      'Works for any document type — no tag_table_usage needed.',
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'The uniquenum_pri of the document.' },
      },
      required: ['id'],
    },
    async func(args) {
      return ormFetch('findById', 'sales', {
        masterfn: args.masterfn,
        companyfn: args.companyfn,
        id: args.id,
      });
    },
  },

  // ── count_sales_documents ──────────────────────────────────────────────────
  {
    name: 'count_sales_documents',
    description:
      `Count Globe3 ERP sales documents matching filters. Use only for pure "how many" or count questions. ` +
      `Do not use when the user asks to list/show document numbers, rows, or says not to count. ` +
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
      return ormFetch('count', 'sales', {
        masterfn: args.masterfn,
        companyfn: args.companyfn,
        filters: args.filters || {},
      });
    },
  },

  // ── aggregate_sales_documents ──────────────────────────────────────────────
  {
    name: 'aggregate_sales_documents',
    description:
      `Summarize Globe3 ERP sales documents — total, average, min, max, or count grouped ` +
      `by customer, staff, location, currency, date, etc. ` +
      `Specify tag_table_usage: ${TAG_DESCRIPTION}. Use for reports and charts.`,
    parameters: {
      type: 'object',
      properties: {
        filters: {
          type: 'object',
          properties: FILTER_PROPS,
          required: ['tag_table_usage'],
          description: 'Filter criteria. tag_table_usage is REQUIRED.',
        },
        func: { type: 'string', description: 'Aggregate function: sum, count, avg, min, max (default sum).' },
        measure: { type: 'string', description: 'Column to aggregate: amount_forex or amount_local (default amount_local). Omit for count.' },
        groupBy: { type: 'string', description: 'Group by: party_code, party_desc, staff_code, staff_desc, location_code, deptunit_code, curr_short_forex, date_trans, creditterm_desc. Omit for a single total.' },
        sortDir: { type: 'string', description: 'ASC or DESC (default DESC).' },
        limit: { type: 'number', description: 'Max groups (default 10, max 50).' },
      },
      required: ['filters'],
    },
    async func(args) {
      return ormFetch('aggregate', 'sales', {
        masterfn: args.masterfn,
        companyfn: args.companyfn,
        filters: args.filters || {},
        func: args.func || 'sum',
        measure: args.measure || 'amount_local',
        groupBy: args.groupBy || '',
        sortDir: args.sortDir || 'DESC',
        limit: Math.min(args.limit || 10, 50),
      });
    },
  },
];
