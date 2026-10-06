import { redirect } from 'next/navigation';

export default function WorkspaceFailuresRedirect() {
  redirect('/experiments/EXP-0241/failures');
}
