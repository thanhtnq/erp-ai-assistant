import { ormFetch } from '../_shared/orm-fetch.js';

export default [
  {
    name: 'list_so_confirmations',
    description: 'List SO confirmations (confirmed sales orders) with optional filters, sorting, and pagination.',
    parameters: {
      type: 'object',
      properties: {
        filters: { type: 'object', properties: { party_code: { type: 'string' }, party_desc: { type: 'string' }, date_trans: { type: 'string' }, date_from: { type: 'string', description: 'Start date filter (YYYY-MM-DD or YYYY-MM for whole month, e.g. "2026-04" for April 2026). Use for "this month", "last month", date range queries.' }, date_to: { type: 'string', description: 'End date filter (exclusive). Same format as date_from.' }, staff_code: { type: 'string' }, dnum_auto: { type: 'string' }, dnum_reference: { type: 'string' }, curr_short_forex: { type: 'string' }, tag_void_yn: { type: 'string' }, amount_min: { type: 'number' }, amount_max: { type: 'number' } }, description: 'Filter criteria. Keys: party_code, party_desc (text search), date_trans, staff_code, dnum_auto, dnum_reference, curr_short_forex, tag_void_yn. amount_min (number, exclude zero/low amounts), amount_max (number, cap amounts).' },
        sortField: { type: 'string', description: 'Sort by: date_trans, dnum_auto, party_code, amount_forex, date_lastupdate.' },
        sortDir: { type: 'string', description: 'ASC or DESC (default DESC).' },
        page: { type: 'number', description: 'Page number (default 1).' },
        pageSize: { type: 'number', description: 'Results per page (max 20, default 10).' }
      },
      required: []
    },
    async func(args) {
      return ormFetch('list', 'sales_confirmation', {
        filters: args.filters || {},
        sortField: args.sortField || 'date_trans',
        sortDir: args.sortDir || 'DESC',
        page: args.page || 1,
        pageSize: Math.min(args.pageSize || 10, 20)
      });
    }
  },
  {
    name: 'get_so_confirmation',
    description: 'Get a single SO confirmation by its unique ID.',
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'The uniquenum_pri of the SO confirmation.' }
      },
      required: ['id']
    },
    async func(args) {
      return ormFetch('findById', 'sales_confirmation', { id: args.id });
    }
  },
  {
    name: 'count_so_confirmations',
    description: 'Count SO confirmations matching filters.',
    parameters: {
      type: 'object',
      properties: {
        filters: { type: 'object', description: 'Same filter criteria as list_so_confirmations.' }
      },
      required: []
    },
    async func(args) {
      return ormFetch('count', 'sales_confirmation', { filters: args.filters || {} });
    }
  },
  {
    name: 'aggregate_so_confirmations',
    description: 'Summarize SO confirmations — total, average, min, max, or count grouped by customer, staff, currency, or date.',
    parameters: {
      type: 'object',
      properties: {
        func: { type: 'string', description: 'Aggregate function: sum, count, avg, min, max.' },
        measure: { type: 'string', description: 'Column: amount_forex or amount_local.' },
        groupBy: { type: 'string', description: 'Group by: party_code, party_desc, staff_code, staff_desc, curr_short_forex, date_trans.' },
        filters: { type: 'object', description: 'Same filter criteria as list_so_confirmations.' },
        sortDir: { type: 'string', description: 'ASC or DESC.' },
        limit: { type: 'number', description: 'Max groups (default 10, max 50).' }
      },
      required: []
    },
    async func(args) {
      return ormFetch('aggregate', 'sales_confirmation', {
        func: args.func || 'sum',
        measure: args.measure || 'amount_local',
        groupBy: args.groupBy || '',
        filters: args.filters || {},
        sortDir: args.sortDir || 'DESC',
        limit: Math.min(args.limit || 10, 50)
      });
    }
  }
];
