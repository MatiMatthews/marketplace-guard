import type { ReactNode } from "react";

type DashboardShellProps = {
  left: ReactNode;
  center: ReactNode;
  right: ReactNode;
};

export default function DashboardShell({
  left,
  center,
  right,
}: DashboardShellProps) {
  return (
    <div className="grid gap-5 xl:grid-cols-[360px_minmax(460px,1fr)_340px]">
      <div className="min-h-[720px]">{left}</div>
      <div className="min-h-[720px]">{center}</div>
      <div className="min-h-[720px]">{right}</div>
    </div>
  );
}
