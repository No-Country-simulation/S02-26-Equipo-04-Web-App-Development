import { describe, expect, it } from "vitest";
import { useAppStore } from "./useAppStore";

describe("useAppStore", () => {
  it("increments clicks", () => {
    useAppStore.setState({ clicks: 0 });

    useAppStore.getState().increaseClicks();

    expect(useAppStore.getState().clicks).toBe(1);
  });
});
