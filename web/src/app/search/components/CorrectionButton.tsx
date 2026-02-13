"use client";

interface CorrectionButtonProps {
  lookupId: number | null;
  matchedHsCode: string;
  matchedDescription: string;
  onCorrect: () => void;
}

export function CorrectionButton({
  lookupId,
  matchedHsCode,
  matchedDescription,
  onCorrect,
}: CorrectionButtonProps) {
  return (
    <button
      type="button"
      onClick={onCorrect}
      disabled={!lookupId}
      className="group relative inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-br from-emerald-600 to-emerald-700 hover:from-emerald-700 hover:to-emerald-800 text-white font-bold text-[13px] rounded-lg shadow-[0_2px_8px_rgba(5,150,105,0.25)] hover:shadow-[0_4px_16px_rgba(5,150,105,0.4)] transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none active:scale-[0.98]"
      title={
        lookupId
          ? `Đề xuất sửa đổi cho ${matchedHsCode}`
          : "Không thể đề xuất sửa đổi cho kết quả này"
      }
    >
      {/* Icon */}
      <svg
        className="w-4 h-4 transition-transform duration-200 group-hover:rotate-12"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2.5}
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
        />
      </svg>

      <span className="tracking-tight">Đề xuất sửa đổi</span>

      {/* Shimmer effect on hover */}
      <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
      </div>
    </button>
  );
}
