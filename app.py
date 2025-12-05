import streamlit as st
import backend.transcriber as transcriber
import backend.generator as generator
import os
from datetime import datetime, timezone
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.query import Query
from appwrite.id import ID

# Configuración de página
st.set_page_config(page_title="Multi-Video Repurposer", page_icon="🤖", layout="wide")

# --- VARIABLES DE ENTORNO ---
APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
APPWRITE_DB_ID = os.environ.get("APPWRITE_DATABASE_ID")
APPWRITE_COL_ID = os.environ.get("APPWRITE_COLLECTION_ID")

# --- CONFIGURACIÓN APPWRITE ---
def get_appwrite_services():
    if not APPWRITE_ENDPOINT or not APPWRITE_PROJECT_ID:
        st.error("❌ Faltan configuraciones de Appwrite.")
        return None, None
    
    client = Client()
    client.set_endpoint(APPWRITE_ENDPOINT)
    client.set_project(APPWRITE_PROJECT_ID)
    
    return Account(client), Databases(client)

# --- LÓGICA DE LÍMITE DIARIO ---
def check_daily_limit(user_id):
    account, databases = get_appwrite_services()
    if not databases: return False

    try:
        # 1. VERIFICAR QUÉ PLAN TIENE EL USUARIO
        # Obtenemos las preferencias del usuario actual
        prefs = account.get_prefs()
        user_plan = prefs.get('plan', 'free') # Si no tiene nada, asume 'free'

        # 2. DEFINIR EL LÍMITE SEGÚN EL PLAN
        if user_plan == 'pro':
            limit = 10  # Los PRO pueden hacer 50 videos
        else:
            limit = 3   # Los gratis solo 3

        # 3. CONTAR CUÁNTOS LLEVA HOY (Igual que antes...)
        today_start = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00.000+00:00")
        
        result = databases.list_documents(
            database_id=APPWRITE_DB_ID,
            collection_id=APPWRITE_COL_ID,
            queries=[
                Query.equal("user_id", user_id),
                Query.greater_than("$createdAt", today_start) 
            ]
        )
        
        usage_count = result['total']
        
        # Le pasamos el límite dinámico a la respuesta para mostrarlo en pantalla
        if usage_count >= limit:
            return False, usage_count, limit
        return True, usage_count, limit
        
    except Exception as e:
        print(f"Error consultando: {e}")
        return True, 0, 3

def log_usage(user_id, video_url):
    """Guarda un registro en la base de datos"""
    account, databases = get_appwrite_services()
    try:
        databases.create_document(
            database_id=APPWRITE_DB_ID,
            collection_id=APPWRITE_COL_ID,
            document_id=ID.unique(),
            data={
                "user_id": user_id,
                "video_url": video_url
            }
        )
    except Exception as e:
        print(f"No se pudo guardar el log: {e}")

# --- LOGIN ---
def login_page():
    st.title("🔐 Iniciar Sesión")
    st.write("Accede para usar el Repurposer AI")
    
    email = st.text_input("Email")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        account, _ = get_appwrite_services()
        try:
            session = account.create_email_password_session(email, password)
            st.session_state['user_id'] = session['userId']
            st.success("¡Bienvenido!")
            st.rerun()
        except Exception as e:
            st.error(f"Error de autenticación: {e}")

# --- APP PRINCIPAL ---
def main_app():
    user_id = st.session_state['user_id']
    
    # --- ESTILOS CSS PARA OCULTAR MENÚ Y FOOTER ---
    hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """
    st.markdown(hide_menu_style, unsafe_allow_html=True)
    
    # Botón de cerrar sesión en la barra lateral
    if st.sidebar.button("Cerrar Sesión"):
        account, _ = get_appwrite_services()
        try:
            account.delete_session('current')
        except:
            pass
        st.session_state.pop('user_id', None)
        st.rerun()

    st.title("🤖 AI Multi-Video Repurposer")
    
    # --- MOSTRAR USO ACTUAL ---
    can_proceed, usage_count, limit = check_daily_limit(user_id) 
    
    st.sidebar.write(f"📊 **Uso Diario:** {usage_count} / {limit} videos")
    
    if not can_proceed:
        st.error("🚫 **Has alcanzado tu límite de 3 videos por hoy.**")
        st.info("💡 Vuelve mañana para seguir creando contenido.")
        # Aquí podrías poner un botón de [Actualizar a PRO]
        return # Detenemos la ejecución de la app aquí si superó el límite

    st.markdown("""
    Convierte uno o varios videos de **YouTube** en posts virales.
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
            
        url_list = [line.strip() for line in urls_input.split('\n') if line.strip()]
        
        # Verificar cuántos videos intenta procesar AHORA vs cuantos le quedan
        videos_remaining = limit - usage_count
        if len(url_list) > videos_remaining:
            st.warning(f"⚠️ Intentas procesar {len(url_list)} videos, pero solo te quedan {videos_remaining} usos hoy.")
            st.stop()

        if not check_linkedin and not check_twitter:
            st.warning("⚠️ Selecciona al menos una plataforma.")
            st.stop()
            
        selected_platforms = []
        if check_linkedin: selected_platforms.append("linkedin")
        if check_twitter: selected_platforms.append("twitter")
        
        status_text = st.empty()
        bar = st.progress(0)
        
        full_transcription = ""
        total_videos = len(url_list)

        try:
            for i, url in enumerate(url_list):
                status_text.text(f"🎧 Procesando video {i+1} de {total_videos}: {url}...")
                
                # Transcribir
                text = transcriber.transcribe_url(url, index=i)
                full_transcription += f"\n\n--- TRANSCRIPCIÓN VIDEO {i+1} ({url}) ---\n{text}"
                
                # --- REGISTRAR USO EN BD ---
                # Importante: Registramos cada video procesado exitosamente
                log_usage(user_id, url)

                status_text.text("🧠 Generando textos con Llama 3...")
                progress = int((i + 1) / total_videos * 50)
                bar.progress(progress)
                
            status_text.text("🧠 Analizando toda la información combinada...")
            bar.progress(60)    
            
            content = generator.generate_content(full_transcription[:25000], selected_platforms)
            bar.progress(100)
            status_text.text("✅ ¡Contenido Generado!")
            
            # (El resto del código de visualización sigue igual...)
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
            
            # Actualizamos el contador visualmente forzando un rerun al final o mostrando aviso
            st.toast("¡Consumo registrado! Vuelve a cargar para ver tu cupo actualizado.")

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

# --- CONTROL DE FLUJO ---
if 'user_id' not in st.session_state:
    login_page()
else:
    main_app()