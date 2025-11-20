from yt_dlp import YoutubeDL
from groq import Groq
import os
import transcriber, generator

def main():
    
    url = input("Enter the URL: ")
    print("You entered:", url)
    text = transcriber.transcribe_url(url)
    content = generator.generate_content(text)
    print("\n" + "="*30)
    print("📢 POST DE LINKEDIN")
    print("="*30)
    print(content['linkedin'])
    
    print("\n" + "="*30)
    print("🐦 HILO DE TWITTER")
    print("="*30)
    print(content['twitter'])
    
    with open("resultado_linkedin.md", "w", encoding="utf-8") as f:
        f.write(content['linkedin'])
        
    with open("resultado_twitter.md", "w", encoding="utf-8") as f:
        f.write(content['twitter'])
        
    print("\n✅ ¡Listo! Archivos guardados.")
    
    
if __name__ == "__main__":
    main()