"use client";

import { useEffect, useState } from "react";
import { getBrowseChapterDetail } from "@/lib/api";
import type {
  BrowseChapterDetailResponse,
  BrowseHeadingItem,
  BrowseSubheadingItem,
  BrowseHSCodeItem,
} from "@/types/browse";

/** Strip dots/spaces from HS code for comparison */
function normalize(code: string): string {
  return code.replace(/[\s.]/g, "");
}

/** Format a raw digit code with dots: 74182000 → 7418.20.00 */
function formatCode(code: string): string {
  const raw = normalize(code);
  if (raw.length === 8) return `${raw.slice(0, 4)}.${raw.slice(4, 6)}.${raw.slice(6)}`;
  if (raw.length === 6) return `${raw.slice(0, 4)}.${raw.slice(4)}`;
  if (raw.length === 4) return raw;
  if (raw.length === 2) return raw;
  return code;
}

interface HSCodeTreeProps {
  hsCode: string;
}

export function HSCodeTree({ hsCode }: HSCodeTreeProps) {
  const [chapter, setChapter] = useState<BrowseChapterDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const raw = normalize(hsCode);
  const chapterCode = raw.slice(0, 2);
  const headingCode = raw.slice(0, 4);

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setError(null);

    getBrowseChapterDetail(chapterCode)
      .then((data) => {
        if (!cancelled) setChapter(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load hierarchy");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [chapterCode]);

  if (isLoading) {
    return (
      <div className="mt-4 bg-white border border-slate-200 rounded-xl p-5 shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)]">
        <div className="flex items-center gap-2.5">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-200 border-t-emerald-600" />
          <span className="text-[12px] text-slate-400 font-medium">Đang tải phân cấp...</span>
        </div>
      </div>
    );
  }

  if (error || !chapter) {
    return null;
  }

  // Find the matching heading
  const matchedHeading = chapter.headings.find(
    (h) => normalize(h.heading_code) === headingCode
  );

  if (!matchedHeading) return null;

  return (
    <div className="mt-4 bg-white border border-slate-200 rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.06),0_0_0_1px_rgba(0,0,0,0.04)] overflow-hidden">
      <div className="px-5 py-3.5 border-b border-slate-100">
        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
          Phân cấp mã HS
        </h3>
      </div>
      <div className="p-4">
        {/* Chapter level */}
        <ChapterNode
          chapterCode={chapter.chapter_code}
          nameVn={chapter.name_vn}
        />

        {/* Heading level */}
        <div className="ml-5 mt-0.5">
          <HeadingNode heading={matchedHeading} matchedHsCode={raw} />
        </div>
      </div>
    </div>
  );
}

function TreeConnector({ isLast }: { isLast?: boolean }) {
  return (
    <span className="text-slate-300 font-mono text-[11px] select-none mr-1.5">
      {isLast ? "└─" : "├─"}
    </span>
  );
}

function ChapterNode({ chapterCode, nameVn }: { chapterCode: string; nameVn: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="font-mono text-[12px] font-bold text-slate-500">
        Ch. {chapterCode}
      </span>
      <span className="text-[12px] text-slate-400 font-medium truncate">
        {nameVn}
      </span>
    </div>
  );
}

function HeadingNode({
  heading,
  matchedHsCode,
}: {
  heading: BrowseHeadingItem;
  matchedHsCode: string;
}) {
  return (
    <div>
      <div className="flex items-baseline gap-1.5">
        <TreeConnector isLast />
        <span className="font-mono text-[12px] font-bold text-slate-600">
          {formatCode(heading.heading_code)}
        </span>
        <span className="text-[12px] text-slate-400 font-medium truncate">
          {heading.name_vn}
        </span>
      </div>

      {/* Subheadings */}
      <div className="ml-5">
        {heading.subheadings.map((sub, idx) => (
          <SubheadingNode
            key={sub.id}
            subheading={sub}
            matchedHsCode={matchedHsCode}
            isLast={idx === heading.subheadings.length - 1}
          />
        ))}
      </div>
    </div>
  );
}

function SubheadingNode({
  subheading,
  matchedHsCode,
  isLast,
}: {
  subheading: BrowseSubheadingItem;
  matchedHsCode: string;
  isLast: boolean;
}) {
  const subNorm = normalize(subheading.subheading_code);
  const matchedSubheading = matchedHsCode.startsWith(subNorm);

  return (
    <div className="mt-0.5">
      <div className="flex items-baseline gap-1.5">
        <TreeConnector isLast={isLast} />
        <span
          className={`font-mono text-[11.5px] font-semibold ${
            matchedSubheading ? "text-emerald-700" : "text-slate-500"
          }`}
        >
          {formatCode(subheading.subheading_code)}
        </span>
        <span
          className={`text-[11.5px] font-medium truncate ${
            matchedSubheading ? "text-emerald-600" : "text-slate-400"
          }`}
        >
          {subheading.name_vn}
        </span>
      </div>

      {/* HS Codes under this subheading */}
      {subheading.hs_codes.length > 0 && (
        <div className="ml-5">
          {subheading.hs_codes.map((code, idx) => (
            <HSCodeLeaf
              key={code.id}
              code={code}
              isMatched={normalize(code.code) === matchedHsCode}
              isLast={idx === subheading.hs_codes.length - 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function HSCodeLeaf({
  code,
  isMatched,
  isLast,
}: {
  code: BrowseHSCodeItem;
  isMatched: boolean;
  isLast: boolean;
}) {
  return (
    <div
      className={`mt-0.5 flex items-baseline gap-1.5 rounded-md px-1.5 py-0.5 -ml-1.5 ${
        isMatched ? "bg-emerald-50 ring-1 ring-emerald-200" : ""
      }`}
    >
      <TreeConnector isLast={isLast} />
      <span
        className={`font-mono text-[11px] font-bold shrink-0 ${
          isMatched ? "text-emerald-700" : "text-slate-500"
        }`}
      >
        {formatCode(code.code)}
      </span>
      <span
        className={`text-[11px] font-medium truncate ${
          isMatched ? "text-emerald-600" : "text-slate-400"
        }`}
      >
        {code.description_vn}
      </span>
      {isMatched && (
        <span className="shrink-0 text-[9px] font-bold text-emerald-600 bg-emerald-100 px-1.5 py-0.5 rounded-full">
          PHÙ HỢP
        </span>
      )}
    </div>
  );
}
