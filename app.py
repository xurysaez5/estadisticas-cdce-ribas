import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN Y SEGURIDAD ---
st.set_page_config(page_title="Estadísticas CDCE RIBAS", layout="wide")

if "supabase" not in st.secrets:
    st.error("⚠️ Error: Credenciales no encontradas en secrets.toml")
    st.stop()

URL = st.secrets["supabase"]["url"]
KEY = st.secrets["supabase"]["key"]
supabase = create_client(URL, KEY)

# --- 2. GESTIÓN DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_id = None
    st.session_state.escuelas_asignadas = []
    st.session_state.menu_actual = "Inicio"

# --- 3. PANTALLA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center;'>🔐 Acceso CDCE RIBAS</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            # Tarea 1: Uso de text_input para eliminar los símbolos + y -
            u_ingresado = st.text_input("Cédula de Identidad (solo números):", value="")
            p_ingresada = st.text_input("Contraseña:", type="password")
            
            if st.form_submit_button("Ingresar", use_container_width=True):
                if not u_ingresado.isdigit():
                    st.error("❌ Por favor, introduzca una cédula válida (solo números).")
                else:
                    try:
                        cedula_int = int(u_ingresado)
                        res_user = supabase.table("usuarios").select("id, password").eq("usuario", cedula_int).execute()
                        
                        if res_user.data and res_user.data[0]['password'] == p_ingresada:
                            u_uuid = res_user.data[0]['id']
                            res_permisos = supabase.table("usuario_escuelas").select("escuela_id").eq("usuario_id", u_uuid).execute()
                            
                            st.session_state.autenticado = True
                            st.session_state.usuario_id = u_uuid
                            st.session_state.escuelas_asignadas = [p['escuela_id'] for p in res_permisos.data]
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")
    st.stop()

# --- 4. ESTILO CSS ---
st.markdown("""
<style>
    header { visibility: visible !important; background-color: #002D57 !important; }
    [data-testid="stHeader"] button, [data-testid="stHeader"] svg { fill: white !important; color: white !important; }
    .guia-menu {
        position: fixed; top: 3.6rem; left: 10px; background-color: rgba(0, 45, 87, 0.9);
        color: white; padding: 5px 12px; border-radius: 5px; font-size: 0.85rem; font-weight: bold; z-index: 9999;
    }
    [data-testid="stAppViewContainer"] { background-color: #9BF0FB !important; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 2px solid #002D57 !important; }
    .st-card {
        background-color: #FFFFFF !important; color: #002D57 !important;
        padding: 15px !important; border-radius: 10px; border: 2px solid #002D57 !important;
        text-align: center; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .tit-pequeno { font-size: 1.1rem !important; font-weight: bold; color: #002D57 !important; }
    .val-pequeno { font-size: 2.5rem !important; font-weight: 800; color: #002D57 !important; margin: 0; }
    .texto-rojo { color: #FF0000 !important; }
</style>
<div class="guia-menu">↑ Haga clic encima de la flecha</div>
""", unsafe_allow_html=True)

# --- 5. CARGA DE DATOS ---
@st.cache_data(ttl=300)
def cargar_datos():
    try:
        esc = supabase.table("escuelas").select("*").execute()
        est = supabase.table("estudiantes").select("*").execute()
        per = supabase.table("personal").select("*").execute()
        con = supabase.table("condicion_laboral").select("*").execute()
        c_car = supabase.table("cat_cargo").select("*").execute()
        c
