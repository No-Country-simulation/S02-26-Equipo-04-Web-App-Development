import { Link } from "react-router-dom";

export function Registro(){
    return(
        <div>
        
        <p className="subtituloCard">Registro</p>
        <div className="selectRegistro">
            <Link to="/auth/login">
                        <button type="button" className="botonRegistro hoverBoton">Login</button>

            </Link>
            <Link to ="">
                        <button type="button" className="botonRegistro botonRegistroSleccionado ">Registro</button>

            </Link>
        </div>
        <form className="form">
        <label className ="label">
            <span className="tituloLabel">Nombre</span>
            <input required placeholder="Tu nombre" className="campoForm"/>
        </label>
        <label className ="label">
            <span className="tituloLabel">Correo</span>
            <input required placeholder="correo@correo.com" className="campoForm"/>
        </label>
        <label className ="label">
            <span className="tituloLabel">password</span>
            <input required placeholder="******" className="campoForm"/>
        </label>
        <label className ="label">
            <span className="tituloLabel">Repetir password</span>
            <input required placeholder="******" className="campoForm"/>
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