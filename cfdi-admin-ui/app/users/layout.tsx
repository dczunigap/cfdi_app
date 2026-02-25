import AdminShell from "@/components/admin-shell";

type UsersLayoutProps = {
  children: React.ReactNode;
};

export default async function UsersLayout({ children }: UsersLayoutProps) {
  return <AdminShell>{children}</AdminShell>;
}
