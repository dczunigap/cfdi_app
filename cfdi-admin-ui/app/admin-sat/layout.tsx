import AdminShell from "@/components/admin-shell";

type AdminSatLayoutProps = {
  children: React.ReactNode;
};

export default async function AdminSatLayout({
  children,
}: AdminSatLayoutProps) {
  return <AdminShell>{children}</AdminShell>;
}
