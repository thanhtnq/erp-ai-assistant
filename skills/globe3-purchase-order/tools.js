import { ormFetch } from '../_shared/orm-fetch.js';

export default [
  {
    name: 'list_purchase_orders',
    description: 'List purchase orders with optional filters, sorting, and pagination. Returns document number, date, supplier, amount, currency.',
    parameters: {
      type: 'object',
      properties: {
        filters: { type: 'object', properties: { party_code: { type: 'string' }, party_desc: { type: 'string' }, date_trans: { type: 'string' }, date_from: { type: 'string', description: 'Start date filter (YYYY-MM-DD or YYYY-MM for whole month, e.g. "2026-04" for April 2026). Use for "this month", "last month", date range queries.' }, date_to: { type: 'string', description: 'End date filter (exclusive). Same format as date_from.' }, dnum_auto: { type: 'string' }, dnum_docnum: { type: 'string' }, dnum_reference: { type: 'string' }, location_code: { type: 'string' }, curr_short_forex: { type: 'string' }, tag_void_yn: { type: 'string' }, amount_min: { type: 'number' }, amount_max: { type: 'number' } }, description: 'Filter criteria. Keys: party_code, party_desc (text search, e.g. "HD Metal" matches "HD Metal Pte Ltd"), date_trans, dnum_auto, dnum_docnum, dnum_reference, location_code, location_desc, curr_short_forex, tag_void_yn. amount_min (number, exclude zero/low amounts), amount_max (number, cap amounts).' },
        sortField: { type: 'string', description: 'Sort by: date_trans, dnum_auto, party_code, party_desc, amount_forex, amount_local.' },
        sortDir: { type: 'string', description: 'ASC or DESC (default DESC).' },
        page: { type: 'number', description: 'Page number (default 1).' },
        pageSize: { type: 'number', description: 'Results per page (max 20, default 10).' }
      },
      required: []
    },
    async func(args) {
      return ormFetch('list', 'purchase_order', {
        filters: args.filters || {},
        sortField: args.sortField || 'date_trans',
        sortDir: args.sortDir || 'DESC',
        page: args.page || 1,
        pageSize: Math.min(args.pageSize || 10, 20)
      });
    }
  },
  {
    name: 'get_purchase_order',
    description: 'Get a single purchase order by its unique ID (uniquenum_pri).',
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'The uniquenum_pri of the purchase order.' }
      },
      required: ['id']
    },
    async func(args) {
      return ormFetch('findById', 'purchase_order', { id: args.id });
    }
  },
  {
    name: 'count_purchase_orders',
    description: 'Count purchase orders matching filters without returning row data.',
    parameters: {
      type: 'object',
      properties: {
        filters: { type: 'object', description: 'Same filter criteria as list_purchase_orders.' }
      },
      required: []
    },
    async func(args) {
      return ormFetch('count', 'purchase_order', { filters: args.filters || {} });
    }
  },
  {
    name: 'aggregate_purchase_orders',
    description: 'Summarize purchase orders — total, average, min, max, or count grouped by supplier, staff, location, currency, or date. Use for procurement analysis.',
    parameters: {
      type: 'object',
      properties: {
        func: { type: 'string', description: 'Aggregate function: sum, count, avg, min, max (default sum).' },
        measure: { type: 'string', description: 'Column: amount_forex, amount_local, subtot_forex, subtot_local, nettot_forex, nettot_local.' },
        groupBy: { type: 'string', description: 'Group by: party_code, party_desc, staff_code, staff_desc, location_code, location_desc, curr_short_forex, date_trans.' },
        filters: { type: 'object', description: 'Same filter criteria as list_purchase_orders.' },
        sortDir: { type: 'string', description: 'ASC or DESC.' },
        limit: { type: 'number', description: 'Max groups (default 10, max 50).' }
      },
      required: []
    },
    async func(args) {
      return ormFetch('aggregate', 'purchase_order', {
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
