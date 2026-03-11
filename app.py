import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN Y BLINDAJE ---
st.set_page_config(page_title="Estadísticas CDCE RIBAS", layout="wide")

# BLINDAJE DE SEGURIDAD
if "supabase" not in st.secrets:
    st.error("⚠️ Error de Seguridad: Credenciales no encontradas.")
    st.info("Por favor, asegúrese de tener configurado el archivo 'secrets.toml'.")
    st.stop()

# CONEXIÓN (Usando tu formato de secrets [supabase])
URL = st.secrets["supabase"]["url"]
KEY = st.secrets["supabase"]["key"]
supabase = create_client(URL, KEY)

# --- 2. PUERTA SECRETA PARA LIMPIEZA DE DIRECTORES ---
if st.sidebar.checkbox("🔧 Activar Formulario de Directores"):
    st.title("🛠️ Actualización de Datos de Directores")
    st.info("Complete los datos de las instituciones con campos vacíos.")
    
    try:
        res = supabase.table("escuelas").select("id, nombre_actual").or_(
            "nombre_director.is.null, cedula_director.is.null, nombre_director.eq.'', cedula_director.eq.''"
        ).execute()
        escuelas_pendientes = res.data

        if escuelas_pendientes:
            opciones = {e['nombre_actual']: e['id'] for e in escuelas_pendientes}
            with st.form("limpieza_form"):
                seleccion = st.selectbox("Seleccione la Institución:", options=list(opciones.keys()))
                c1, c2 = st.columns(2)
                with c1:
                    n = st.text_input("Nombre Completo del Director:")
                    c = st.text_input("Cédula de Identidad:")
                with c2:
                    m = st.text_input("Correo (Opcional):")
                    t = st.text_input("Teléfono:")
                
                if st.form_submit_button("Guardar y Actualizar"):
                    if n and c:
                        supabase.table("escuelas").update({
                            "nombre_director": n, "cedula_director": c,
                            "correo_electronico": m if m else None, "telefono": t
                        }).eq("id", opciones[seleccion]).execute()
                        st.success(f"✅ ¡Actualizado: {seleccion}!")
                        st.rerun()
                    else:
                        st.error("Nombre y Cédula son obligatorios.")
        else:
            st.success("🎉 ¡Todo al día! No quedan escuelas pendientes.")
    except Exception as e:
        st.error(f"Error en limpieza: {e}")
    st.stop() 

# --- 3. ESTILO CSS ---
st.markdown("""
<style>
    header { visibility: visible !important; background-color: #002D57 !important; }
    [data-testid="stHeader"] button, [data-testid="stHeader"] svg { fill: white !important; color: white !important; }
    .guia-menu { position: fixed; top: 3.6rem; left: 10px; background-color: rgba(0, 45, 87, 0.9); color: white; padding: 5px 12px; border-radius: 5px; font-size: 0.85rem; font-weight: bold; z-index: 9999; pointer-events: none; }
    [data-testid="stAppViewContainer"] { background-color: #9BF0FB !important; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 2px solid #002D57 !important; }
    .st-card { background-color: #FFFFFF !important; color: #002D57 !important; padding: 15px !important; border-radius: 10px; border: 2px solid #002D57 !important; text-align: center; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .val-pequeno { font-size: 2.8rem !important; font-weight: 800; color: #002D57 !important; margin: 0; line-height: 1.2; }
    .tit-pequeno { font-size: 1.2rem !important; font-weight: bold; color: #002D57 !important; }
    [data-testid="stNotification"] { background-color: #B00020 !important; color: white !important; border-radius: 10px !important; }
</style>
<div class="guia-menu">↑ Haga clic encima de la flecha</div>
""", unsafe_allow_html=True)

# --- 4. CARGA DE DATOS ---
@st.cache_data(ttl=300)
def cargar_datos():
    try:
        esc = supabase.table("escuelas").select("*").execute()
        est = supabase.table("estudiantes").select("*").execute()
        per = supabase.table("personal").select("*").execute()
        con = supabase.table("condicion_laboral").select("*").execute()
        c_car = supabase.table("cat_cargo").select("*").execute()
        c_con = supabase.table("cat_condicion").select("*").execute()
        c_dep = supabase.table("cat_dependencia").select("*").execute()
        return (pd.DataFrame(esc.data), pd.DataFrame(est.data), pd.DataFrame(per.data),
                pd.DataFrame(con.data), pd.DataFrame(c_car.data), 
                pd.DataFrame(c_con.data), pd.DataFrame(c_dep.data))
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return [pd.DataFrame()] * 7

df_esc, df_est, df_per, df_con, df_cat_car, df_cat_con, df_cat_dep = cargar_datos()

# --- 5. PANEL LATERAL ---
if 'menu_actual' not in st.session_state:
    st.session_state.menu_actual = "Inicio"

with st.sidebar:
    if os.path.exists("logo definitivo1.png"):
        st.image("logo definitivo1.png", use_container_width=True)
    st.write("---")
    st.button("🏠 INICIO", on_click=lambda: setattr(st.session_state, 'menu_actual', 'Inicio'), use_container_width=True)
    st.button("🏫 POR INSTITUCIÓN", on_click=lambda: setattr(st.session_state, 'menu_actual', 'Por Institución'), use_container_width=True)
    st
