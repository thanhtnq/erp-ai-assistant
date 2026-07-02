export default [
  {
    name: 'get_finance_guidance',
    description: 'Return concise finance-module guidance for GL, AR/AP, bank reconciliation, and financial reporting questions.',
    parameters: {
      type: 'object',
      properties: {
        question: {
          type: 'string',
          description: 'The user question or topic to summarize.',
        },
      },
      required: [],
    },
    async func(args) {
      const question = String(args.question || args.query || '').trim();
      const topics = [
        'General Ledger',
        'Accounts Receivable',
        'Accounts Payable',
        'Bank Reconciliation',
        'Financial Reporting',
      ];

      return {
        ok: true,
        skill: 'globe3-finance',
        module: 'finance',
        question: question || null,
        supported_topics: topics,
        summary: question
          ? `Finance guidance for: ${question}`
          : 'Finance guidance is available for GL, AR/AP, bank reconciliation, and financial reporting.',
        note: 'This is a knowledge-only skill until a dedicated finance query tool is added.',
      };
    },
  },
];
