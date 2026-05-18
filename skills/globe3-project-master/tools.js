import { ormFetch } from '../_shared/orm-fetch.js';
export default [
  { name: 'lookup_project', description: 'Search projects by code, name, or status.', parameters: { type: 'object', properties: { filters: { type: 'object', properties: { projcode_code: { type: 'string' }, desc_english: { type: 'string' }, tag_active_yn: { type: 'string' } }, description: 'Keys: projcode_code (project code), desc_english (text search, e.g. "warehouse" matches "Warehouse Extension"), tag_active_yn (y/n).' }, sortField: { type: 'string', description: 'Sort by: projcode_code, desc_english, date_lastupdate.' }, sortDir: { type: 'string', description: 'ASC or DESC.' }, pageSize: { type: 'number', description: 'Max 20.' } }, required: [] },
    async func(args) { return ormFetch('list', 'project', { filters: args.filters || {}, sortField: args.sortField || 'projcode_code', sortDir: args.sortDir || 'ASC', pageSize: Math.min(args.pageSize || 10, 20) }); } },
  { name: 'get_project', description: 'Get a single project by its unique ID.', parameters: { type: 'object', properties: { id: { type: 'string', description: 'uniquenum_pri.' } }, required: ['id'] },
    async func(args) { return ormFetch('findById', 'project', { id: args.id }); } },
  { name: 'count_projects', description: 'Count projects matching filters.', parameters: { type: 'object', properties: { filters: { type: 'object', description: 'Same as lookup_project.' } }, required: [] },
    async func(args) { return ormFetch('count', 'project', { filters: args.filters || {} }); } }
];
