"use client";

import { LogOut, Menu, UserRound } from 'lucide-react'
import Link from 'next/link';
import { useRouter } from 'next/navigation'
import { useTranslations } from 'next-intl';
import { HaceloCortoLogo } from '@/src/components/branding/HaceloCortoLogo';
import { useAuthStore } from '@/src/store/useAuthStore';
interface TopbarProps {
  onOpenMenu: () => void
}


export default function NavBar(
  { onOpenMenu }: TopbarProps
){
    const t = useTranslations("dashboard");
    const logout = useAuthStore((state) => state.logout);
    const user = useAuthStore((state) => state.user);
    const isLoading = useAuthStore((state) => state.isLoading);

    const router = useRouter()
    const handleClick=async() =>{
        await logout();
        router.replace("/auth/login")
    };

    const userName = user?.email ? user.email.split("@")[0] : t("defaultUser");
    const userEmail = user?.email ?? t("noEmail");

    return(
    <header className="sticky top-0 z-30 border-b border-white/10 bg-night-900/60 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div className='flex w-full items-center justify-between gap-3'>
            <div className="flex items-center gap-3">
          <button
            className="rounded-lg border border-white/20 p-1.5 text-white/85 transition hover:bg-white/10 lg:hidden"
            aria-label={t("openMenu")}
            onClick={() => {

                onOpenMenu();
            }}
          >
            <Menu size={18} /> 
          </button>
            <Link href="/app" className="inline-flex items-center" aria-label={t("goHome")}>
              <HaceloCortoLogo
                variant="compact"
                className="h-8 w-auto text-white lg:hidden sm:h-9"
                title="Hacelo Corto"
              />
              <HaceloCortoLogo
                variant="wordmark"
                className="hidden h-8 w-auto text-white lg:block"
                title="Hacelo Corto"
              />
            </Link>
             
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
            
            <div className='flex items-center gap-2 border border-white/15 rounded-full bg-white/5 px-3 py-1.5'>
                <div className='grid h-8 w-8 rounded-full place-items-center bg-white/10 text-neon-mint'>
                    <UserRound size={14}/>
                </div>
                <div className='hidden text-right sm:block'>
                    <p className='text-sm font-semibold text-white'>{userName}</p>
                    <p className='text-xs text-white/60'>{userEmail}</p>
                </div>
                
            </div>
            <button
                onClick={handleClick}
                className='logout-btn inline-flex items-center gap-2 rounded-lg border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-xs font-semibold text-rose-200 transition hover:-translate-y-0.5 hover:bg-rose-400/20 disabled:cursor-not-allowed disabled:opacity-70'
                disabled={isLoading}
            >
                <LogOut size={14}/>
                {isLoading ? t("loggingOut") : t("logout")}
                </button>
        </div>
        </div>
        
    </header>
    )
}
