import type { Lab } from "@/features/labs/types";

export function formatDifficultyLabel(difficulty: Lab["difficulty"]): string {
  return difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
}

export function formatStatusLabel(status: string): string {
  if (!status.trim()) {
    return "Unknown";
  }

  return status
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function formatTimestamp(isoDate: string): string {
  const date = new Date(isoDate);

  if (Number.isNaN(date.getTime())) {
    return "Unknown";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(date);
}
