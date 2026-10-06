import { redirect } from 'next/navigation';

export default function WorkspaceBoundaryRedirect() {
  redirect('/experiments/EXP-0241/results?tab=boundary');
}
