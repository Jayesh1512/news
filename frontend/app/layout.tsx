import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'News Aggregator',
  description: 'Multi-source news aggregator with RSS and social media feeds',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
