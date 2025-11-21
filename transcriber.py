import os
from groq import Groq
from yt_dlp import YoutubeDL

def download_audio_with_groq(url, index):
    
    desired_filename = f"audio_temp_{index}"
    
    ydl_opts = {
        "format": "worstaudio",
        "outtmpl": f"{desired_filename}.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
            "preferredquality": "16",
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return f"{desired_filename}.m4a"


def transcribe_with_groq(audio_file):
    api_key = os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        raise ValueError("❌ No se encontró la API Key en las variables de entorno.")
    
    if not os.path.exists(audio_file):
        raise FileNotFoundError(f"❌ OJO: El archivo '{audio_file}' no se encuentra en la carpeta.")
    
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
    audio_file = download_audio_with_groq(url, index)
    print(f"✅ Audio {index} descargado correctamente: {audio_file}")
    transcription = transcribe_with_groq(audio_file)
    return transcription
