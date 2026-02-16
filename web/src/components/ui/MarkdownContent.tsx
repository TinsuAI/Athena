"use client";

import dynamic from "next/dynamic";
import type { MarkdownContentProps } from "./MarkdownContentRenderer";

// Dynamic import with ssr: false — react-markdown and its dependencies
// (micromark, mdast-util-*, remark-*) are ESM-only and break Turbopack SSR.
const MarkdownContentRenderer = dynamic(
  () => import("./MarkdownContentRenderer"),
  { ssr: false }
);

export function MarkdownContent(props: MarkdownContentProps) {
  return <MarkdownContentRenderer {...props} />;
}
