"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { AlertCircle } from "lucide-react";

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

/**
 * Error boundary for the search page.
 * Catches runtime errors and displays a user-friendly message.
 */
export default function SearchError({ error, reset }: ErrorProps) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error("Search page error:", error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center max-w-md">
        <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
        <h2 className="text-2xl font-bold mb-2">Đã xảy ra lỗi</h2>
        <p className="text-muted-foreground mb-6">
          Đã xảy ra lỗi khi tải trang tìm kiếm. Vui lòng thử lại.
        </p>
        <Button onClick={reset}>Thử lại</Button>
      </div>
    </div>
  );
}
