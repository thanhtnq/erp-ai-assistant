export default [
  {
    name: 'get_project_guidance',
    description: 'Return concise project-module guidance for project costing, budgets, claims, and dashboard questions.',
    parameters: {
      type: 'object',
      properties: {
        question: {
          type: 'string',
          description: 'The user question or project topic to summarize.',
        },
      },
      required: [],
    },
    async func(args) {
      const question = String(args.question || args.query || '').trim();
      const topics = [
        'Project Dashboard',
        'Progress Claims',
        'Certified Claims',
        'Project Budgeting',
        'Enterprise Project Accounting',
      ];

      return {
        ok: true,
        skill: 'globe3-project',
        module: 'project',
        question: question || null,
        supported_topics: topics,
        summary: question
          ? `Project guidance for: ${question}`
          : 'Project guidance is available for dashboards, budgets, claims, and project costing.',
        note: 'This is a knowledge-only skill until a dedicated project query tool is added.',
      };
    },
  },
];
