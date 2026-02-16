"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export interface MarkdownContentProps {
  content: string;
  className?: string;
}

export default function MarkdownContentRenderer({ content, className = "" }: MarkdownContentProps) {
  return (
    <div className={`prose prose-sm prose-slate max-w-none dark:prose-invert prose-headings:text-foreground prose-p:text-foreground prose-li:text-foreground prose-strong:text-foreground prose-a:text-emerald-600 dark:prose-a:text-emerald-400 ${className}`}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
