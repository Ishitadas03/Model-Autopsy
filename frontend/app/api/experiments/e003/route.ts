import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { E003ComparisonDataSchema } from '@/lib/schemas';

// Disallow dynamic or user-controlled paths. Fixed canonical filenames only.
const ALLOWED_FORMATS = ['json', 'csv', 'markdown'] as const;
type ArtifactFormat = (typeof ALLOWED_FORMATS)[number];

function getCanonicalArtifactPath(format: ArtifactFormat = 'json'): string {
  const filename =
    format === 'csv'
      ? 'aggregate_comparison.csv'
      : format === 'markdown'
      ? 'report.md'
      : 'aggregate_comparison.json';

  // Strategy 1: Relative to process.cwd() when cwd is repo root
  const pRoot = path.resolve(process.cwd(), 'artifacts', 'experiments', 'E003', filename);
  if (fs.existsSync(pRoot)) return pRoot;

  // Strategy 2: Relative to process.cwd() when cwd is frontend/
  const pFrontend = path.resolve(process.cwd(), '..', 'artifacts', 'experiments', 'E003', filename);
  if (fs.existsSync(pFrontend)) return pFrontend;

  // Fallback upwards from __dirname
  let curr = __dirname;
  for (let i = 0; i < 6; i++) {
    const candidate = path.resolve(curr, 'artifacts', 'experiments', 'E003', filename);
    if (fs.existsSync(candidate)) return candidate;
    curr = path.dirname(curr);
  }

  // Return pFrontend as canonical reference if not found
  return pFrontend;
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const rawFormat = searchParams.get('format') || 'json';

    // Strict format validation to block any arbitrary parameter injection
    const format: ArtifactFormat = ALLOWED_FORMATS.includes(rawFormat as ArtifactFormat)
      ? (rawFormat as ArtifactFormat)
      : 'json';

    const artifactPath = getCanonicalArtifactPath(format);

    if (!fs.existsSync(artifactPath)) {
      return NextResponse.json(
        {
          error: 'E003 canonical artifact not found. Please ensure the experiment pipeline has run.',
          experiment_id: 'E003',
        },
        { status: 404 }
      );
    }

    if (format === 'csv') {
      const csvData = fs.readFileSync(artifactPath, 'utf-8');
      return new NextResponse(csvData, {
        status: 200,
        headers: {
          'Content-Type': 'text/csv; charset=utf-8',
          'Content-Disposition': 'inline; filename="aggregate_comparison.csv"',
        },
      });
    }

    if (format === 'markdown') {
      const mdData = fs.readFileSync(artifactPath, 'utf-8');
      return new NextResponse(mdData, {
        status: 200,
        headers: {
          'Content-Type': 'text/markdown; charset=utf-8',
          'Content-Disposition': 'inline; filename="report.md"',
        },
      });
    }

    // Default: JSON
    const rawJsonStr = fs.readFileSync(artifactPath, 'utf-8');
    let parsedJson: unknown;
    try {
      parsedJson = JSON.parse(rawJsonStr);
    } catch {
      return NextResponse.json(
        {
          error: 'E003 canonical artifact contains invalid JSON.',
          experiment_id: 'E003',
        },
        { status: 500 }
      );
    }

    const validationResult = E003ComparisonDataSchema.safeParse(parsedJson);
    if (!validationResult.success) {
      return NextResponse.json(
        {
          error: 'E003 canonical artifact failed schema validation at API boundary.',
          experiment_id: 'E003',
        },
        { status: 500 }
      );
    }

    // Return the validated data
    return NextResponse.json(validationResult.data, {
      status: 200,
      headers: {
        'Cache-Control': 'public, max-age=3600, stale-while-revalidate=86400',
      },
    });
  } catch {
    // Never expose stack trace, system paths, or environment variables
    return NextResponse.json(
      {
        error: 'An internal error occurred while processing the E003 artifact request.',
        experiment_id: 'E003',
      },
      { status: 500 }
    );
  }
}
