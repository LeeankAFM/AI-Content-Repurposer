from groq import Groq
import os

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
system_prompt = "Eres un experto en creación de contenido viral y marketing digital. Tu objetivo es transformar transcripciones de video en piezas de contenido de alto impacto."

def generate_content(transcription, platforms):
    
    results = {}
    
    print(f"--- Iniciando generación para: {platforms} ---")
    
    for platform in platforms:
        
        print(f" > Procesando: {platform}...")
        
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
            continue
           
        try: 
            response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7
            )  
            
            contenido_generado = response.choices[0].message.content
            results[platform] = contenido_generado
            print(f" ✅ {platform} generado con éxito.")
            
        except Exception as e:
            print(f" ❌ Error generando {platform}: {e}")
            results[platform] = "Error al generar contenido."
        
    return results