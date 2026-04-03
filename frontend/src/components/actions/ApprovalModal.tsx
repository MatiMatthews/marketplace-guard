type ApprovalModalProps = {
  open: boolean;
  onConfirm: () => void;
  onClose: () => void;
  loading?: boolean;
};

export default function ApprovalModal({
  open,
  onConfirm,
  onClose,
  loading = false,
}: ApprovalModalProps) {
  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 p-4">
      <div className="w-full max-w-md rounded-2xl border border-line bg-white p-6 shadow-xl">
        <p className="panel-title">Approval requerido</p>
        <h3 className="mt-2 text-lg font-semibold text-ink">Confirmar bloqueo</h3>
        <p className="mt-3 text-sm leading-6 text-muted">
          El backend exige approval para ejecutar el bloqueo simulado. Si confirmas,
          se vuelve a intentar la acción con autorización.
        </p>
        <div className="mt-6 flex gap-3">
          <button
            className="flex-1 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
            onClick={onClose}
            type="button"
          >
            Cancelar
          </button>
          <button
            className="flex-1 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={loading}
            onClick={onConfirm}
            type="button"
          >
            {loading ? "Confirmando..." : "Aprobar y ejecutar"}
          </button>
        </div>
      </div>
    </div>
  );
}
