import { MainLayout } from '@/components/layout/main-layout';

export default function CleaningLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <MainLayout>{children}</MainLayout>;
}