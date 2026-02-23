import { Pause, Play, Volume2 } from "lucide-react"
import { useState } from "react";

type ControlProp={
    isPlaying:boolean, 
    togglePlay:  () => void,
    volume:number,
    timeNow:number ,
    volumenFunction: (event:React.ChangeEvent<HTMLInputElement>) => void,
    duration?:number 
}
const formatTime =(segundos:number) => {
    if(!segundos && segundos !== 0) return "0:00" 
    const totalSecond = Math.floor(segundos);
    const hora = Math.floor(segundos/3600);
    const minuto = Math.floor((segundos % 3600)/60) ;
    const seg = totalSecond % 60
    const padd = seg.toString().padStart(2, "0")
    if(hora > 0){
      const paddMin = minuto.toString().padStart(2, "0")
      return `${hora}:${paddMin}: ${padd}`
    }
    return `${minuto}:${padd}`
  } 

export function ControlPlayer({isPlaying, togglePlay,volume,timeNow ,volumenFunction, duration}:ControlProp){
      const [handHover, setHandHover] = useState(false);
    
    return(
        <>
        <div>
            <div className="absolute  bottom-2 left-2 overflow-hidden rounded-lg border border-white/15 bg-black/40">
                {isPlaying?(<Pause size={25}
                onClick={togglePlay}/>): <Play size={25} onClick={togglePlay}/>}
        
            </div>


            <div onMouseEnter={() =>setHandHover(true)} onMouseLeave={() => setHandHover(false)} className=" absolute bottom-2 right-2 rounded-full flex items-center gap-2 bg-black/30 px-2 py-1 overflow-hidden">
                <Volume2 className={`
                    transition-transform duration-200 ${handHover ? "-translate-x-1":"translate-x-0"}`}/>
                {handHover && (<input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={volume}
                onChange={volumenFunction}
                className={`
                transition-all duration-300 ease-out
                ${handHover ? "w-24 opacity-100" : "w-0 opacity-0"}
                `}
                />)}
                <div >
                    <span>{ formatTime(timeNow) }/ {formatTime(duration || 0)}</span>
                </div>  
            </div>
        </div>
        
        </>
    )
}