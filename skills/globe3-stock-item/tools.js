import { ormFetch } from '../_shared/orm-fetch.js';
export default [
  { name: 'lookup_stock_item', description: 'Search stock items by code, name, or status. Use to find item details.', parameters: { type: 'object', properties: { filters: { type: 'object', properties: { stkcode_code: { type: 'string' }, stkcode_desc_english: { type: 'string' }, tag_active_yn: { type: 'string' }, tag_assembly_yn: { type: 'string' }, tag_taxable_yn: { type: 'string' } }, description: 'Keys: stkcode_code (item code), stkcode_desc_english (text search, e.g. "cable" matches "Cable Assembly"), tag_active_yn (y/n), tag_assembly_yn, tag_taxable_yn.' }, sortField: { type: 'string', description: 'Sort by: stkcode_code, stkcode_desc_english, date_lastupdate.' }, sortDir: { type: 'string', description: 'ASC or DESC.' }, pageSize: { type: 'number', description: 'Max 20.' } }, required: [] },
    async func(args) { return ormFetch('list', 'stock_item', { filters: args.filters || {}, sortField: args.sortField || 'stkcode_code', sortDir: args.sortDir || 'ASC', pageSize: Math.min(args.pageSize || 10, 20) }); } },
  { name: 'get_stock_item', description: 'Get a single stock item by its unique ID.', parameters: { type: 'object', properties: { id: { type: 'string', description: 'uniquenum_pri.' } }, required: ['id'] },
    async func(args) { return ormFetch('findById', 'stock_item', { id: args.id }); } },
  { name: 'count_stock_items', description: 'Count stock items matching filters.', parameters: { type: 'object', properties: { filters: { type: 'object', description: 'Same as lookup_stock_item.' } }, required: [] },
    async func(args) { return ormFetch('count', 'stock_item', { filters: args.filters || {} }); } }
];
