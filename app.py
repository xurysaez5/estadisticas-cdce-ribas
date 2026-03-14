# 14/03/2026 - Versión Corregida CDCE RIBAS
import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(
    page_title="Estadísticas CDCE RIBAS", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "supabase" not in st.secrets:
    st.error("⚠️ Error: Credenciales no encontradas")
    st.stop()

URL = st.secrets["supabase"]["url"]
KEY = st.secrets["supabase"]["key"]
supabase = create_client(URL, KEY)

# --- 2. GESTIÓN DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_id = None
    st.session_state.rol = None 
    st.session_state.escuelas_asignadas = []
    st.session_state.menu_actual = "Inicio"

# --- 3. PANTALLA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center;'>🔐 Acceso CDCE RIBAS</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            u_raw = st.text_input("Cédula de Identidad:", placeholder="Solo números").strip()
            p_raw = st.text_input("Contraseña:", type="password").strip()
            
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u_raw.isdigit():
                    try:
                        res_user = supabase.table("usuarios").select("id, password, rol").eq("usuario", int(u_raw)).execute()
                        if res_user.data and res_user.data[0]['password'] == p_raw:
                            user_data = res_user.data[0]
                            st.session_state.autenticado = True
                            st.session_state.usuario_id = user_data['id']
                            st.session_state.rol = str(user_data.get('rol', 'director')).lower()
                            
                            if st.session_state.rol != 'admin':
                                res_permisos = supabase.table("usuario_escuelas").select("escuela_id").eq("usuario_id", user_data['id']).execute()
                                st.session_state.escuelas_asignadas = [p['escuela_id'] for p in res_permisos.data]
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas")
                    except Exception as e:
                        st.error(f"Error de conexión: {e}")
                else:
                    st.warning("⚠️ Ingrese solo números.")
    st.stop()

# --- 4. ESTILO CSS ---
st.markdown("""
<style>
    header { visibility: visible !important; background-color: #002D57 !important; }
    [data-testid="stAppViewContainer"] { background-color: #9BF0FB !important; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 2px solid #002D57 !important; }
    .st-card {
        background-color: #FFFFFF !important; color: #002D57 !important;
        padding: 15px !important; border-radius: 10px; border: 2px solid #002D57 !important;
        text-align: center; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .val-kpi { font-size: 1.8rem !important; font-weight: 800; color: #002D57 !important; margin: 0; }
    .tit-kpi { font-size: 0.9rem; font-weight: bold; color: #555; margin-bottom: 5px; }
    div.stButton > button:first-child { border-radius: 10px; font-weight: bold; height: 3em; }
</style>
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
        c_con = supabase.table("cat_condicion").select("*").execute()
        return (pd.DataFrame(esc.data), pd.DataFrame(est.data), pd.DataFrame(per.data),
                pd.DataFrame(con.data), pd.DataFrame(c_car.data), pd.DataFrame(c_con.data))
    except:
        return [pd.DataFrame()] * 6

df_esc_t, df_est, df_per, df_con, df_cat_car, df_cat_con = cargar_datos()
df_esc = df_esc_t if st.session_state.rol == 'admin' else df_esc_t[df_esc_t['id'].isin(st.session_state.escuelas_asignadas)]

config_graf = {'displayModeBar': False}

# --- 6. PANEL LATERAL ---
with st.sidebar:
    if os.path.exists("logo definitivo1.png"):
        st.image("logo definitivo1.png", use_container_width=True)
    st.write("---")
    if st.button("🏠 INICIO", use_container_width=True): st.session_state.menu_actual = "Inicio"; st.rerun()
    if st.button("🏫 INSTITUCIÓN", use_container_width=True): st.session_state.menu_actual = "Por Institución"; st.rerun()
    st.write("**GESTIÓN DE PERSONAL**")
    if st.button("👩‍🏫 DOCENTES", use_container_width=True): st.session_state.menu_actual = "Docentes"; st.rerun()
    if st.button("🛠️ ADMINISTRATIVOS / OBREROS", use_container_width=True
