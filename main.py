from yt_dlp import YoutubeDL
from groq import Groq
import os
import transcriber

def main():
    
    url = input("Enter the URL: ")
    print("You entered:", url)
    text = transcriber.transcribe_url(url)
    print("text: ", text)
    
if __name__ == "__main__":
    main()