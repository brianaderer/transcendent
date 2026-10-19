import { create } from "zustand";

/** Browser-only state (atlas plate 30): what the pointer is over, and the theme. */
type UiState = {
  highlightedTopic: number | null;
  highlightTopic: (topicId: number | null) => void;
};

export const useUiState = create<UiState>((set) => ({
  highlightedTopic: null,
  highlightTopic: (topicId) => set({ highlightedTopic: topicId }),
}));
