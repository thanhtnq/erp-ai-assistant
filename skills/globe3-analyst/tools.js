import { ormFetch } from '../_shared/orm-fetch.js';

export default [
  {
    name: 'run_query',
    description: [
      'Execute a custom PostgreSQL SELECT query for ad-hoc ERP analysis.',
      'Use ONLY when no specific skill tool (list/count/aggregate) covers the question.',
      'The server automatically injects the company filter and caps results at 100 rows.',
      'Rules: SELECT only. Do NOT include masterfn/companyfn in WHERE. Always add LIMIT.',
      'ALLOWED TABLES — use EXACT names only:',
      'scm_sal_main (sales header),',
      'scm_sal_data (sales lines),',
      'scm_pur_main (purchase header),',
      'scm_pur_data (purchase lines),',
      'stkm_main_all (stock/inventory — DO NOT use scm_stk_data or scm_stk_main, those do not exist),',
      'prj_pbill_main (CRM/projects),',
      'memo_long_table (notes).',
      'Using any other table name will throw an error.',
    ].join(' '),
    parameters: {
      type: 'object',
      properties: {
        sql: {
          type: 'string',
          description: [
            'A valid PostgreSQL SELECT query using only the allowed tables listed in the tool description.',
            'For ANY stock or inventory query always use table "stkm_main_all".',
            'NEVER use "scm_stk_data", "scm_stk_main", or any other variant — they do not exist.',
            'Do NOT include masterfn or companyfn in WHERE — injected automatically.',
            'Use exact column names as in SKILL.md. Include LIMIT (max 100).',
          ].join(' '),
        },
        description: {
          type: 'string',
          description: 'One sentence explaining what this query returns (shown to user while loading).',
        },
      },
      required: ['sql', 'description'],
    },

    async func(args) {
      return ormFetch('runQuery', null, {
        sql:       args.sql,
        masterfn:  args.masterfn,
        companyfn: args.companyfn,
      });
    },
  },
];
