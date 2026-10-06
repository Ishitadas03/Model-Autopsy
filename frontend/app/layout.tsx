import type { Metadata } from 'next';
import { Manrope, Cabin, Instrument_Serif, Inter } from 'next/font/google';
import './globals.css';
import { MotionProvider } from '@/components/motion/MotionProvider';

const manrope = Manrope({
  subsets: ['latin'],
  weight: ['500', '600', '700'],
  variable: '--font-manrope',
  display: 'swap',
});

const cabin = Cabin({
  subsets: ['latin'],
  weight: ['500', '600'],
  variable: '--font-cabin',
  display: 'swap',
});

const instrumentSerif = Instrument_Serif({
  subsets: ['latin'],
  weight: ['400'],
  style: ['normal', 'italic'],
  variable: '--font-instrument-serif',
  display: 'swap',
});

const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Model Autopsy — Find Out Why AI Fails',
  description:
    'Research-grade ML robustness testing platform. Systematically stress-test machine learning models, measure their robustness, and discover failure conditions.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${manrope.variable} ${cabin.variable} ${instrumentSerif.variable} ${inter.variable}`}
    >
      <body className="min-h-screen bg-bg text-text font-inter selection:bg-accent/30 selection:text-white">
        <MotionProvider>{children}</MotionProvider>
      </body>
    </html>
  );
}
