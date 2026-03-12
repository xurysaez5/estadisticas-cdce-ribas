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
            u_ingresado = st.text_input("Cédula de Identidad:", placeholder="Solo números")
            p_ingresada = st.text_input("Contraseña:", type="password")
            
            if st.form_submit_button("Ingresar", use_container_width=True):
                if u_ingresado.isdigit():
                    try:
                        res_user = supabase.table("usuarios").select("id, password, rol").eq("usuario", int(u_ingresado)).execute()
                        if res_user.data and res_user.data[0]['password'] == p_ingresada:
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
                    st.warning("⚠️ Ingrese solo números en la cédula.")
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
    .val-pequeno { font-size: 2.2rem !important; font-weight: 800; color: #002D57 !important; margin: 0; }
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

# --- 7. LÓGICA DE PERIODO ---
meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
col_v, col_m = st.columns([3, 1])
with col_m:
    mes_elegido = st.selectbox("Mes de Auditoría:", meses_lista)
    st.session_state.mes_global = mes_elegido
    st.markdown(f'<div class="st-card" style="border-top: 5px solid #002D57; padding: 5px;"><p style="font-size: 1.2rem; font-weight: 800; margin:0;">{mes_elegido.upper()}</p></div>', unsafe_allow_html=True)

# --- 8. MÓDULOS ---

# INICIO
if st.session_state.menu_actual == "Inicio":
    st.markdown("<h2 style='text-align: center;'>Resumen de Gestión</h2>", unsafe_allow_html=True)
    df_mes = df_est[df_est['mes_carga'] == mes_elegido]
    total = len(df_esc)
    cargadas = df_mes[df_mes['escuela_id'].isin(df_esc['id'])]['escuela_id'].nunique()
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="st-card"><p>Total</p><p class="val-pequeno">{total}</p></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="st-card"><p>Cargadas</p><p class="val-pequeno">{cargadas}</p></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="st-card"><p style="color:red">Pendientes</p><p class="val-pequeno" style="color:red">{total-cargadas}</p></div>', unsafe_allow_html=True)

# POR INSTITUCIÓN
elif st.session_state.menu_actual == "Por Institución":
    st.markdown("<h2 style='text-align: center;'>Matrícula por Institución</h2>", unsafe_allow_html=True)
    if not df_esc.empty:
        inst = st.selectbox("Seleccione Institución:", sorted(df_esc['nombre_actual'].tolist()))
        id_i = df_esc[df_esc['nombre_actual'] == inst]['id'].values[0]
        d = df_est[(df_est['escuela_id'] == id_i) & (df_est['mes_carga'] == mes_elegido)]
        if not d.empty:
            fig = px.bar(d, x='nivel_educativo', y='total_matricula', color='detalle_grupo', barmode='group', title=inst)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("⚠️ Sin datos registrados para este mes.")

# DOCENTES
elif st.session_state.menu_actual == "Docentes":
    st.markdown("<h2 style='text-align: center;'>Personal Docente</h2>", unsafe_allow_html=True)
    if not df_esc.empty:
        inst = st.selectbox("Seleccione Institución:", sorted(df_esc['nombre_actual'].tolist()))
        id_i = df_esc[df_esc['nombre_actual'] == inst]['id'].values[0]
        d = df_per[(df_per['escuela_id'] == id_i) & (df_per['mes_carga'] == mes_elegido) & (df_per['tipo_personal'] == "Docente")]
        if not d.empty:
            fig = px.bar(d, x="nivel_educativo", y=["hembras_contratadas", "varones_contratados"], barmode="group", title=f"Docentes - {inst}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay registros de docentes.")

# NO DOCENTES
elif st.session_state.menu_actual == "No Docentes":
    st.markdown("<h2 style='text-align: center;'>Personal Administrativo, Obrero y Cocineras</h2>", unsafe_allow_html=True)
    if not df_esc.empty:
        inst = st.selectbox("Seleccione Institución:", sorted(df_esc['nombre_actual'].tolist()))
        id_i = df_esc[df_esc['nombre_actual'] == inst]['id'].values[0]
        d = df_per[(df_per['escuela_id'] == id_i) & (df_per['mes_carga'] == mes_elegido) & (df_per['tipo_personal'] != "Docente")]
        if not d.empty:
            df_g = d.groupby('tipo_personal')[['varones_contratados', 'hembras_contratadas']].sum().reset_index()
            fig = px.bar(df_g, x="tipo_personal", y=["varones_contratados", "hembras_contratadas"], barmode="group", title=f"No Docentes - {inst}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay registros de personal no docente.")

# CONDICIÓN LABORAL
elif st.session_state.menu_actual == "Condicion":
    st.markdown("<h2 style='text-align: center;'>Estatus y Condición Laboral</h2>", unsafe_allow_html=True)
    if not df_esc.empty:
        inst = st.selectbox("Seleccione Institución:", sorted(df_esc['nombre_actual'].tolist()))
        id_i = df_esc[df_esc['nombre_actual'] == inst]['id'].values[0]
        d = df_con[df_con['escuela_id'] == id_i].copy()
        if not d.empty:
            d['Cargo'] = d['cargo_id'].map(df_cat_car.set_index('id')['nombre'].to_dict())
            d['Condición'] = d['condicion_id'].map(df_cat_con.set_index('id')['nombre'].to_dict())
            res = d.groupby(['Condición', 'Cargo']).size().reset_index(name='Cantidad')
            cols = st.columns(3)
            for i, r in res.iterrows():
                with cols[i % 3]:
                    st.markdown(f'<div class="st-card"><p style="color:#002D57; font-weight:bold;">{r["Condición"]}</p><p>{r["Cargo"]}</p><h3>{r["Cantidad"]}</h3></div>', unsafe_allow_html=True)
        else:
            st.warning("Sin datos de condición laboral.")
