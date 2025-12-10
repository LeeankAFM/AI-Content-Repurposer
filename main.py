from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from appwrite.client import Client
from appwrite.services.account import Account
from appwrite.services.databases import Databases
from appwrite.query import Query
from appwrite.id import ID
from datetime import datetime, timezone
import os
import uvicorn

import backend.transcriber as transcriber
import backend.generator as generator

app = FastAPI()

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*") 

app.mount("/static", StaticFiles(directory="static"), name="static") 

# Configurar Templates
templates = Jinja2Templates(directory="templates")

# --- CONFIG APPWRITE ---
APPWRITE_ENDPOINT = os.environ.get("APPWRITE_ENDPOINT")
APPWRITE_PROJECT_ID = os.environ.get("APPWRITE_PROJECT_ID")
APPWRITE_DB_ID = os.environ.get("APPWRITE_DATABASE_ID")
APPWRITE_COL_ID = os.environ.get("APPWRITE_COLLECTION_ID")

# Nombre único de cookie
COOKIE_NAME = "session_ai_repurposer_v2"

def get_appwrite_client(session_id: str = None):
    client = Client()
    client.set_endpoint(APPWRITE_ENDPOINT)
    client.set_project(APPWRITE_PROJECT_ID)
    if session_id:
        client.set_session(session_id)
    return client

# --- MIDDLEWARE & UTILS ---

async def get_current_user(request: Request):
    session_id = request.cookies.get(COOKIE_NAME)
    
    # DEBUG: Ver si llega la cookie ahora
    if not session_id:
        # print(f"⚠️ Debug: Cookies recibidas: {request.cookies}", flush=True)
        return None
    
    try:
        client = get_appwrite_client(session_id)
        account = Account(client)
        user = account.get()
        user['client'] = client
        return user
    except Exception as e:
        print(f"❌ Error verificando usuario: {e}", flush=True)
        return None

def check_limit(user_id, client):
    databases = Databases(client)
    try:
        # Check Plan
        account = Account(client)
        prefs = account.get_prefs()
        plan = prefs.get('plan', 'free')
        limit = 50 if plan == 'pro' else 3

        # Check Count
        today_start = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00.000+00:00")
        result = databases.list_documents(
            database_id=APPWRITE_DB_ID,
            collection_id=APPWRITE_COL_ID,
            queries=[
                Query.equal("user_id", user_id),
                Query.greater_than("$createdAt", today_start)
            ]
        )
        return True, result['total'], limit
    except Exception as e:
        print(f"Error checking limit: {e}")
        return True, 0, 3

# --- RUTAS ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    user = await get_current_user(request)
    if user:
        return RedirectResponse("/dashboard")
    return templates.TemplateResponse("auth.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    # NOTA: Importante no pasar session_id aquí para que sea un cliente limpio
    client = get_appwrite_client()
    account = Account(client)
    
    try:
        # 1. Crear sesión
        session = account.create_email_password_session(email, password)
        
        secret = None
        
        # 2. Intento estándar (Body del JSON)
        if isinstance(session, dict) and session.get('secret'):
            secret = session.get('secret')
        elif hasattr(session, 'secret') and session.secret:
            secret = session.secret

        # 3. SI FALLA EL BODY, BUSCAMOS EN EL CLIENTE (EL FIX)
        if not secret:
            print("⚠️ Secret vacío en body. Iniciando inspección profunda...", flush=True)
            
            # --- INSPECCIÓN DE ATRIBUTOS (Para ver en los logs) ---
            # Esto imprimirá qué variables tiene tu cliente disponibles
            print(f"🔍 ESTRUCTURA CLIENTE: {dir(client)}", flush=True)
            # ------------------------------------------------------

            # Probamos las ubicaciones más comunes de las cookies en Python
            candidates = [
                getattr(client, 'http', None),       # Versiones modernas
                getattr(client, '_http', None),      # Versiones antiguas
                getattr(client, 'session', None),    # Requests directo
                getattr(client, '_session', None)    # Requests privado
            ]

            for i, candidate in enumerate(candidates):
                if candidate:
                    try:
                        # Intentamos sacar las cookies de este candidato
                        cookies = candidate.cookies.get_dict()
                        print(f"🔎 Buscando en candidato {i}: {cookies}", flush=True)
                        for key, value in cookies.items():
                            if key.startswith('a_session_'):
                                secret = value
                                print(f"✅ ¡ENCONTRADO! Secret en candidato {i}", flush=True)
                                break
                    except Exception as e:
                        print(f"⚠️ Candidato {i} falló: {e}", flush=True)
                
                if secret: break

        # 4. Verificación final
        if not secret:
             print("❌ FATAL: No se encontró el secret en ningún lado.", flush=True)
             raise Exception("Error de autenticación: No se recibió el token de sesión.")

        # 5. Respuesta exitosa
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(
            key=COOKIE_NAME, 
            value=secret,
            httponly=True, 
            samesite="lax",
            secure=True,
            path="/"
        )
        return response

    except Exception as e:
        print(f"❌ Login Exception: {e}", flush=True)
        return templates.TemplateResponse("auth.html", {"request": request, "error": f"Error: {str(e)}"})

@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, email: str = Form(...), password: str = Form(...)):
    client = get_appwrite_client()
    account = Account(client)
    try:
        account.create(ID.unique(), email, password)
        session = account.create_email_password_session(email, password)
        
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        if hasattr(session, 'secret'):
            # Si es un Objeto (SDK nuevo)
            secret = session.secret
        elif isinstance(session, dict):
            # Si es un Diccionario (SDK viejo)
            secret = session.get('secret')
        else:
            # Fallback raro (tuplas o algo inesperado)
            secret = str(session) 
        
        response.set_cookie(
            key=COOKIE_NAME, 
            value=secret, 
            httponly=True, 
            samesite="lax",
            secure=True,
            path="/"
        )
        return response
    except Exception as e:
        return templates.TemplateResponse("auth.html", {"request": request, "error": f"Error: {str(e)}"})

@app.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get(COOKIE_NAME)
    if session_id:
        try:
            client = get_appwrite_client(session_id)
            account = Account(client)
            account.delete_session('current')
        except:
            pass
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(COOKIE_NAME)
    return response

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/")
    
    can_proceed, usage, limit = check_limit(user['$id'], user['client'])
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": user,
        "usage_count": usage,
        "limit": limit
    })

@app.post("/api/process")
async def process_video(
    request: Request,
    urls: str = Form(...),
    linkedin: str = Form("false"),
    twitter: str = Form("false")
):
    user = await get_current_user(request)
    if not user:
        return JSONResponse({"error": "No autorizado"}, status_code=401)

    do_linkedin = linkedin == "true"
    do_twitter = twitter == "true"
    
    can_proceed, usage, limit = check_limit(user['$id'], user['client'])
    url_list = [line.strip() for line in urls.split('\n') if line.strip()]
    
    if usage + len(url_list) > limit:
         return JSONResponse({"error": f"Límite excedido. Te quedan {limit - usage} videos."}, status_code=400)

    try:
        full_transcription = ""
        databases = Databases(user['client'])

        for i, url in enumerate(url_list):
            text = transcriber.transcribe_url(url, index=i)
            full_transcription += f"\n\n--- VIDEO {i+1} ---\n{text}"
            
            databases.create_document(
                database_id=APPWRITE_DB_ID,
                collection_id=APPWRITE_COL_ID,
                document_id=ID.unique(),
                data={"user_id": user['$id'], "video_url": url}
            )

        platforms = []
        if do_linkedin: platforms.append("linkedin")
        if do_twitter: platforms.append("twitter")
        
        content = generator.generate_content(full_transcription[:25000], platforms)
        
        return JSONResponse(content)
        
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
    
@app.get("/diagnostico")
async def diagnostico(request: Request):
    """Ruta para detectar por qué falla el login"""
    results = {
        "1_cookies_recibidas": request.cookies,
        "2_cookie_esperada": COOKIE_NAME,
        "3_tiene_cookie_sesion": COOKIE_NAME in request.cookies,
        "4_endpoint_appwrite": APPWRITE_ENDPOINT,
        "5_prueba_conexion": "Pendiente..."
    }

    # Intentar verificar cookie
    session_id = request.cookies.get(COOKIE_NAME)
    if session_id:
        results["session_id_oculto"] = session_id[:5] + "..."
        try:
            client = get_appwrite_client(session_id)
            account = Account(client)
            user = account.get()
            results["5_prueba_conexion"] = f"✅ ÉXITO: Usuario es {user.get('email', 'Desconocido')}"
        except Exception as e:
            results["5_prueba_conexion"] = f"❌ ERROR CONEXIÓN: {str(e)}"
    else:
        results["5_prueba_conexion"] = "⚠️ No se puede probar conexión sin cookie"

    return JSONResponse(results)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8501, reload=True, proxy_headers=True, forwarded_allow_ips="*")