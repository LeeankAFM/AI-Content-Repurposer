# 🤖 AI Content Repurposer (YouTube to LinkedIn/Twitter)

Transforma videos largos de YouTube en contenido viral listo para publicar usando el poder de **Groq**, **Whisper** (Audio) y **Llama 3** (Texto).

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-red)
![Groq](https://img.shields.io/badge/AI-Groq_API-orange)

## 💡 ¿Qué hace este proyecto?

Esta herramienta automatiza el proceso de creación de contenido para marketing:

1.  **Descarga** el audio de múltiples videos de YouTube (`yt-dlp`).
2.  **Transcribe** el audio a texto con alta precisión usando **Whisper-large-v3**.
3.  **Sintetiza** y redacta posts profesionales para LinkedIn e hilos de Twitter usando **Llama 3**.

## 🛠️ Tech Stack

- **Backend Logic:** Python
- **Frontend:** Streamlit
- **AI Processing:** Groq API (Whisper + Llama 3)
- **Media Handling:** FFmpeg & YT-DLP
