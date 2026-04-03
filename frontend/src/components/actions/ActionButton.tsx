type ActionButtonProps = {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  tone?: "primary" | "secondary";
};

export default function ActionButton({
  label,
  onClick,
  disabled = false,
  loading = false,
  tone = "secondary",
}: ActionButtonProps) {
  return (
    <button
      className={`w-full rounded-xl px-4 py-3 text-sm font-medium transition duration-150 ${
        tone === "primary"
          ? "bg-[linear-gradient(180deg,#0f172a_0%,#18243c_100%)] text-white shadow-[0_10px_22px_rgba(15,23,42,0.16)] hover:brightness-110"
          : "border border-slate-300 bg-white text-slate-800 shadow-sm hover:bg-slate-50"
      } disabled:cursor-not-allowed disabled:opacity-50`}
      disabled={disabled || loading}
      onClick={onClick}
      type="button"
    >
      {loading ? "Procesando..." : label}
    </button>
  );
}
