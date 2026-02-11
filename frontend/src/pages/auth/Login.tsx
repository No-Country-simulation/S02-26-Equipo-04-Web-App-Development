import {  Link, useNavigate } from "react-router-dom";

export function Login(){
    const navegate = useNavigate()
    return(
        
    <div>
        
        <p className="subtituloCard">Login</p>
        <div className="selectRegistro">
            <Link to = "">
            <button type="button" className="botonRegistro botonRegistroSleccionado">Login</button>

            </Link>
            <Link to="/auth/registro">
            <button type="button" className="botonRegistro hoverBoton" >Registro</button>
            </Link>
        </div>
        <form className="form">
        <label className ="label">
            <span className="tituloLabel">Correo</span>
            <input placeholder="correo@correo.com" className="campoForm"/>
        </label>
        <label className ="label">
            <span className="tituloLabel">password</span>
            <input placeholder="******" className="campoForm"/>
        </label>
        <button className="boton botonAzul">Entrar</button>
        
        <button className="boton iconGoogle">
            Ingresar con Google
            <img className="iconGoogle" width="20" height="20" src="https://img.icons8.com/fluency/48/google-logo.png" alt="google-logo"/>
        </button>
        </form>
        
    </div>
)
}