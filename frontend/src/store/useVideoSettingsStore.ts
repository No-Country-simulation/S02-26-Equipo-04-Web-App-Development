import { create } from "zustand";
import { persist } from "zustand/middleware";

export type VideoSettings = {
  subtitles: boolean;
  watermark: string;
  outputStyle: "vertical" | "speaker_split";
  contentProfile: "auto" | "interview" | "sports" | "music";
};

const defaultSettings: VideoSettings = {
  subtitles: true,
  watermark: "Hacelo Corto",
  outputStyle: "vertical",
  contentProfile: "auto"
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
