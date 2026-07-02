export default [
  {
    name: 'get_hr_guidance',
    description: 'Return concise HR guidance for employee, payroll, leave, attendance, and HR administration questions.',
    parameters: {
      type: 'object',
      properties: {
        question: {
          type: 'string',
          description: 'The user question or HR topic to summarize.',
        },
      },
      required: [],
    },
    async func(args) {
      const question = String(args.question || args.query || '').trim();
      const topics = [
        'Employee Database Management',
        'Benefits Management',
        'Time and Attendance',
        'Payroll Administration',
        'Leave Management',
      ];

      return {
        ok: true,
        skill: 'globe3-hr',
        module: 'hr',
        question: question || null,
        supported_topics: topics,
        summary: question
          ? `HR guidance for: ${question}`
          : 'HR guidance is available for employee records, payroll, leave, and attendance questions.',
        note: 'This is a knowledge-only skill until a dedicated HR query tool is added.',
      };
    },
  },
];
