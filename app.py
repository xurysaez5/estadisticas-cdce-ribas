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
    if st.button("🛠️ ADMINISTRATIVOS / OBREROS", use_container_width=True): st.session_state.menu_actual = "No Docentes"; st.rerun()
    if st.button("📜 CONDICIÓN LABORAL", use_container_width=True): st.session_state.menu_actual = "Condicion"; st.rerun()
    st.write("---")
    st.write("**CARGA DE DATOS**")
    if st.button("📝 CARGAR MATRÍCULA", use_container_width=True): st.session_state.menu_actual = "Cargar Datos"; st.rerun()
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

# --- 8. MÓDULOS ---

if st.session_state.menu_actual == "Inicio":
    st.markdown("<h2 style='text-align: center;'>Menú Principal</h2>", unsafe_allow_html=True)
    c_nav1, c_nav2 = st.columns(2)
    with c_nav1:
        if st.button("🏫 Institución", use_container_width=True): st.session_state.menu_actual = "Por Institución"; st.rerun()
        if st.button("👩‍🏫 Docentes", use_container_width=True): st.session_state.menu_actual = "Docentes"; st.rerun()
    with c_nav2:
        if st.button("🛠️ Adm / Obreros / Coc", use_container_width=True): st.session_state.menu_actual = "No Docentes"; st.rerun()
        if st.button("📝 Cargar Datos", use_container_width=True): st.session_state.menu_actual = "Cargar Datos"; st.rerun()
    st.write("---")
    
    df_mes = df_est[df_est['mes_carga'] == mes_elegido]
    total_e = len(df_esc)
    cargadas = df_mes[df_mes['escuela_id'].isin(df_esc['id'])]['escuela_id'].nunique()
    
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="st-card"><p>Total Escuelas</p><p class="val-kpi">{total_e}</p></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="st-card"><p>Con Carga</p><p class="val-kpi">{cargadas}</p></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="st-card"><p style="color:red">Pendientes</p><p class="val-kpi" style="color:red">{total_e-cargadas}</p></div>', unsafe_allow_html=True)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if not df_mes.empty:
            df_g = df_mes.groupby('nivel_educativo')['total_matricula'].sum().reset_index()
            fig_i = px.pie(df_g, values='total_matricula', names='nivel_educativo', title="Matrícula por Nivel", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_i, use_container_width=True, config=config_graf)
    with col_g2:
        data_pie = pd.DataFrame({"Estado": ["Cargadas", "Pendientes"], "Cantidad": [cargadas, total_e-cargadas]})
        fig_p = px.pie(data_pie, values='Cantidad', names='Estado', title="Progreso de Carga", color_discrete_sequence=['#2ECC71', '#E74C3C'])
        st.plotly_chart(fig_p, use_container_width=True, config=config_graf)

else:
    if st.button("⬅️ Volver al Menú Principal"):
        st.session_state.menu_actual = "Inicio"; st.rerun()

    # --- NUEVO: MÓDULO CARGAR DATOS ---
    if st.session_state.menu_actual == "Cargar Datos":
        st.markdown("<h2 style='text-align: center;'>Registro de Matrícula y Asistencia</h2>", unsafe_allow_html=True)
        if not df_esc.empty:
            inst_nombres = sorted(df_esc['nombre_actual'].tolist())
            inst_elegida = st.selectbox("Seleccione Institución a reportar:", inst_nombres)
            id_escuela = df_esc[df_esc['nombre_actual'] == inst_elegida]['id'].values[0]
            
            with st.form("form_carga_est", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nivel = st.selectbox("Nivel Educativo:", ["Inicial", "Primaria", "Media General", "Especial"])
                    grupo = st.text_input("Grado / Sección / Grupo:", placeholder="Ej: 1er Grado A")
                    mes_c = st.selectbox("Mes que reporta:", meses_lista, index=meses_lista.index(mes_elegido))
                with col2:
                    v_ins = st.number_input("Varones Inscritos:", min_value=0, step=1)
                    h_ins = st.number_input("Hembras Inscritas:", min_value=0, step=1)
                    v_asist = st.number_input("Asistencia Promedio Varones:", min_value=0, step=1)
                    h_asist = st.number_input("Asistencia Promedio Hembras:", min_value=0, step=1)

                enviar = st.form_submit_button("🚀 GUARDAR REGISTRO", use_container_width=True)
                
                if enviar:
                    if (v_asist > v_ins) or (h_asist > h_ins):
                        st.error("❌ Error: La asistencia no puede ser mayor a la matrícula.")
                    elif (v_ins + h_ins) == 0:
                        st.warning("⚠️ Ingrese al menos un alumno.")
                    else:
                        total_m = v_ins + h_ins
                        prom_r = ((v_asist + h_asist) / total_m * 100) if total_m > 0 else 0
                        
                        nuevo_reg = {
                            "escuela_id": int(id_escuela), "nivel_educativo": nivel,
                            "detalle_grupo": grupo, "varones": v_ins, "hembras": h_ins,
                            "total_matricula": total_m, "asistencia_varones": v_asist,
                            "asistencia_hembras": h_asist, "asistencia_promedio_real": round(prom_r, 2),
                            "mes_carga": mes_c, "ano_escolar": "2023-2024"
                        }
                        try:
                            supabase.table("estudiantes").insert(nuevo_reg).execute()
                            st.success(f"✅ ¡Registro de {grupo} guardado!")
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"Error: {e}")

    # --- MÓDULO POR INSTITUCIÓN ---
    elif st.session_state.menu_actual == "Por Institución":
        st.markdown("<h2 style='text-align: center;'>Análisis por Institución</h2>", unsafe_allow_html=True)
        if not df_esc.empty:
            inst = st.selectbox("Seleccione Institución:", sorted(df_esc['nombre_actual'].tolist()))
            id_i = df_esc[df_esc['nombre_actual'] == inst]['id'].values[0]
            d = df_est[(df_est['escuela_id'] == id_i) & (df_est['mes_carga'] == mes_elegido)]
            
            if not d.empty:
                total_m = d['total_matricula'].sum()
                total_asist_real = d['asistencia_varones'].sum() + d['asistencia_hembras'].sum()
                porc_a = (total_asist_real / total_m * 100) if total_m > 0 else 0
                
                k1, k2, k3 = st.columns(3)
                with k1: st.markdown(f'<div class="st-card"><p class="tit-kpi">MATRÍCULA TOTAL</p><p class="val-kpi">{int(total_m)}</p></div>', unsafe_allow_html=True)
                with k2: st.markdown(f'<div class="st-card"><p class="tit-kpi">ASISTENCIA REAL</p><p class="val-kpi">{int(total_asist_real)}</p></div>', unsafe_allow_html=True)
                with k3: st.markdown(f'<div class="st-card"><p class="tit-kpi">% ASISTENCIA</p><p class="val-kpi">{porc_a:.1f}%</p></div>', unsafe_allow_html=True)
                
                fig = px.bar(d, x='nivel_educativo', y='total_matricula', color='detalle_grupo', barmode='group', text_auto=True, title=f"Distribución Estudiantil", color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig, use_container_width=True, config=config_graf)
            else:
                st.warning("⚠️ Sin datos registrados para este mes.")

    # --- MÓDULO DOCENTES ---
    elif st.session_state.menu_actual == "Docentes":
        st.markdown("<h2 style='text-align: center;'>Asistencia Personal Docente</h2>", unsafe_allow_html=True)
        if not df_esc.empty:
            inst = st.selectbox("Seleccione Institución:", sorted(df_esc['nombre_actual'].tolist()))
            id_i = df_esc[df_esc['nombre_actual'] == inst]['id'].values[0]
            d = df_per[(df_per['escuela_id'] == id_i) & (df_per['tipo_personal'] == "Docente") & (df_per['mes_carga'] == mes_elegido)]
            
            if not d.empty:
                total_contratado = d['varones_contratados'].sum() + d['hembras_contratadas'].sum()
                total_asist_doc = d['asistencia_v'].sum() + d['asistencia_h'].sum()
                porc_doc = (total_asist_doc / total_contratado * 100) if total_contratado > 0 else 0
                
                k1, k2, k3 = st.columns(3)
                with k1: st.markdown(f'<div class="st-card"><p class="tit-kpi">DOCENTES CONTRATADOS</p><p class="val-kpi">{int(total_contratado)}</p></div>', unsafe_allow_html=True)
                with k2: st.markdown(f'<div class="st-card"><p class="tit-kpi">ASISTENCIA PROMEDIO</p><p class="val-kpi">{int(total_asist_doc)}</p></div>', unsafe_allow_html=True)
                with k3: st.markdown(f'<div class="st-card"><p class="tit-kpi">% ASISTENCIA</p><p class="val-kpi">{porc_doc:.1f}%</p></div>', unsafe_allow_html=True)
                
                df_plot = d.melt(id_vars=['nivel_educativo'], value_vars=['asistencia_v', 'asistencia_h'], var_name='Género', value_name='Asistencia')
                df_plot['Género'] = df_plot['Género'].replace({'asistencia_h': 'Hembras', 'asistencia_v': 'Varones'})
                fig = px.bar(df_plot, x="nivel_educativo", y="Asistencia", color="Género", barmode="group", text_auto=True, title=f"Asistencia Docente", color_discrete_sequence=['#FF5733', '#FFC300']) 
                st.plotly_chart(fig, use_container_width=True, config=config_graf)
            else: st.info(f"ℹ️ Sin registros.")

    # --- MÓDULO NO DOCENTES ---
    elif st.session_state.menu_actual == "No Docentes":
        st.markdown("<h2 style='text-align: center;'>Asistencia Personal de Apoyo</h2>", unsafe_allow_html=True)
        if not df_esc.empty:
            inst = st.selectbox("Seleccione Institución:", sorted(df_esc['nombre_actual'].tolist()))
            id_i = df_esc[df_esc['nombre_actual'] == inst]['id'].values[0]
            d = df_per[(df_per['escuela_id'] == id_i) & (df_per['tipo_personal'] != "Docente") & (df_per['mes_carga'] == mes_elegido)]
            
            if not d.empty:
                total_contratado = d['varones_contratados'].sum() + d['hembras_contratadas'].sum()
                total_asist_apoyo = d['asistencia_v'].sum() + d['asistencia_h'].sum()
                porc_apoyo = (total_asist_apoyo / total_contratado * 100) if total_contratado > 0 else 0
                
                k1, k2, k3 = st.columns(3)
                with k1: st.markdown(f'<div class="st-card"><p class="tit-kpi">TOTAL PERSONAL APOYO</p><p class="val-kpi">{int(total_contratado)}</p></div>', unsafe_allow_html=True)
                with k2: st.markdown(f'<div class="st-card"><p class="tit-kpi">ASISTENCIA PROMEDIO</p><p class="val-kpi">{int(total_asist_apoyo)}</p></div>', unsafe_allow_html=True)
                with k3: st.markdown(f'<div class="st-card"><p class="tit-kpi">% ASISTENCIA</p><p class="val-kpi">{porc_apoyo:.1f}%</p></div>', unsafe_allow_html=True)
                
                df_g = d.groupby('tipo_personal')[['asistencia_v', 'asistencia_h']].sum().reset_index()
                df_plot = df_g.melt(id_vars=['tipo_personal'], value_vars=['asistencia_h', 'asistencia_v'], var_name='Género', value_name='Cantidad')
                df_plot['Género'] = df_plot['Género'].replace({'asistencia_h': 'Hembras', 'asistencia_v': 'Varones'})
                fig = px.bar(df_plot, x="tipo_personal", y="Cantidad", color="Género", barmode="group", text_auto=True, title=f"Asistencia por Categoría", color_discrete_sequence=['#27AE60', '#ABEBC6'])
                st.plotly_chart(fig, use_container_width=True, config=config_graf)
            else: st.info(f"ℹ️ Sin registros.")

    # --- MÓDULO CONDICIÓN ---
    elif st.session_state.menu_actual == "Condicion":
        st.markdown("<h2 style='text-align: center;'>Condición Laboral</h2>", unsafe_allow_html=True)
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
                        st.markdown(f'<div class="st-card"><p style="color:#002D57; font-weight:bold; margin:0;">{r["Condición"]}</p><p style="font-size:0.8rem; margin:0;">{r["Cargo"]}</p><h3>{int(r["Cantidad"])}</h3></div>', unsafe_allow_html=True)
            else: st.warning("⚠️ Sin datos registrados.")
