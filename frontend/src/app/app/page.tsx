export default function AppHomePage() {
  return (
    <section className="mx-auto flex min-h-screen w-full max-w-4xl flex-col justify-center gap-5 px-6 py-10">
      <h2 className="font-display text-2xl text-white">Dashboard</h2>
      <p className="text-white/70">Sesion activa. Esta area queda protegida por el auth store.</p>
     </section>
  );
}
