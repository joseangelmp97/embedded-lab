"use client";

export const LAB_PROGRESS_UPDATED_EVENT = "lab-progress-updated";

export function notifyLabProgressUpdated(): void {
  window.dispatchEvent(new Event(LAB_PROGRESS_UPDATED_EVENT));
}

export function subscribeToLabProgressUpdates(onProgressUpdated: () => void): () => void {
  window.addEventListener(LAB_PROGRESS_UPDATED_EVENT, onProgressUpdated);

  return () => {
    window.removeEventListener(LAB_PROGRESS_UPDATED_EVENT, onProgressUpdated);
  };
}
