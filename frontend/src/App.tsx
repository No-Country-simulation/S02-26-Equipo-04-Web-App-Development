import { useAppStore } from "./store/useAppStore";

function App() {
  const clicks = useAppStore((state) => state.clicks);
  const increaseClicks = useAppStore((state) => state.increaseClicks);

  return (
    <main className="min-h-screen bg-slate-100 text-slate-900">
      <section className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-6 px-6">
        <p className="rounded-full border border-brand-500/30 bg-brand-100 px-4 py-1 text-sm font-medium text-brand-700">
          Frontend base ready
        </p>
        <h1 className="text-center text-4xl font-bold tracking-tight">
          React + TypeScript + Tailwind + Zustand
        </h1>
        <p className="max-w-xl text-center text-lg text-slate-600">
          Esta base esta preparada para que el equipo frontend trabaje sobre
          features pequenas y PRs rapidos hacia develop.
        </p>
        <button
          type="button"
          className="rounded-lg bg-brand-500 px-5 py-3 text-white transition hover:bg-brand-700"
          onClick={increaseClicks}
        >
          Clicks del equipo: {clicks}
        </button>
      </section>
    </main>
  );
}

export default App;
