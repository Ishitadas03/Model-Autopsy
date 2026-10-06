'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function ExperimentFeaturesRedirect() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id || 'EXP-0241';

  useEffect(() => {
    router.replace(`/experiments/${id}/results?tab=features`);
  }, [id, router]);

  return <div className="min-h-screen bg-bg" />;
}
