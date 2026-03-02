import { create } from "zustand";
import { persist } from "zustand/middleware";

export type VideoSettings = {
  cropToVertical: boolean;
  subtitles: boolean;
  faceTracking: boolean;
  colorFilter: boolean;
  watermark: string;
  videoStart: number;
  videoEnd: number;
};

const defaultSettings: VideoSettings = {
  cropToVertical: true,
  subtitles: true,
  faceTracking: false,
  colorFilter: false,
  watermark: "Hacelo Corto",
  videoStart: 0,
  videoEnd: 60
};

type VideoSettingsState = {
  settings: VideoSettings;
  saveSettings: (nextSettings: VideoSettings) => void;
  resetSettings: () => void;
};

export const useVideoSettingsStore = create<VideoSettingsState>()(
  persist(
    (set) => ({
      settings: defaultSettings,
      saveSettings: (nextSettings) => set({ settings: nextSettings }),
      resetSettings: () => set({ settings: defaultSettings })
    }),
    {
      name: "video-settings"
    }
  )
);
