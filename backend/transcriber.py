import os
from groq import Groq
from yt_dlp import YoutubeDL

def check_duration_and_download(url, index):
    folder = "temp"
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    filename = f"audio_temp_{index}"
    filepath = os.path.join(folder, filename)
    
    # Configuración inicial para extraer info sin descargar
    ydl_opts_info = {
        "quiet": True,
        "no_warnings": True,
    }

    # 1. Verificar duración
    with YoutubeDL(ydl_opts_info) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            duration = info.get('duration', 0) # Duración en segundos
            
            # 20 minutos = 1200 segundos
            if duration > 1200:
                raise ValueError(f"❌ El video excede los 20 minutos ({int(duration/60)} min).")
                
        except Exception as e:
            # Si es el error de duración, lo relanzamos, si es otro, continuamos (a veces no da la info)
            if "excede los 20 minutos" in str(e):
                raise e
            print(f"⚠️ No se pudo verificar duración previa, intentando descarga... {e}")

    # 2. Descargar si pasa la prueba
    ydl_opts_download = {
        "format": "worstaudio",
        "outtmpl": f"{filepath}.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
            "preferredquality": "16",
        }],
    }

    with YoutubeDL(ydl_opts_download) as ydl:
        ydl.download([url])

    return f"{filepath}.m4a"

def transcribe_with_groq(audio_file):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("❌ No se encontró la API Key en las variables de entorno.")
    
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"❌ El archivo '{audio_file}' no existe.")
    
    client = Groq(api_key=api_key)
    
    with open(audio_file, "rb") as file_stream:
        result = client.audio.transcriptions.create(
            file=(audio_file, file_stream.read()),
            model="whisper-large-v3",
            response_format="text",
            language="es"
        )
        
    try:
        os.remove(audio_file)
    except:
        pass
    
    return result

def transcribe_url(url, index=0):
    # Usamos la nueva función que chequea duración
    audio_file = check_duration_and_download(url, index)
    print(f"✅ Audio {index} descargado correctamente: {audio_file}")
    transcription = transcribe_with_groq(audio_file)
    return transcription