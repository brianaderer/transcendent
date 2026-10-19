import { create } from "zustand";

/** Browser-only state (atlas plate 30): which topic the pointer or keyboard focus is on. */
type UiState = {
  highlightedTopic: number | null;
  highlightTopic: (topicId: number | null) => void;
};

export const useUiState = create<UiState>((set) => ({
  highlightedTopic: null,
  highlightTopic: (topicId) => set({ highlightedTopic: topicId }),
}));
