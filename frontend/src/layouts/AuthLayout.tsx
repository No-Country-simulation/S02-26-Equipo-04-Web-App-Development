import { Outlet } from "react-router-dom"
import '../style/authCardLayout.css'
export function AuthLayout(){
    return (
    <div className="bodyAuth">
        <div className="cardAuth">
            <p className="tituloCard">Hacelo Corto</p>
            <Outlet/>
            <button className="boton botonVolver">Volver</button>
        </div>
        
    </div>
    )    
}