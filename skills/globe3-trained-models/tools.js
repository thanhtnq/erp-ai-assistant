import { execFile } from 'child_process';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dir = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dir, '..', '..');
const pythonExe = process.env.SCM_MODEL_PYTHON || join(repoRoot, '.venv', 'Scripts', 'python.exe');

function runPython(args) {
  return new Promise((resolve, reject) => {
    execFile(
      pythonExe,
      args,
      {
        cwd: repoRoot,
        env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
        windowsHide: true,
        timeout: 120000,
        maxBuffer: 1024 * 1024 * 8,
      },
      (error, stdout, stderr) => {
        const text = (stdout || '').trim();
        let payload = null;
        if (text) {
          try {
            payload = JSON.parse(text.split(/\r?\n/).at(-1));
          } catch (parseError) {
            return reject(new Error(`Could not parse SCM model output: ${parseError.message}. stderr=${stderr || ''}`));
          }
        }

        if (error) {
          const message = payload?.error || error.message;
          return reject(new Error(message));
        }

        resolve(payload || { ok: false, error: 'No output from SCM model tool' });
      },
    );
  });
}

export default [
  {
    name: 'run_scm_model',
    description: [
      'Run trained SCM Python models for scoped ERP analytics.',
      'Use for forecast/demand prediction, customer churn/retention risk, product/category demand forecast, and product trend scoring.',
      'forecast and churn use persisted trained .pkl models; demand_forecast uses extracted product artifacts; product_trend uses live sales-history scoring.',
    ].join(' '),
    parameters: {
      type: 'object',
      properties: {
        task: {
          type: 'string',
          description: 'auto, forecast, churn, demand_forecast, or product_trend. Use auto unless the intent is clear.',
        },
        query: {
          type: 'string',
          description: 'The original user question.',
        },
        days: {
          type: 'number',
          description: 'Forecast/history window in days. Default 30 for forecast, 90 is useful for trend.',
        },
        top: {
          type: 'number',
          description: 'Maximum ranked rows to return for churn or product trend. Default 10.',
        },
        group_by: {
          type: 'string',
          description: 'For demand_forecast: product or category. Default category.',
        },
      },
      required: ['query'],
    },

    async func(args) {
      const cliArgs = [
        '-m', 'scm_training.model_tool',
        '--task', args.task || 'auto',
        '--query', args.query || '',
        '--masterfn', args.masterfn,
        '--companyfn', args.companyfn,
        '--days', String(Math.min(Math.max(Number(args.days || 30), 1), 365)),
        '--top', String(Math.min(Math.max(Number(args.top || 10), 1), 50)),
        '--group-by', args.group_by || 'category',
      ];

      return runPython(cliArgs);
    },
  },
];
