import { ormFetch } from '../_shared/orm-fetch.js';

export default [
  {
    name: 'run_inventory_query',
    description: [
      'Execute a custom PostgreSQL SELECT query for inventory, stock balance, stock movement, purchase, and supplier delivery analysis.',
      'Use for stock-on-hand, overstock, reorder, slow-moving items, purchase receipt, GRN, and supplier late-delivery questions.',
      'The server validates SELECT-only SQL, injects masterfn/companyfn scope filters, and caps results at 100 rows.',
      'Do not include masterfn or companyfn in the SQL.',
    ].join(' '),
    parameters: {
      type: 'object',
      properties: {
        sql: {
          type: 'string',
          description: [
            'A valid PostgreSQL SELECT query using allowed inventory and purchase tables.',
            'Use table aliases and exact column names from the inventory skill schema.',
            'Always filter voided rows with tag_void_yn = n where the table has tag_void_yn.',
            'Include LIMIT (max 100).',
          ].join(' '),
        },
        description: {
          type: 'string',
          description: 'One sentence explaining what this query returns.',
        },
      },
      required: ['sql', 'description'],
    },

    async func(args) {
      return ormFetch('runQuery', null, {
        sql: args.sql,
        masterfn: args.masterfn,
        companyfn: args.companyfn,
      });
    },
  },
];
