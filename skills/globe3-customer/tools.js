import { ormFetch } from '../_shared/orm-fetch.js';

export default [
  {
    name: 'lookup_customer',
    description: 'Look up customer/supplier records by code, name, or status. Use to find customer details before querying their transactions.',
    parameters: {
      type: 'object',
      properties: {
        filters: { type: 'object', properties: { party_code: { type: 'string' }, party_desc: { type: 'string' }, tag_client_vendor: { type: 'string' }, tag_active_yn: { type: 'string' } }, description: 'Filter criteria. Keys: party_code, party_desc (text search, e.g. "GENERAL" matches "GENERAL PARTY"), tag_client_vendor (c=client, v=vendor), tag_active_yn (y/n).' },
        pageSize: { type: 'number', description: 'Max results (default 10, max 20).' }
      },
      required: []
    },
    async func(args) {
      return ormFetch('list', 'customer', {
        filters: args.filters || {},
        sortField: 'party_code',
        sortDir: 'ASC',
        pageSize: Math.min(args.pageSize || 10, 20)
      });
    }
  },
  {
    name: 'get_customer',
    description: 'Get a single customer/supplier record by its unique ID.',
    parameters: {
      type: 'object',
      properties: {
        id: { type: 'string', description: 'The uniquenum_pri of the customer/supplier.' }
      },
      required: ['id']
    },
    async func(args) {
      return ormFetch('findById', 'customer', { id: args.id });
    }
  },
  {
    name: 'aggregate_customers',
    description: 'Summarize customers — count or analyze by type (client/vendor), active status, country, or state. Can aggregate credit limits.',
    parameters: {
      type: 'object',
      properties: {
        func: { type: 'string', description: 'Aggregate function: sum, count, avg, min, max (default count).' },
        measure: { type: 'string', description: 'Column: creditlimit_client. Not needed for count.' },
        groupBy: { type: 'string', description: 'Group by: tag_client_vendor, tag_active_yn, addr_main_nation, addr_main_state.' },
        filters: { type: 'object', description: 'Same filter criteria as lookup_customer.' },
        sortDir: { type: 'string', description: 'ASC or DESC.' },
        limit: { type: 'number', description: 'Max groups (default 10, max 50).' }
      },
      required: []
    },
    async func(args) {
      return ormFetch('aggregate', 'customer', {
        func: args.func || 'count',
        measure: args.measure || '',
        groupBy: args.groupBy || '',
        filters: args.filters || {},
        sortDir: args.sortDir || 'DESC',
        limit: Math.min(args.limit || 10, 50)
      });
    }
  }
];
