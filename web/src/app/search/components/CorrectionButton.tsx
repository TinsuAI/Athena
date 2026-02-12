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
      className="text-[12.5px] font-medium text-slate-400 hover:text-emerald-600 transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed"
      title={
        lookupId
          ? `Đề xuất sửa đổi cho ${matchedHsCode}`
          : "Không thể đề xuất sửa đổi cho kết quả này"
      }
    >
      Đề xuất sửa đổi
    </button>
  );
}
