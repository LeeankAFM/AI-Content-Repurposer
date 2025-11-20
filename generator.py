from groq import Groq
import os

# Inicializa el cliente (igual que antes)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
system_prompt = "Eres un experto en creación de contenido viral y marketing digital. Tu objetivo es transformar transcripciones de video en piezas de contenido de alto impacto."

def generate_content(transcription):
    
    format_type = ["twitter"]
    
    results = {}
    for format in format_type:
        
        print(f" > Procesando: {format}...") # Debug para saber que entró al bucle
        
        prompt = ""
        
        if format == "linkedin":
            prompt = f"""
            Crea un post profesional para LinkedIn basado en la siguiente transcripción.
            Reglas:
            - Usa un gancho fuerte al principio.
            - Usa listas (bullet points) para las ideas clave.
            - Tono: Profesional pero cercano.
            - Incluye una llamada a la acción al final.
            - No uses hashtags excesivos (máximo 3).
            
            Transcripción:
            {transcription}
            """
        elif format == "twitter":
            prompt = f"""
            Crea un hilo de Twitter (X) basado en esta transcripción.
            Reglas:
            - Separa los tweets con "---".
            - El primer tweet debe ser extremadamente llamativo.
            - Máximo 280 caracteres por tweet (hazlo corto y conciso).
            
            Transcripción:
            {transcription}
            """
        if not prompt:
            print(f"⚠️ Error: No se definió prompt para {format}")
            continue
           
        try: 
            response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7 # Creatividad media
            )  
            
            contenido_generado = response.choices[0].message.content
            results[format] = contenido_generado
            print(f" ✅ {format} generado con éxito.")
            
        except Exception as e:
            print(f" ❌ Error generando {format}: {e}")
            results[format] = "Error al generar contenido."
        
    return results