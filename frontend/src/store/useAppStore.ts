import { create } from "zustand";

type AppState = {
  clicks: number;
  increaseClicks: () => void;
};

export const useAppStore = create<AppState>((set) => ({
  clicks: 0,
  increaseClicks: () => set((state) => ({ clicks: state.clicks + 1 }))
}));
