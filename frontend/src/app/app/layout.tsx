"use client";

import NavBar from "@/src/layouts/NavBar";
import { Sidebar } from "@/src/layouts/Sidebar";
import { getProtectedRedirect } from "@/src/router/redirects";
import { useAuthStore } from "@/src/store/useAuthStore";
import { useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";


export default function Layout({children}:{children:ReactNode} ){

    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
    const router = useRouter();
    const bootstrapSession = useAuthStore((state) => state.bootstrapSession);
    const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
    const isBootstrapped = useAuthStore((state) => state.isBootstrapped);

    useEffect(() => {
        void bootstrapSession();
    }, [bootstrapSession]);

    useEffect(() => {
        const redirectPath = isBootstrapped ? getProtectedRedirect(isAuthenticated) : null;

        if (redirectPath) {
            router.replace(redirectPath);
        }
    }, [isAuthenticated, isBootstrapped, router]);

    if (!isBootstrapped || !isAuthenticated) {
        return null;
    }

    return (<div >
        <NavBar onOpenMenu={() => setMobileMenuOpen(prev => !prev)}/>

        <div className="fixed left-0 top-0 h-full flex">
            <Sidebar mobileOpen={mobileMenuOpen} closeMobile={() => setMobileMenuOpen(false)}/>
            <div>
                    {children}  
            </div>
        </div>
    </div>);
}
