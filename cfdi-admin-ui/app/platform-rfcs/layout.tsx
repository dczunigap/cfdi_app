import AdminShell from "@/components/admin-shell";

type PlatformRfcsLayoutProps = {
  children: React.ReactNode;
};

export default async function PlatformRfcsLayout({
  children,
}: PlatformRfcsLayoutProps) {
  return <AdminShell>{children}</AdminShell>;
}
