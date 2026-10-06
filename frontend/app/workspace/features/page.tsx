import { redirect } from 'next/navigation';

export default function WorkspaceFeaturesRedirect() {
  redirect('/experiments/EXP-0241/results?tab=features');
}
