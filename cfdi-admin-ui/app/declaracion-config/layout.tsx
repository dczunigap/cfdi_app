import AdminShell from "@/components/admin-shell";

type DeclaracionConfigLayoutProps = {
  children: React.ReactNode;
};

export default function DeclaracionConfigLayout({
  children,
}: DeclaracionConfigLayoutProps) {
  return <AdminShell>{children}</AdminShell>;
}
