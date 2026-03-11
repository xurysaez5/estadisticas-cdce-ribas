import streamlit as st
#mosca aqui comienza limpieza
# --- PUERTA SECRETA PARA LIMPIEZA ---
# Solo aparecerá este botón si quieres limpiar datos
if st.sidebar.checkbox("Activar Formulario de Directores"):
    st.title("🛠️ Limpieza de Datos de Directores")
    
    # Aquí va el código que te pasé antes para filtrar las escuelas NULL
    escuelas_pendientes = supabase.table("escuelas").select("id, nombre_actual").or_(
        "nombre_director.is.null, cedula_director.is.null, nombre_director.eq.'', cedula_director.eq.''"
    ).execute().data

    if escuelas_pendientes:
        opciones = {e['nombre_actual']: e['id'] for e in escuelas_pendientes}
        with st.form("limpieza_form"):
            seleccion = st.selectbox("Escuela a completar:", options=list(opciones.keys()))
            col1, col2 = st.columns(2)
            with col1:
                n = st.text_input("Nombre Director:")
                c = st.text_input("Cédula:")
            with col2:
                m = st.text_input("Correo (Opcional):")
                t = st.text_input("Teléfono:")
            
            if st.form_submit_button("Guardar Datos"):
                if n and c:
                    supabase.table("escuelas").update({
                        "nombre_director": n, "cedula_director": c,
                        "correo_electronico": m if m else None, "telefono": t
                    }).eq("id", opciones[seleccion]).execute()
                    st.success("¡Guardado!")
                    st.rerun()
                else:
                    st.error("Nombre y Cédula son obligatorios.")
    else:
        st.success("¡Todo al día!")
    
    st.stop() # ESTO ES LO IMPORTANTE: Detiene el resto de la app
# --- FIN DE LA PUERTA SECRETA ---
from supabase import create_client

# 1. Configuración de conexión (Asegúrate de tener tus credenciales)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🛠️ Actualización de Datos de Directores")
st.write("Este formulario solo muestra escuelas con datos incompletos.")

# 2. Consultar solo escuelas que tengan NULL o vacío en los datos del director
def obtener_escuelas_incompletas():
    # Consultamos las columnas clave para filtrar
    response = supabase.table("escuelas").select("id, nombre_actual").or_(
        "nombre_director.is.null, cedula_director.is.null, nombre_director.eq.'', cedula_director.eq.''"
    ).execute()
    return response.data

escuelas_pendientes = obtener_escuelas_incompletas()

if escuelas_pendientes:
    # Creamos un diccionario para que en el selectbox se vea el nombre pero manejemos el ID
    opciones = {e['nombre_actual']: e['id'] for e in escuelas_pendientes}
    
    with st.form("form_actualizacion"):
        escuela_seleccionada = st.selectbox("Selecciona la Institución a completar:", options=list(opciones.keys()))
        id_escuela = opciones[escuela_seleccionada]
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            nuevo_nombre = st.text_input("Nombre Completo del Director:")
            nueva_cedula = st.text_input("Cédula de Identidad:")
        with col2:
            nuevo_correo = st.text_input("Correo Electrónico (Opcional):")
            nuevo_tlf = st.text_input("Teléfono de Contacto:")

        submit = st.form_submit_button("Guardar Cambios")

        if submit:
            if nuevo_nombre and nueva_cedula:
                # 3. Actualización quirúrgica en la tabla escuelas
                data, count = supabase.table("escuelas").update({
                    "nombre_director": nuevo_nombre,
                    "cedula_director": nueva_cedula,
                    "correo_electronico": nuevo_correo if nuevo_correo else None,
                    "telefono": nuevo_tlf
                }).eq("id", id_escuela).execute()
                
                st.success(f"✅ ¡Datos actualizados para: {escuela_seleccionada}!")
                st.balloons()
                # Recargamos la página para que la escuela ya no aparezca en la lista
                st.rerun()
            else:
                st.error("⚠️ El nombre y la cédula son obligatorios para poder crear el acceso después.")
else:

    st.success("🎉 ¡Increíble! No quedan escuelas con datos de director pendientes.")
