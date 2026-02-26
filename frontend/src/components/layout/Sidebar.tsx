import { Film, Home, Upload, Waypoints, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const items = [
  { icon: Home, label: "Panel", href: "/app" },
  { icon: Waypoints, label: "Timeline editor", href: "/app/timeline" },
  { icon: Film, label: "Biblioteca clips", href: "/app/library" },
  { icon: Upload, label: "Exportacion", href: "/app/export" }
];

interface SidebarProps {
  mobileOpen: boolean;
  closeMobile: () => void;
}

export function Sidebar({ mobileOpen, closeMobile }: SidebarProps) {
  const pathname = usePathname();
  return (
    <>
      <div
        className={`fixed inset-0 z-30 bg-[#01030d]/60 backdrop-blur-sm transition lg:hidden ${
         mobileOpen ? "opacity-100" : "pointer-events-none opacity-0"}`}
        onClick={closeMobile}
      />
      <aside
        className={`fixed left-0 top-0 z-40 h-full w-72 border-r border-white/10 bg-night-900/90 p-5 backdrop-blur-xl transition-transform lg:sticky lg:top-[73px] lg:z-20 lg:h-[calc(100vh-73px)] lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"}`}
      >
        <div className="flex items-center justify-between lg:justify-start">
          <p className="font-display text-lg tracking-wide text-white">HACELO CORTO</p>
          <button
            className="rounded-lg border border-white/20 p-1 text-white/80 lg:hidden"
            onClick={closeMobile}
            aria-label="Cerrar menu"
          >
            <X size={16} />
          </button>
        </div>

        <p className="mt-2 text-xs uppercase tracking-[0.25em] text-neon-cyan/70">video dashboard</p>

        <nav className="mt-8 space-y-2">
          {items.map((item) => {
            const active =
              item.href === "/app"
                ? pathname === "/app"
                : pathname === item.href || pathname?.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.label}
                href={item.href}
                onClick={closeMobile}
                className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm transition ${
                  active
                    ? "bg-neon-cyan/10 text-neon-cyan hover:bg-neon-cyan/20"
                    : "text-white/60 hover:bg-white/10 hover:text-white"
                }`}
              >
                <item.icon size={16} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/*
        <div className="mt-10 rounded-2xl border border-neon-magenta/25 bg-neon-magenta/10 p-4 text-sm text-neon-magenta">
          <p className="font-semibold">Hacelo Corto</p>
          <p className="mt-1 text-xs text-neon-magenta/80">View transitions en navegacion interna.</p>
        </div> */}
      </aside>
    </>
  );
}
