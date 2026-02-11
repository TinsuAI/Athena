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
      className="text-sm text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      title={
        lookupId
          ? `Suggest a correction for ${matchedHsCode}`
          : "Correction unavailable for this result"
      }
    >
      Suggest Correction
    </button>
  );
}
