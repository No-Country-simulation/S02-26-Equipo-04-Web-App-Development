"use client";

import { LogOut, Menu, UserRound } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '../store/useAuthStore';
interface TopbarProps {
  onOpenMenu: () => void
}


export default function NavBar({ onOpenMenu }: TopbarProps){
    const logout = useAuthStore((state) => state.logout);

    const router = useRouter()
    const handleClick=() =>{
        logout();
        router.push("/auth/login")
    };
    return(
    <header className=" top-0 z-10 sticky border-b bg-night-900/60 border-white/10 px-4 py-3 backdrop-blur-xl sm:px-6">
        <div className='flex mx-auto max-w-7xl items-center gap-3 justify-between'>
            <div className="flex items-center gap-3">
            <button
            className=""
            aria-label="Abrir menu"
            onClick={() => {

                onOpenMenu();
            }}
          >
            <Menu size={18} /> 
          </button>
            <div>
                <p>Hacelo Corto</p>
                <h1>Dashboard</h1>
            </div>
            
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
            
            <div className='flex items-center gap-2 border border-white/15 rounded-full bg-white/5 px-3 py-1.5'>
                <div className='grid h-8 w-8 rounded-full place-items-center bg-white/10 text-neon-mint'>
                    <UserRound size={14}/>
                </div>
                <div className='hidden text-right sm:block'>
                    <p className='text-sm font-semibold text-white'>Nombre</p>
                    <p className='text-xs text-white/60'>correo@correo.com</p>
                </div>
                
            </div>
            <button onClick={handleClick} className='inline-flex items-center gap-2 rounded-lg border border-rose-400/35 bg-rose-400/10 px-3 py-2 text-xs font-semibold text-rose-200 transition hover:-translate-y-0.5 hover:bg-rose-400/200'>
                <LogOut size={14}/>
                Cerrar sessión
                </button>
        </div>
        </div>
        
    </header>
    )
}