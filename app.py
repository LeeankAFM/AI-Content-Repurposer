import streamlit as st
import backend.transcriber as transcriber
import backend.generator as generator
import os
from appwrite.client import Client
from appwrite.services.account import Account

# Configuración de página
st.set_page_config(page_title="Multi-Video Repurposer", page_icon="🤖", layout="wide")

# --- CONFIGURACIÓN APPWRITE ---
APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")

def init_appwrite():
    if not APPWRITE_ENDPOINT or not APPWRITE_PROJECT_ID:
        st.error("❌ Faltan configuraciones de Appwrite.")
        return None
    client = Client()
    client.set_endpoint(APPWRITE_ENDPOINT)
    client.set_project(APPWRITE_PROJECT_ID)
    return Account(client)

def login_page():
    st.title("🔐 Iniciar Sesión")
    st.write("Accede para usar el Repurposer AI")
    
    email = st.text_input("Email")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        account = init_appwrite()
        try:
            # Crear sesión (esto devuelve un objeto sesión si es exitoso)
            session = account.create_email_password_session(email, password)
            st.session_state['user_id'] = session['userId']
            st.success("¡Bienvenido!")
            st.rerun() # Recargar la página para mostrar la app
        except Exception as e:
            st.error(f"Error de autenticación: {e}")

def main_app():
    # --- AQUÍ VA TU CÓDIGO ORIGINAL COMPLETO ---
    if st.sidebar.button("Cerrar Sesión"):
        account = init_appwrite()
        try:
            account.delete_session('current')
        except:
            pass
        st.session_state.pop('user_id', None)
        st.rerun()

    st.title("🤖 AI Multi-Video Repurposer")
    st.markdown("""
    Convierte uno o varios videos de **YouTube** en posts virales para **LinkedIn** y **Twitter**.
    *Límite: Videos de máx 20 minutos.*
    """)

    col_config1, col_config2 = st.columns(2)

    with col_config1:
        urls_input = st.text_area("🔗 Pega las URLs aquí (Una por renglón):", height=150)

    with col_config2:
        st.write("### 🎯 Selecciona el formato:")
        check_linkedin = st.checkbox("Generar post de LinkedIn", value=True)
        check_twitter = st.checkbox("Generar hilo de Twitter", value=True)

    if st.button("✨ Generar contenido fusionado"):
        if not urls_input:
            st.error("❌ Por favor, ingresa al menos una URL válida.")
            st.stop()
            
        if not check_linkedin and not check_twitter:
            st.warning("⚠️ Debes seleccionar al menos una plataforma.")
            st.stop()
            
        selected_platforms = []
        if check_linkedin: selected_platforms.append("linkedin")
        if check_twitter: selected_platforms.append("twitter")
        
        url_list = [line.strip() for line in urls_input.split('\n') if line.strip()]
        
        status_text = st.empty()
        bar = st.progress(0)
        
        full_transcription = ""
        total_videos = len(url_list)

        try:
            for i, url in enumerate(url_list):
                status_text.text(f"🎧 Procesando video {i+1} de {total_videos}: {url}...")
                
                # Esto ahora llama a la función con el chequeo de 20 min
                text = transcriber.transcribe_url(url, index=i)
                
                full_transcription += f"\n\n--- TRANSCRIPCIÓN VIDEO {i+1} ({url}) ---\n{text}"

                status_text.text("🧠 Generando textos con Llama 3...")
                progress = int((i + 1) / total_videos * 50)
                bar.progress(progress)
                
            status_text.text("🧠 Analizando toda la información combinada...")
            bar.progress(60)    
            
            content = generator.generate_content(full_transcription[:25000], selected_platforms)
            bar.progress(100)
            status_text.text("✅ ¡Contenido Generado!")
            
            if 'linkedin' in content and 'twitter' in content:
                col1, col2 = st.columns(2)
            else:
                col1 = st.container()
                col2 = st.container()

            if 'linkedin' in content:
                with col1:
                    st.subheader("🟦 LinkedIn Post")
                    st.markdown(content['linkedin'])

            if 'twitter' in content:
                target_col = col2 if 'linkedin' in content else col1
                with target_col:
                    st.subheader("🐦 Twitter Thread")
                    st.markdown(content['twitter'])

            with st.expander("Ver Transcripción Completa"):
                st.write(full_transcription)

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

# --- CONTROL DE FLUJO PRINCIPAL ---
if 'user_id' not in st.session_state:
    login_page()
else:
    main_app()