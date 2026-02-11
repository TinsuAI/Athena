"use client";

import { useEffect } from "react";
import Link from "next/link";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error("Lookup detail page error:", error);
  }, [error]);

  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <div className="rounded-lg border bg-card p-8 text-center">
        <h2 className="text-lg font-semibold text-foreground mb-2">
          Đã xảy ra lỗi
        </h2>
        <p className="text-sm text-muted-foreground mb-4">
          Không thể tải trang chi tiết tra cứu. Vui lòng thử lại.
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            Thử lại
          </button>
          <Link
            href="/lookups"
            className="rounded-md border bg-background px-4 py-2 text-sm font-medium hover:bg-accent transition-colors"
          >
            Quay lại danh sách
          </Link>
        </div>
        {error.digest && (
          <p className="mt-4 text-xs text-muted-foreground">
            Mã lỗi: {error.digest}
          </p>
        )}
      </div>
    </div>
  );
}
