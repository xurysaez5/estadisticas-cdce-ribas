import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN Y BLINDAJE ---
st.set_page_config(page_title="Estadísticas CDCE RIBAS", layout="wide")

if "supabase" not in st.secrets:
    st.error("⚠️ Error de Seguridad: Credenciales no encontradas.")
    st.stop()

URL = st.secrets["supabase"]["url"]
KEY = st.secrets["supabase"]["key"]

# CONEXIÓN GLOBAL (Para que el Login y la Carga de datos la reconozcan)
supabase = create_client(URL, KEY)

# --- 2. INICIALIZAR ESTADO DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_id = None
    st.session_state.escuelas_asignadas = []

# --- 3. PANTALLA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center;'>🔐 Sistema de Gestión CDCE RIBAS</h2>", unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                u_ingresado = st.number_input("Cédula de Identidad:", step=1, value=0)
                p_ingresada = st.text_input("Contraseña:", type="password")
                
                if st.form_submit_button("Ingresar"):
                    # Verificación contra la tabla de usuarios
                    res_user = supabase.table("usuarios").select("id, password").eq("usuario", u_ingresado).execute()
                    
                    if res_user.data and res_user.data[0]['password'] == p_ingresada:
                        u_uuid = res_user.data[0]['id']
                        # Obtener permisos de escuelas
                        res_permisos = supabase.table("usuario_escuelas").select("escuela_id").eq("usuario_id", u_uuid).execute()
                        
                        st.session_state.autenticado = True
                        st.session_state.usuario_id = u_uuid
                        st.session_state.escuelas_asignadas = [p['escuela_id'] for p in res_permisos.data]
                        
                        st.success("✅ Acceso correcto")
                        st.rerun()
                    else:
                        st.error("❌ Cédula o contraseña incorrecta")
    st.stop()

# --- 4. ESTILO CSS ---
st.markdown("""
<style>
    header { visibility: visible !important; background-color: #002D57 !important; }
    [data-testid="stHeader"] button, [data-testid="stHeader"] svg { fill: white !important; color: white !important; }
    .guia-menu {
        position: fixed; top: 3.6rem; left: 10px; background-color: rgba(0, 45, 87, 0.9);
        color: white; padding: 5px 12px; border-radius: 5px; font-size: 0.85rem;
        font-weight: bold; z-index: 9999; pointer-events: none;
    }
    [data-testid="stSidebar"][aria-expanded="true"] ~ div .guia-menu { display: none !important; }
    [data-testid="stAppViewContainer"] { background-color: #9BF0FB !important; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 2px solid #002D57 !important; }
    .st-card {
        background-color: #FFFFFF !important; color: #002D57 !important;
        padding: 15px !important; border-radius: 10px; border: 2px solid #002D57 !important;
        text-align: center; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .tit-pequeno { font-size: 1.2rem !important; font-weight: bold; color: #002D57 !important; }
    .val-pequeno { font-size: 2.8rem !important; font-weight: 800; color: #002D57 !important; margin: 0; }
    .block-container {padding-top: 6rem !important;}
    [data-testid="stNotification"] {
        background-color: #B00020 !important; color: white !important;
        border: 2px solid #5f0000 !important; border-radius: 10px !important;
    }
</style>
<div class="guia-menu">↑ Haga clic encima de la flecha</div>
""", unsafe_allow_html=True)

# --- 5. CONEXIÓN A DATOS ---
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

# Ejecutar carga de datos
df_esc, df_est, df_per, df_con, df_cat_car, df_cat_con, df_cat_dep = cargar_datos()

# FILTRADO DE SEGURIDAD (Solo escuelas permitidas para este usuario)
df_esc = df_esc[df_esc['id'].isin(st.session_state.escuelas_asignadas)]

# --- 6. PANEL LATERAL ---
if 'menu_actual' not in st.session_state:
    st.session_state.menu_actual = "Inicio"

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
    col_izq, col_centro, col_der = st.columns([1, 2, 1])
    with col_centro:
        if st.button("Cerrar Sesión", type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# --- 7. LÓGICA DE MES DINÁMICA ---
col_vacia, col_info = st.columns([3, 1])
with col_info:
    meses_lista = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                   "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    if st.session_state.menu_actual == "Inicio":
        mes_elegido = st.selectbox("Seleccione Mes de Auditoría:", meses_lista)
        st.session_state.mes_global = mes_elegido
    else:
        mes_elegido = st.session_state.get('mes_global', meses_lista[0])

    st.markdown(f'''
        <div class="st-card" style="border-top: 5px solid #002D57; padding: 10px;">
            <p style="font-size: 0.8rem; font-weight: bold; margin:0;">MES CONSULTADO</p>
            <p style="font-size: 1.8rem; font-weight: 800; color: #002D57; margin:0;">{mes_elegido.upper()}</p>
        </div>
    ''', unsafe_allow_html=True)

# --- 8. MÓDULOS DE VISUALIZACIÓN ---

# MÓDULO INICIO
if st.session_state.menu_actual == "Inicio":
    st.markdown("<h2 style='text-align: center;'>Resumen de Gestión de Carga</h2>", unsafe_allow_html=True)
    df_est_mes = df_est[df_est['mes_carga'] == mes_elegido] if not df_est.empty else pd.DataFrame()
    
    total_escuelas = len(df_esc)
    cargadas = df_est_mes['escuela_id'].nunique() if not df_est_mes.empty else 0
    pendientes = total_escuelas - cargadas
    
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f'<div class="st-card"><p class="tit-pequeno">Total Instituciones</p><p class="val-pequeno">{total_escuelas}</p></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="st-card"><p class="tit-pequeno">Cargadas</p><p class="val-pequeno">{cargadas}</p></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="st-card" style="border-color:#FF0000;"><p class="tit-pequeno" style="color:#FF0000">Pendientes</p><p class="val-pequeno" style="color:#FF0000">{pendientes}</p></div>', unsafe_allow_html=True)
    
    st.write("---")
    col_graf1, col_graf2 = st.columns([1, 1])
    
    with col_graf1:
        st.markdown("<p style='text-align: center; font-weight: bold;'>ESTADO DE CUMPLIMIENTO</p>", unsafe_allow_html=True)
        datos_pie = pd.DataFrame({"Estado": ["Cargadas", "Pendientes"], "Cantidad": [cargadas, pendientes]})
        fig_anillo = px.pie(datos_pie, values='Cantidad', names='Estado', hole=0.6,
                            color='Estado', color_discrete_map={'Cargadas':'#002D57', 'Pendientes':'#FF0000'})
        st.plotly_chart(fig_anillo, use_container_width=True)

    with col_graf2:
        st.markdown("<p style='text-align: center; font-weight: bold;'>RITMO DE CARGA</p>", unsafe_allow_html=True)
        if not df_est_mes.empty:
            df_est_mes['fecha'] = pd.to_datetime(df_est_mes['created_at']).dt.date
            tendencia = df_est_mes.groupby('fecha').size().reset_index(name='registros')
            fig_ritmo = px.area(tendencia, x='fecha', y='registros', color_discrete_sequence=['#002D57'])
            st.plotly_chart(fig_ritmo, use_container_width=True)
        else:
            st.info(f"No hay datos registrados para el mes de {mes_elegido}.")

# MÓDULO POR INSTITUCIÓN
elif st.session_state.menu_actual == "Por Institución":
    st.markdown("<h2 style='text-align: center;'>Consulta por Institución</h2>", unsafe_allow_html=True)
    if not df_esc.empty:
        seleccion = st.selectbox("Seleccione la Institución:", sorted(df_esc['nombre_actual'].tolist()))
        id_escuela = df_esc[df_esc['nombre_actual'] == seleccion]['id'].values[0]
        datos_carga = df_est[(df_est['escuela_id'] == id_escuela) & (df_est['mes_carga'] == mes_elegido)]
        
        if not datos_carga.empty:
            col_a, col_b = st.columns(2)
            with col_a: st.markdown(f'<div class="st-card">MATRÍCULA TOTAL<br><b>{datos_carga["total_matricula"].sum()}</b></div>', unsafe_allow_html=True)
            with col_b:
                asist = datos_carga['asistencia_promedio_real'].mean() if 'asistencia_promedio_real' in datos_carga.columns else 0
                st.markdown(f'<div class="st-card">PROM. ASISTENCIA<br><b>{asist:.1f}%</b></div>', unsafe_allow_html=True)
            st.plotly_chart(px.bar(datos_carga, x='nivel_educativo', y='total_matricula', color='detalle_grupo', barmode='group'), use_container_width=True)
        else:
            st.warning("⚠️ Esta institución no tiene registros cargados.")

# MÓDULO DOCENTES
elif st.session_state.menu_actual == "Docentes":
    st.markdown("<h2 style='text-align: center;'>Análisis Pedagógico de Docentes</h2>", unsafe_allow_html=True)
    if not df_esc.empty:
        seleccion_esc = st.selectbox("Seleccione la Institución:", sorted(df_esc['nombre_actual'].tolist()), key="sel_doc_inst")
        id_escuela = df_esc[df_esc['nombre_actual'] == seleccion_esc]['id'].values[0]
        df_base = df_per[(df_per['escuela_id'] == id_escuela) & (df_per['mes_carga'] == mes_elegido) & (df_per['tipo_personal'] == "Docente")]
        
        niveles_pedagogicos = sorted(df_base['nivel_educativo'].dropna().unique().tolist())
        if niveles_pedagogicos:
            nivel_elegido = st.selectbox("Seleccione el Nivel Educativo:", niveles_pedagogicos, key="sel_doc_nivel")
            df_f = df_base[df_base['nivel_educativo'] == nivel_elegido]
            if not df_f.empty:
                data_grafico = {
                    "Categoría": ["Hembras (Nom)", "Varones (Nom)", "Asist. Hembras", "Asist. Varones"],
                    "Cantidad": [df_f['hembras_contratadas'].sum(), df_f['varones_contratados'].sum(), df_f['asistencia_h'].sum(), df_f['asistencia_v'].sum()]
                }
                st.plotly_chart(px.bar(data_grafico, x="Categoría", y="Cantidad", color="Categoría", text_auto=True), use_container_width=True)
        else:
            st.warning("⚠️ Sin registros para este mes.")

# MÓDULO NO DOCENTES
elif st.session_state.menu_actual == "No Docentes":
    st.markdown("<h2 style='text-align: center;'>Análisis de Personal No Docente</h2>", unsafe_allow_html=True)
    if not df_esc.empty:
        seleccion_esc = st.selectbox("
