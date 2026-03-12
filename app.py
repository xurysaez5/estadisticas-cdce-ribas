import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN Y BLINDAJE ---
st.set_page_config(page_title="Estadísticas CDCE RIBAS", layout="wide")

# Verificación de secretos
if "supabase" not in st.secrets:
    st.error("⚠️ Error: Credenciales no encontradas en secrets.toml")
    st.stop()

URL = st.secrets["supabase"]["url"]
KEY = st.secrets["supabase"]["key"]

# Conexión Global a Supabase
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
            u_ingresado = st.number_input("Cédula de Identidad:", step=1, value=0)
            p_ingresada = st.text_input("Contraseña:", type="password")
            
            if st.form_submit_button("Ingresar", use_container_width=True):
                try:
                    res_user = supabase.table("usuarios").select("id, password").eq("usuario", u_ingresado).execute()
                    
                    if res_user.data and res_user.data[0]['password'] == p_ingresada:
                        u_uuid = res_user.data[0]['id']
                        # Obtener escuelas permitidas para este usuario
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

# --- 4. ESTILO CSS (PERSONALIZACIÓN) ---
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
        c_con = supabase.table("cat_condicion").select("*").execute()
        c_dep = supabase.table("cat_dependencia").select("*").execute()
        
        return (pd.DataFrame(esc.data), pd.DataFrame(est.data), pd.DataFrame(per.data),
                pd.DataFrame(con.data), pd.DataFrame(c_car.data), 
                pd.DataFrame(c_con.data), pd.DataFrame(c_dep.data))
    except Exception as e:
        st.error(f"Error cargando tablas: {e}")
        return [pd.DataFrame()] * 7

# Ejecutar carga
df_esc_total, df_est, df_per, df_con, df_cat_car, df_cat_con, df_cat_dep = cargar_datos()

# Filtrar escuelas según el usuario logueado
df_esc = df_esc_total[df_esc_total['id'].isin(st.session_state.escuelas_asignadas)]

# --- 6. PANEL LATERAL ---
with st.sidebar:
    if os.path.exists("logo definitivo1.png"):
        st.image("logo definitivo1.png", use_container_width=True)
    st.write("---")
    st.button("🏠 INICIO", on_click=lambda: setattr(st.session_state, 'menu_actual', 'Inicio'), use_container_width=True)
    st.button("🏫 POR INSTITUCIÓN", on_click=lambda: setattr(st.session_state, 'menu_actual', 'Por Institución'), use_container_width=True)
    st.write("**GESTIÓN DE PERSONAL**")
    st.button("👩‍🏫 DOCENTES", on_click=lambda: setattr(st.session_state, 'menu_actual', 'Docentes'), use_container_width=True)
    st.button("🛠️ NO DOCENTES", on_click=lambda: setattr(st.session_state, 'menu_actual', 'No Docentes'), use_container_width=True)
    st.button("📜 CONDICIÓN LABORAL", on_click=lambda: setattr(st.session_state, 'menu_actual', 'Condicion'), use_container_width=True)
    st.write("---")
    if st.button("Cerrar Sesión", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 7. LÓGICA DE MES ---
meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
col_v, col_m = st.columns([3, 1])
with col_m:
    if st.session_state.menu_actual == "Inicio":
        mes_elegido = st.selectbox("Mes de Auditoría:", meses_lista)
        st.session_state.mes_global = mes_elegido
    else:
        mes_elegido = st.session_state.get('mes_global', meses_lista[0])
    st.markdown(f'<div class="st-card" style="border-top: 5px solid #002D57; padding: 10px;"><p style="font-size: 0.7rem; font-weight: bold; margin:0;">PERIODO</p><p style="font-size: 1.4rem; font-weight: 800; color: #002D57; margin:0;">{mes_elegido.upper()}</p></div>', unsafe_allow_html=True)

# --- 8. MÓDULOS ---

# INICIO
if st.session_state.menu_actual == "Inicio":
    st.markdown("<h2 style='text-align: center;'>Resumen de Gestión</h2>", unsafe_allow_html=True)
    df_est_mes = df_est[df_est['mes_carga'] == mes_elegido] if not df_est.empty else pd.DataFrame()
    total_esc = len(df_esc)
    cargadas = df_est_mes[df_est_mes['escuela_id'].isin(df_esc['id'])]['escuela_id'].nunique()
    pendientes = total_esc - cargadas
    
    c1, c2, c3 =
