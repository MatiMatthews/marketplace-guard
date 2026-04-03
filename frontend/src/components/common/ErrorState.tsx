type ErrorStateProps = {
  message: string;
  onRetry?: () => void;
};

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
      <p>{message}</p>
      {onRetry ? (
        <button
          className="mt-3 rounded-lg border border-rose-300 px-3 py-2 font-medium text-rose-700 transition hover:bg-rose-100"
          onClick={onRetry}
          type="button"
        >
          Reintentar
        </button>
      ) : null}
    </div>
  );
}
