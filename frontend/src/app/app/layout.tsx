"use client";

import NavBar from "@/src/layouts/NavBar";
import { Sidebar } from "@/src/layouts/Sidebar";
import { useState,ReactNode } from "react";


export default function Layout({children}:{children:ReactNode} ){

    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

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