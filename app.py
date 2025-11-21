import streamlit as st
import backend.transcriber as transcriber
import backend.generator as generator
import os

st.set_page_config(page_title="Multi-Video Repurposer", page_icon="🤖", layout="wide")
st.title("🤖 AI Content Repurposer")
st.markdown("""
Convierte uno o varios videos de **YouTube** en posts virales para **LinkedIn** y **Twitter** en segundos.
Powered by **Groq, Whisper & Llama 3**.
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
        st.warning("⚠️ Debes seleccionar al menos una plataforma (LinkedIn o Twitter).")
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
            
            text = transcriber.transcribe_url(url, index=i)
            
            full_transcription += f"\n\n--- TRANSCRIPCIÓN VIDEO {i+1} ({url}) ---\n{text}"

            status_text.text("🧠 Generando textos con Llama 3...")
            
            progress = int((i + 1) / total_videos * 50)
            bar.progress(progress)
            
        status_text.text("🧠 Analizando toda la información combinada con Llama 3...")
        
        bar.progress(60)    
        
        content = generator.generate_content(full_transcription[:25000])
        
        bar.progress(100)
        
        status_text.text("✅ ¡Contenido Generado!")
        
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🟦 LinkedIn Post")
            st.markdown(content['linkedin'])
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

        with st.expander("Ver Transcripción Combinada Completa"):
            st.write(full_transcription)

    except Exception as e:
        st.error(f"Ocurrió un error: {e}")