import streamlit as st
from supabase import create_client

# 1. PRIMERO: Definir la conexión (La base de todo)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# 2. SEGUNDO: La Puerta Secreta (Ahora sí conoce a 'supabase')
if st.sidebar.checkbox("Activar Formulario de Directores"):
    st.title("🛠️ Limpieza de Datos de Directores")
    st.write("Solo se muestran instituciones con datos faltantes.")
    
    # Consultamos las escuelas que necesitan datos
    res = supabase.table("escuelas").select("id, nombre_actual").or_(
        "nombre_director.is.null, cedula_director.is.null, nombre_director.eq.'', cedula_director.eq.''"
    ).execute()
    escuelas_pendientes = res.data

    if escuelas_pendientes:
        opciones = {e['nombre_actual']: e['id'] for e in escuelas_pendientes}
        
        with st.form("limpieza_form"):
            seleccion = st.selectbox("Selecciona la Institución:", options=list(opciones.keys()))
            
            col1, col2 = st.columns(2)
            with col1:
                n = st.text_input("Nombre Completo del Director:")
                c = st.text_input("Cédula de Identidad:")
            with col2:
                m = st.text_input("Correo (Opcional):")
                t = st.text_input("Teléfono:")
            
            if st.form_submit_button("Guardar y Actualizar"):
                if n and c:
                    supabase.table("escuelas").update({
                        "nombre_director": n, 
                        "cedula_director": c,
                        "correo_electronico": m if m else None, 
                        "telefono": t
                    }).eq("id", opciones[seleccion]).execute()
                    
                    st.success(f"✅ ¡Actualizado: {seleccion}!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("⚠️ Nombre y Cédula son obligatorios.")
    else:
        st.success("🎉 ¡Felicidades! Todas las escuelas tienen sus directores registrados.")
    
    st.stop() # Bloquea el resto de la app mientras limpias

# 3. TERCERO: El resto de tu aplicación (Gráficos, KPIs, etc.)
# Aquí sigue tu código normal...
st.write("Aquí verías tus gráficos normales si la casilla estuviera desactivada.")
