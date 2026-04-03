import { getSuggestedActionLabel } from "../../lib/mappers";
import type { SuggestedAction } from "../../types/api";

type ActionChipProps = {
  action: SuggestedAction;
};

export default function ActionChip({ action }: ActionChipProps) {
  return (
    <span className="inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-600">
      {getSuggestedActionLabel(action)}
    </span>
  );
}
