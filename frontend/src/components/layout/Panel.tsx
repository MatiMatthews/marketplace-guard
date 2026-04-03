import type { ReactNode } from "react";

type PanelProps = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
};

export default function Panel({
  title,
  subtitle,
  actions,
  children,
  className = "",
}: PanelProps) {
  return (
    <section
      className={`section-card overflow-hidden rounded-[28px] border border-slate-200/80 bg-white ${className}`}
    >
      <header className="flex items-start justify-between gap-4 border-b border-slate-200/80 bg-slate-50/70 px-5 py-4">
        <div className="min-w-0">
          <p className="panel-title">{title}</p>
          {subtitle ? <p className="panel-subtitle mt-1.5">{subtitle}</p> : null}
        </div>
        {actions}
      </header>
      <div className="px-5 py-5">{children}</div>
    </section>
  );
}
