import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN Y SEGURIDAD ---
st.set_page_config(page_title="Estadísticas CDCE RIBAS", layout="wide")

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
            u_ingresado = st.text_input("Cédula de Identidad:", placeholder="Ingrese solo números")
            p_ingresada = st.text_input("Contraseña:", type="password")
            
            if st.form_submit_button("Ingresar", use_container_width=True):
                if not u_ingresado.isdigit():
                    st.error("❌ La cédula debe contener solo números.")
                else:
                    try:
                        # Buscamos usuario, clave y el ROL que ya existe en tu tabla
                        res_user = supabase.table("usuarios").select("id, password, rol").eq("usuario", int(u_ingresado)).execute()
                        
                        if res_user.data and res_user.data[0]['password'] == p_ingresada:
                            user_data = res_user.data[0]
                            st.session_state.autenticado = True
                            st.session_state.usuario_id = user_data['id']
                            # Si la columna rol está vacía en Supabase, le asignamos 'director' por defecto
                            st.session_state.rol = user_data.get('rol') if user_data.get('rol') else 'director'
                            
                            # Si NO es admin, buscamos sus escuelas asignadas
                            if st.session_state.rol != 'admin':
                                res_permisos = supabase.table("usuario_escuelas").select("escuela_id").eq("usuario_id", user_data['id']).execute()
                                st.session_state.escuelas_asignadas = [p['escuela_id'] for p in res_permisos.data]
                            
                            st.rerun()
                        else:
                            st.error("❌ Cédula o contraseña incorrecta")
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
    .badge-rol { background-color: #D4AF37; color: black; padding: 5px; border-radius: 5px; font-weight: bold; text-align: center; margin-bottom: 10px; }
</style>
<div class="guia-menu">↑ Menú</div>
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

df_esc_total, df_est, df_per, df_con, df_cat_car, df_cat_con = cargar_datos()

# FILTRADO POR ROL
if st.session_state.rol == 'admin':
    df_esc = df_esc_total
else:
    df_esc = df_esc_total[df_esc_total['id'].isin(st.session_state.escuelas_asignadas)]

# --- 6. PANEL LATERAL ---
with st.sidebar:
    if os.path.exists("logo definitivo1.png"):
        st.image("logo definitivo1.png", use_container_width=True)
    
    if st.session_state.rol == 'admin':
        st.markdown("<div class='badge-rol'>⭐ MODO ADMINISTRADOR</div>", unsafe_allow_html=True)
        
    st.button("🏠 INICIO", on_click=lambda: setattr(st.session_state, 'menu_actual', 'Inicio'), use_container_width=True)
    st.button("🏫 POR INSTITUCIÓN", on_click=lambda: setattr(st.session_state, 'menu_actual', 'Por Institución'), use_container_width=True)
    st.write("**GESTIÓN DE PERSONAL**")
    st.button("👩‍🏫 DOCENTES", on_click=lambda: setattr(st.session_state, 'menu_actual', 'Docentes'), use_container_width=True)
    st.button("🛠️ NO DOCENTES", on_click=lambda: setattr(st.session_state, 'menu_actual', 'No Docentes'), use_container_width=True)
    
    if st.session_state.rol == 'admin':
        st.write("---")
        st.write("**CONTROL TOTAL**")
        st.button("📊 TABLA MAESTRA", on_click=lambda: setattr(st.session_state, 'menu_actual', 'AdminTable'), use_container_width=True)

    st.write("---")
    if st.button("Cerrar Sesión", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# --- 7. PERIODO ---
meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
col_v, col_m = st.columns([3, 1])
with col_m:
    mes_elegido = st.selectbox("Mes:", meses_lista)
    st.session_state.mes_global = mes_elegido

# --- 8. MÓDULOS ---

if st.session_state.menu_actual == "Inicio":
    st.markdown(f"<h2 style='text-align: center;'>Gestión Ribas - {mes_elegido}</h2>", unsafe_allow_html=True)
    df_est_mes = df_est[df_est['mes_carga'] == mes_elegido]
    total_esc = len(df_esc)
    cargadas = df_est_mes[df_est_mes['escuela_id'].isin(df_esc['id'])]['escuela_id'].nunique()
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="st-card"><p>Total</p><h2>{total_esc}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="st-card"><p>Cargadas</p><h2>{cargadas}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="st-card"><p style="color:red">Pendientes</p><h2 style="color:red">{total_esc - cargadas}</h2></div>', unsafe_allow_html=True)

elif st.session_state.menu_actual == "AdminTable":
    st.markdown("<h2 style='text-align: center;'>Base de Datos Global</h2>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📊 Estudiantes (Matrícula)", "👥 Personal (Nómina)"])
    with tab1:
        st.dataframe(df_est[df_est['mes_carga'] == mes_elegido], use_container_width=True)
    with tab2:
        st.dataframe(df_per[df_per['mes_carga'] == mes_elegido], use_container_width=True)

elif st.session_state.menu_actual == "Por Institución":
    st.markdown("<h2 style='text-align: center;'>Consulta Individual</h2>", unsafe_allow_html=True)
    if not df_esc.empty:
        inst = st.selectbox("Institución:", sorted(df_esc['nombre_actual'].tolist()))
        id_i = df_esc[df_esc['nombre_actual'] == inst]['id'].values[0]
        data = df_est[(df_est['escuela_id'] == id_i) & (df_est['mes_carga'] == mes_elegido)]
        if not data.empty:
            st.plotly_chart(px.bar(data, x='nivel_educativo', y='total_matricula', color='detalle_grupo', barmode='group'), use_container_width=True)
        else:
            st.info("Aún no han cargado datos este mes.")
elif st.session_state.menu_actual == "No Docentes":
    st.markdown("<h2 style='text-align: center;'>Análisis de Personal No Docente</h2>", unsafe_allow_html=True)
    if not df_esc.empty:
        sel_esc = st.selectbox("Institución:", sorted(df_esc['nombre_actual'].tolist()), key="nodoc_sel")
        id_esc = df_esc[df_esc['nombre_actual'] == sel_esc]['id'].values[0]
        df_f = df_per[(df_per['escuela_id'] == id_esc) & (df_per['tipo_personal'] != "Docente") & (df_per['mes_carga'] == mes_elegido)]
        if not df_f.empty:
            df_g = df_f.groupby('tipo_personal')[['varones_contratados', 'hembras_contratadas']].sum().reset_index()
            st.plotly_chart(px.bar(df_g, x="tipo_personal", y=["varones_contratados", "hembras_contratadas"], barmode="group"), use_container_width=True)
        else:
            st.info("No hay personal administrativo/obrero registrado.")

elif st.session_state.menu_actual == "Condicion":
    st.markdown("<h2 style='text-align: center;'>Estatus Laboral</h2>", unsafe_allow_html=True)
    if not df_esc.empty:
        sel_esc = st.selectbox("Institución:", sorted(df_esc['nombre_actual'].tolist()), key="cond_sel")
        id_esc = df_esc[df_esc['nombre_actual'] == sel_esc]['id'].values[0]
        df_p = df_con[df_con['escuela_id'] == id_esc].copy()
        if not df_p.empty:
            df_p['Cargo'] = df_p['cargo_id'].map(df_cat_car.set_index('id')['nombre'].to_dict())
            df_p['Cond'] = df_p['condicion_id'].map(df_cat_con.set_index('id')['nombre'].to_dict())
            res = df_p.groupby(['Cond', 'Cargo']).size().reset_index(name='Cant')
            cols = st.columns(3)
            for i, r in res.iterrows():
                with cols[i % 3]:
                    st.markdown(f'<div class="st-card"><p style="color:red; font-weight:bold;">{r["Cond"]}</p><p>{r["Cargo"]}</p><h2>{r["Cant"]}</h2></div>', unsafe_allow_html=True)
        else:
            st.warning("⚠️ Sin registros de condición laboral.")


