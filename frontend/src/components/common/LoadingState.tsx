type LoadingStateProps = {
  label?: string;
};

export default function LoadingState({
  label = "Cargando datos...",
}: LoadingStateProps) {
  return (
    <div className="flex min-h-[180px] items-center justify-center rounded-xl border border-dashed border-line bg-slate-50 p-6 text-sm text-muted">
      {label}
    </div>
  );
}
