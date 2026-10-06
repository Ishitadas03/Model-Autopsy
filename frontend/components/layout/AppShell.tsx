'use client';

import React from 'react';
import { TopBar } from './TopBar';
import { Sidebar } from './Sidebar';

interface AppShellProps {
  children: React.ReactNode;
  showSidebar?: boolean;
  experimentId?: string;
}

export function AppShell({
  children,
  showSidebar = false,
  experimentId,
}: AppShellProps) {
  return (
    <div className="relative min-h-screen text-text flex flex-col">
      {/* Top Glass Navigation Bar */}
      <TopBar />

      <div className="relative z-10 flex-1 flex max-w-[1600px] w-full mx-auto">
        {showSidebar && <Sidebar experimentId={experimentId} />}
        <main className="flex-1 flex flex-col min-w-0 p-6 md:p-8 relative">
          {children}
        </main>
      </div>
    </div>
  );
}
