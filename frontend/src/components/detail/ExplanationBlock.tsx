type ExplanationBlockProps = {
  title: string;
  explanation: string;
};

export default function ExplanationBlock({
  title,
  explanation,
}: ExplanationBlockProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-5 shadow-[0_8px_24px_rgba(15,23,42,0.04)]">
      <p className="panel-title">Problema</p>
      <h3 className="mt-2.5 text-lg font-semibold tracking-[-0.02em] text-slate-950">{title}</h3>
      <p className="mt-3.5 text-sm leading-7 text-slate-700">{explanation}</p>
    </div>
  );
}
