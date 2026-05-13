import { ormFetch } from '../_shared/orm-fetch.js';

export default [
  {
    name: 'run_query',
    description: [
      'Execute a custom PostgreSQL SELECT query for ad-hoc ERP analysis.',
      'Use ONLY when no specific skill tool (list/count/aggregate) covers the question.',
      'The server automatically injects the company filter and caps results at 100 rows.',
      'Rules: SELECT only. Do NOT include masterfn in WHERE. Always add LIMIT.',
    ].join(' '),
    parameters: {
      type: 'object',
      properties: {
        sql: {
          type: 'string',
          description: [
            'A valid PostgreSQL SELECT query using the schema from SKILL.md.',
            'Do not include masterfn/company filter — it is injected automatically.',
            'Use parameterized column names exactly as defined in the schema.',
            'Include LIMIT (max 100).',
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
      // modelName is unused for runQuery — safety layer defaults company_field to 'masterfn'
      return ormFetch('runQuery', null, {
        sql: args.sql,
        masterfn: args.masterfn,
        companyfn: args.companyfn,
      });
    },
  },
];
