export default [
  {
    name: 'get_product_overview',
    description: 'Return a concise Globe3 ERP product and company overview, including modules, services, and contact points.',
    parameters: {
      type: 'object',
      properties: {
        question: {
          type: 'string',
          description: 'Optional question or topic to tailor the overview.',
        },
      },
      required: [],
    },
    async func(args) {
      const question = String(args.question || args.query || '').trim();

      return {
        ok: true,
        skill: 'globe3-product-info',
        module: 'product-info',
        question: question || null,
        company: 'TNO Systems Pte Ltd',
        product: 'Globe3 ERP',
        summary: question
          ? `Globe3 ERP overview for: ${question}`
          : 'Globe3 ERP is a cloud-based, multi-module ERP for finance, inventory, SCM, project, CRM, and HR.',
        highlights: [
          'Cloud-based and web-based ERP',
          'Multi-company and multi-language support',
          'Finance, inventory, SCM, project, CRM, and HR modules',
          'Support for customization, implementation, and maintenance',
        ],
        note: 'This skill returns product knowledge and should not be used for live ERP data queries.',
      };
    },
  },
];
