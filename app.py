import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import os

# --- 1. CONFIGURACIÓN Y BLINDAJE ---
st.set_page_config(page_title="Estadísticas CDCE RIBAS", layout="wide")

# BLINDAJE DE SEGURIDAD:
# Intentamos obtener las credenciales desde st.secrets.
# Si no existen, mostramos un aviso informativo y detenemos la ejecución.
if "supabase" not in st.secrets:
    st.error("⚠️ Error de Seguridad: Credenciales no encontradas.")
    st.info("Por favor, asegúrese de tener configurado el archivo 'secrets.toml' en la carpeta '.streamlit'.")
    st.stop()

URL = st.secrets["supabase"]["url"]
KEY = st.secrets["supabase"]["key"]

# --- 2. ESTILO CSS ---
st.markdown("""
<style>
    /* 1. Encabezado sólido */
    header {
        visibility: visible !important;
        background-color: #002D57 !important;
    }
    
    /* 2. Forzar flecha blanca */
    [data-testid="stHeader"] button, [data-testid="stHeader"] svg {
        fill: white !important;
        color: white !important;
    }

    /* 3. MENSAJE DE GUÍA INTELIGENTE */
    .guia-menu {
        position: fixed;
        top: 3.6rem;
        left: 10px;
        background-color: rgba(0, 45, 87, 0.9);
        color: white;
        padding: 5px 12px;
        border-radius: 5px;
        font-size: 0.85rem;
        font-weight: bold;
        z-index: 9999;
        pointer-events: none;
        transition: opacity 0.3s ease;
    }

    /* OCULTAR EL MENSAJE CUANDO EL MENÚ ESTÁ ABIERTO */
    /* En computadoras y móviles, cuando el sidebar se expande, 
       el contenedor principal cambia su margen. Usamos eso para ocultar la guía. */
    [data-testid="stSidebar"][aria-expanded="true"] ~ div .guia-menu,
    section[data-testid="stSidebar"] + section .guia-menu {
        display: none !important;
    }
    
    /* Regla específica para cuando el menú tapa la pantalla en el celular */
    div[data-tight="true"] .guia-menu {
        display: none !important;
    }

    /* 4. Colores de fondo */
    [data-testid="stAppViewContainer"] {
        background-color: #9BF0FB !important;
    }
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 2px solid #002D57 !important;
    }

    /* 5. Estilo de las tarjetas estadísticas (Blindado contra Modo Oscuro) */
    .st-card {
        background-color: #FFFFFF !important; /* Fondo siempre blanco */
        color: #002D57 !important;            /* Texto siempre azul oscuro */
        padding: 15px !important;             /* Un poco más de aire para el móvil */
        border-radius: 10px;
        border: 2px solid #002D57 !important; /* Borde más definido */
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }

    /* Forzamos el color azul en el título para que no se ponga blanco */
    .tit-pequeno { 
        font-size: 1.2rem !important; 
        font-weight: bold; 
        color: #002D57 !important; 
    }

    /* Forzamos el color azul en el valor y ajustamos el tamaño para que quepa en el celular */
    .val-pequeno { 
        font-size: 2.8rem !important; /* Bajamos de 3.5 a 2.8 para evitar que el número se salga */
        font-weight: 800; 
        color: #002D57 !important; 
        margin: 0;
        line-height: 1.2;
    }
    
    .block-container {padding-top: 6rem !important;}
    /* MEJORA DE CONTRASTE PARA ALERTAS (st.warning) */
    [data-testid="stNotification"] {
        background-color: #FFEB3B !important; /* Un amarillo más sólido y vibrante */
        color: #000000 !important; /* Texto negro puro para máxima legibilidad */
        border: 2px solid #FFC107 !important; /* Borde oscuro para definir la caja */
    }
    
    /* Asegura que el icono de la advertencia también sea visible */
    [data-testid="stNotification"] svg {
        fill: #000000 !important;
    }
    /* CAMBIO TOTAL AL RECTÁNGULO DE ADVERTENCIA */
    [data-testid="stNotification"] {
        background-color: #B00020 !important; /* Rojo fuerte */
        color: white !important;               /* Texto blanco puro */
        border: 2px solid #5f0000 !important;  /* Borde oscuro para dar profundidad */
        border-radius: 10px !important;
        padding: 15px !important;
    }
    
    /* Forzar que el icono (la advertencia) también sea blanco */
    [data-testid="stNotification"] svg {
        fill: white !important;
        color: white !important;
    }
</style>

<div class="guia-menu">↑ Haga clic encima de la flecha</div>
""", unsafe_allow_html=True)
# --- 3. CONEXIÓN A DATOS ---
@st.cache_data(ttl=300)
def cargar_datos():
    try:
        supabase = create_client(URL, KEY)
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

# --- 4. PANEL LATERAL ---
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
    # --- BOTÓN CENTRADO USANDO COLUMNAS ---
    # Creamos 3 columnas. La [1, 2, 1] hace que la del medio sea más ancha para el botón.
    col_izq, col_centro, col_der = st.columns([1, 2, 1])
    
    with col_centro:
        # Quitamos el 'st.sidebar.' porque ya estamos dentro del 'with st.sidebar'
        if st.button("Cerrar Sesión", type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# --- LÓGICA DE MES DINÁMICA ---
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



# --- MÓDULO INICIO ---
if st.session_state.menu_actual == "Inicio":
    st.markdown("<h2 style='text-align: center;'>Resumen de Gestión de Carga</h2>", unsafe_allow_html=True)
    df_est_mes = df_est[df_est['mes_carga'] == mes_elegido] if not df_est.empty else pd.DataFrame()
    
    total_escuelas = len(df_esc)
    cargadas = df_est_mes['escuela_id'].nunique() if not df_est_mes.empty else 0
    pendientes = total_escuelas - cargadas
    
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f'<div class="st-card"><p class="tit-pequeno">Total Instituciones</p><p class="val-pequeno">{total_escuelas}</p></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="st-card"><p class="tit-pequeno">Cargadas</p><p class="val-pequeno">{cargadas}</p></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="st-card" style="border-color:#FF0000;"><p class="tit-pequeno texto-rojo">Pendientes</p><p class="val-pequeno texto-rojo">{pendientes}</p></div>', unsafe_allow_html=True)
    
    st.write("---")
    col_graf1, col_graf2 = st.columns([1, 1])
    
    with col_graf1:
        st.markdown("<p style='text-align: center; font-weight: bold;'>ESTADO DE CUMPLIMIENTO (ANILLO)</p>", unsafe_allow_html=True)
        datos_pie = pd.DataFrame({"Estado": ["Cargadas", "Pendientes"], "Cantidad": [cargadas, pendientes]})
        fig_anillo = px.pie(datos_pie, values='Cantidad', names='Estado', hole=0.6,
                            color='Estado', color_discrete_map={'Cargadas':'#002D57', 'Pendientes':'#FF0000'})
        fig_anillo.update_layout(showlegend=True, height=350, margin=dict(t=20, b=20, l=20, r=20),
                                 paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_anillo, use_container_width=True, config={'displayModeBar': False, 'staticPlot': False})

    with col_graf2:
        st.markdown("<p style='text-align: center; font-weight: bold;'>RITMO DE CARGA (LÍNEA DE TIEMPO)</p>", unsafe_allow_html=True)
        if not df_est_mes.empty:
            df_est_mes['fecha'] = pd.to_datetime(df_est_mes['created_at']).dt.date
            tendencia = df_est_mes.groupby('fecha').size().reset_index(name='registros')
            fig_ritmo = px.area(tendencia, x='fecha', y='registros', color_discrete_sequence=['#002D57'])
            fig_ritmo.update_layout(height=350, margin=dict(t=20, b=20, l=20, r=20),
                                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_ritmo, use_container_width=True, config={'displayModeBar': False, 'staticPlot': False})
        else:
            st.info(f"No hay datos registrados para el mes de {mes_elegido}.")

# --- POR INSTITUCIÓN ---
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
            st.plotly_chart(px.bar(datos_carga, x='nivel_educativo', y='total_matricula', color='detalle_grupo', barmode='group'), use_container_width=True, config={'displayModeBar': False, 'staticPlot': False})
        else:
            st.warning("⚠️ Esta institución no tiene registros cargados.")

# --- MÓDULO DOCENTES ---
elif st.session_state.menu_actual == "Docentes":
    st.markdown("<h2 style='text-align: center;'>Análisis Pedagógico de Docentes</h2>", unsafe_allow_html=True)
    
    if not df_esc.empty:
        seleccion_esc = st.selectbox("Seleccione la Institución:", 
                                     sorted(df_esc['nombre_actual'].tolist()), key="sel_doc_inst")
        id_escuela = df_esc[df_esc['nombre_actual'] == seleccion_esc]['id'].values[0]

        df_base = df_per[
            (df_per['escuela_id'] == id_escuela) & 
            (df_per['mes_carga'] == mes_elegido) & 
            (df_per['tipo_personal'] == "Docente") &
            (df_per['nivel_educativo'] != "No Docente")
        ]
        
        niveles_pedagogicos = sorted(df_base['nivel_educativo'].dropna().unique().tolist())
        
        if niveles_pedagogicos:
            nivel_elegido = st.selectbox("Seleccione el Nivel Educativo:", niveles_pedagogicos, key="sel_doc_nivel")
            df_f = df_base[df_base['nivel_educativo'] == nivel_elegido]

            if not df_f.empty:
                h_cont = df_f['hembras_contratadas'].sum()
                v_cont = df_f['varones_contratados'].sum()
                h_asist = df_f['asistencia_h'].sum()
                v_asist = df_f['asistencia_v'].sum()

                data_grafico = {
                    "Categoría": ["Hembras (Nom)", "Varones (Nom)", "Asist. Hembras", "Asist. Varones"],
                    "Cantidad": [h_cont, v_cont, h_asist, v_asist],
                    "Grupo": ["Nómina", "Nómina", "Asistencia", "Asistencia"]
                }
                
                fig_col = px.bar(
                    data_grafico, 
                    x="Categoría", 
                    y="Cantidad",
                    color="Categoría",
                    title=f"Estadística Docente: {nivel_elegido}",
                    text_auto=True,
                    color_discrete_map={
                        "Hembras (Nom)": "#E91E63",
                        "Varones (Nom)": "#1976D2",
                        "Asist. Hembras": "#F48FB1",
                        "Asist. Varones": "#64B5F6"
                    }
                )

                fig_col.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", font=dict(size=14), height=500)
                st.plotly_chart(fig_col, use_container_width=True, config={'displayModeBar': False, 'staticPlot': False})
            else:
                st.info(f"ℹ️ No hay registros detallados para {nivel_elegido}.")
        else:
            st.warning("⚠️ Esta institución no tiene personal calificado como 'Docente' en este mes.")

# --- MÓDULO NO DOCENTES ---
elif st.session_state.menu_actual == "No Docentes":
    tipo = "No Docente"
    st.markdown(f"<h2 style='text-align: center;'>Análisis de Personal {tipo}</h2>", unsafe_allow_html=True)
    
    if not df_esc.empty:
        seleccion_esc = st.selectbox("Seleccione la Institución:", 
                                     sorted(df_esc['nombre_actual'].tolist()), key="sel_no_doc")
        
        id_escuela = df_esc[df_esc['nombre_actual'] == seleccion_esc]['id'].values[0]
        
        df_f = df_per[(df_per['escuela_id'] == id_escuela) & 
                      (df_per['tipo_personal'] != "Docente") & 
                      (df_per['mes_carga'] == mes_elegido)]
        
        if not df_f.empty:
            total_v = df_f['varones_contratados'].sum()
            total_h = df_f['hembras_contratadas'].sum()
            total_personal = total_v + total_h
            total_asistieron = df_f['asistencia_v'].sum() + df_f['asistencia_h'].sum()
            promedio_asist = (total_asistieron / total_personal * 100) if total_personal > 0 else 0

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="st-card"><p class="tit-pequeno">TOTAL PERSONAL</p><p class="val-pequeno">{total_personal}</p></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="st-card"><p class="tit-pequeno">VARONES</p><p class="val-pequeno">{total_v}</p></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="st-card"><p class="tit-pequeno">HEMBRAS</p><p class="val-pequeno">{total_h}</p></div>', unsafe_allow_html=True)
            with c4: 
                col_asist = "texto-rojo" if promedio_asist < 75 else ""
                st.markdown(f'<div class="st-card"><p class="tit-pequeno {col_asist}">% ASISTENCIA</p><p class="val-pequeno {col_asist}">{promedio_asist:.1f}%</p></div>', unsafe_allow_html=True)

            st.write("---")
            
            df_graf = df_f.groupby(['tipo_personal']).agg({
                'varones_contratados': 'sum', 'hembras_contratadas': 'sum',
                'asistencia_v': 'sum', 'asistencia_h': 'sum'
            }).reset_index()

            df_graf['Total'] = df_graf['varones_contratados'] + df_graf['hembras_contratadas']
            df_graf['Asistieron'] = df_graf['asistencia_v'] + df_graf['asistencia_h']
            df_graf['% Asistencia'] = (df_graf['Asistieron'] / df_graf['Total'] * 100).fillna(0)

            st.markdown(f"<p style='text-align: center; font-weight: bold;'>ESTADÍSTICAS POR CARGO ({mes_elegido.upper()})</p>", unsafe_allow_html=True)

            g1, g2 = st.columns(2)
            with g1:
                fig1 = px.bar(df_graf, x="tipo_personal", y="Total", text="Total",
                               title="Cantidades por Tipo de Personal",
                               color_discrete_sequence=['#002D57'])
                st.plotly_chart(fig1, use_container_width=True, key="bar_total_nodoc", config={'displayModeBar': False, 'staticPlot': False})

            with g2:
                fig2 = px.bar(df_graf, x="tipo_personal", y="% Asistencia", text="% Asistencia",
                               title="Promedio de Asistencia por Cargo",
                               color="% Asistencia", color_continuous_scale='RdYlGn', range_color=[50, 100])
                fig2.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                st.plotly_chart(fig2, use_container_width=True, key="bar_perc_nodoc", config={'displayModeBar': False, 'staticPlot': False})

            g3, g4 = st.columns(2)
            with g3:
                df_gen = df_graf.melt(id_vars='tipo_personal', value_vars=['varones_contratados', 'hembras_contratadas'],
                                     var_name='Género', value_name='Cantidad')
                fig3 = px.bar(df_gen, x="tipo_personal", y="Cantidad", color="Género",
                               title="Distribución por Género", barmode="group",
                               color_discrete_map={'varones_contratados': '#00D4FF', 'hembras_contratadas': '#FF00D4'})
                st.plotly_chart(fig3, use_container_width=True, key="bar_gen_nodoc", config={'displayModeBar': False, 'staticPlot': False})

            with g4:
                df_comp = df_graf.melt(id_vars='tipo_personal', value_vars=['Total', 'Asistieron'],
                                      var_name='Estatus', value_name='Cantidad')
                fig4 = px.bar(df_comp, x="tipo_personal", y="Cantidad", color="Estatus",
                               title="Comparativa: Contratados vs Asistieron", barmode="group",
                               color_discrete_map={'Total': '#002D57', 'Asistieron': '#00D4FF'})
                st.plotly_chart(fig4, use_container_width=True, key="bar_comp_nodoc", config={'displayModeBar': False, 'staticPlot': False})
        else:
            st.warning(f"No hay registros de personal No Docente en {mes_elegido}.")

# --- MÓDULO CONDICIÓN LABORAL ---
elif st.session_state.menu_actual == "Condicion":
    st.markdown("<h2 style='text-align: center;'>Estatus y Condición Laboral Detallada</h2>", unsafe_allow_html=True)
    
    if not df_esc.empty:
        seleccion_esc = st.selectbox("Seleccione la Institución:", 
                                     sorted(df_esc['nombre_actual'].tolist()), key="sel_cond_mapeo")
        
        id_escuela = df_esc[df_esc['nombre_actual'] == seleccion_esc]['id'].values[0]
        df_puente = df_con[df_con['escuela_id'] == id_escuela].copy()

        if not df_puente.empty:
            dict_cargos = df_cat_car.set_index('id')['nombre'].to_dict()
            dict_deps = df_cat_dep.set_index('id')['nombre'].to_dict()
            dict_conds = df_cat_con.set_index('id')['nombre'].to_dict()

            df_puente['CAT_CARGO'] = df_puente['cargo_id'].map(dict_cargos)
            df_puente['CAT_DEPENDENCIA'] = df_puente['dependencia_id'].map(dict_deps)
            df_puente['CAT_CONDICION'] = df_puente['condicion_id'].map(dict_conds)

            resumen = df_puente.groupby(['CAT_CONDICION', 'CAT_DEPENDENCIA', 'CAT_CARGO']).size().reset_index(name='cantidad')

            st.write(f"### Análisis Administrativo: {seleccion_esc}")
            cols = st.columns(3)
            for i, fila in resumen.iterrows():
                with cols[i % 3]:
                    st.markdown(f'''
                        <div class="st-card" style="border-top: 4px solid #002D57; text-align: left;">
                            <p style="color: #FF0000; font-weight: bold; font-size: 0.85rem; margin:0;">
                                {str(fila['CAT_CONDICION']).upper()}
                            </p>
                            <p style="margin:0; font-size: 0.85rem; color: #555;"><b>Cargo:</b> {fila['CAT_CARGO']}</p>
                            <p style="margin:0; font-size: 0.85rem; color: #555;"><b>Dependencia:</b> {fila['CAT_DEPENDENCIA']}</p>
                            <h2 style="margin: 5px 0 0 0; color: #002D57;">{int(fila['cantidad'])}</h2>
                        </div>
                    ''', unsafe_allow_html=True)
        else:

            st.warning("⚠️ No se encontraron registros en la tabla 'condicion_laboral' para esta institución.")
