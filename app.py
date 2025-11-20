import streamlit as st
import transcriber
import generator
import os

# 1. Configuración de la página (Título e icono)
st.set_page_config(page_title="AI Content Repurposer", page_icon="🤖", layout="wide")

# 2. Título y Descripción
st.title("🤖 AI Content Repurposer")
st.markdown("""
Convierte cualquier video de **YouTube** en posts virales para **LinkedIn** y **Twitter** en segundos.
Powered by **Groq, Whisper & Llama 3**.
""")

# 3. Input del Usuario (Barra de texto)
url = st.text_input("🔗 Pega la URL del video de YouTube aquí:")

# 4. Botón de Acción
if st.button("✨ Generar Contenido"):
    if not url:
        st.error("❌ Por favor, ingresa una URL válida.")
    else:
        # Creamos un contenedor para mostrar el progreso
        status_text = st.empty()
        bar = st.progress(0)

        try:
            # Paso A: Transcripción
            status_text.text("🎧 Descargando audio y transcribiendo con Whisper...")
            bar.progress(20)
            
            # Llamamos a tu función original
            transcription = transcriber.transcribe_url(url)
            
            bar.progress(50)
            status_text.text("🧠 Generando textos con Llama 3...")
            
            # Paso B: Generación
            content = generator.generate_content(transcription)
            
            bar.progress(100)
            status_text.text("✅ ¡Listo!")
            
            # 5. Mostrar Resultados en dos columnas
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🟦 LinkedIn Post")
                st.markdown(content['linkedin'])
                # Botón para copiar/descargar
                st.download_button(
                    label="📥 Descargar Markdown LinkedIn",
                    data=content['linkedin'],
                    file_name="post_linkedin.md",
                    mime="text/markdown"
                )

            with col2:
                st.subheader("🐦 Twitter Thread")
                st.markdown(content['twitter'])
                st.download_button(
                    label="📥 Descargar Markdown Twitter",
                    data=content['twitter'],
                    file_name="hilo_twitter.md",
                    mime="text/markdown"
                )

            # Mostrar la transcripción original en un desplegable (por si acaso)
            with st.expander("Ver Transcripción Original"):
                st.write(transcription)

        except Exception as e:
            st.error(f"Ocurrió un error: {e}")