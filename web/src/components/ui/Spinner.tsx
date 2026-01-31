import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  className?: string;
  label?: string;
}

const sizeClasses = {
  sm: "h-4 w-4",
  md: "h-6 w-6",
  lg: "h-8 w-8",
};

/**
 * Loading spinner component that respects prefers-reduced-motion.
 * Uses CSS animation with motion-reduce modifier.
 */
export function Spinner({ size = "md", className, label = "Loading..." }: SpinnerProps) {
  return (
    <Loader2
      className={cn(
        "animate-spin motion-reduce:animate-none",
        sizeClasses[size],
        className
      )}
      aria-label={label}
      role="status"
    />
  );
}
