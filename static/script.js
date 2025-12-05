/* --- LÓGICA DE AUTENTICACIÓN (LOGIN/REGISTER) --- */
let isLogin = true;

function toggleMode() {
    const form = document.getElementById('authForm');
    const btn = document.getElementById('submitBtn');
    const link = document.getElementById('toggleLink');
    const text = document.getElementById('toggleText');

    if (!form) return; // Si no existe el formulario, no hacemos nada

    isLogin = !isLogin;
    if (isLogin) {
        form.action = "/login";
        btn.textContent = "Iniciar Sesión";
        text.textContent = "¿No tienes cuenta?";
        link.textContent = "Crear cuenta gratis";
    } else {
        form.action = "/register";
        btn.textContent = "Registrarse";
        text.textContent = "¿Ya tienes cuenta?";
        link.textContent = "Inicia sesión aquí";
    }
}

/* --- LÓGICA DEL DASHBOARD (GENERAR CONTENIDO) --- */
async function generateContent() {
    const urlsInput = document.getElementById('urls');
    
    // Si no estamos en el dashboard, detenemos la ejecución
    if (!urlsInput) return;

    const urls = urlsInput.value;
    const linkedin = document.getElementById('linkedin').checked;
    const twitter = document.getElementById('twitter').checked;
    const generateBtn = document.getElementById('generateBtn');
    
    if (!urls.trim()) { alert("Ingresa al menos una URL"); return; }
    if (!linkedin && !twitter) { alert("Selecciona una plataforma"); return; }

    // Actualizar UI (Mostrar Spinner)
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Procesando...';
    
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('resultsArea').classList.add('hidden');
    document.getElementById('loader').classList.remove('hidden');

    try {
        const formData = new FormData();
        formData.append('urls', urls);
        formData.append('linkedin', linkedin);
        formData.append('twitter', twitter);

        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) throw new Error(data.error);

        // Mostrar Resultados
        document.getElementById('loader').classList.add('hidden');
        document.getElementById('resultsArea').classList.remove('hidden');

        if (data.linkedin) {
            document.getElementById('resLinkedin').classList.remove('hidden');
            document.getElementById('txtLinkedin').textContent = data.linkedin;
        }
        if (data.twitter) {
            document.getElementById('resTwitter').classList.remove('hidden');
            document.getElementById('txtTwitter').textContent = data.twitter;
        }

        // Opcional: Recargar página suavemente para actualizar contadores
        // location.reload(); 

    } catch (e) {
        alert("Error: " + e.message);
        document.getElementById('loader').classList.add('hidden');
        document.getElementById('emptyState').classList.remove('hidden');
    } finally {
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Generar Contenido';
    }
}

/* --- UTILIDADES --- */
function copyToClipboard(id) {
    const element = document.getElementById(id);
    if(element) {
        navigator.clipboard.writeText(element.textContent);
        // Podrías usar una librería de notificaciones tipo Toastify aquí
        alert("¡Copiado al portapapeles!");
    }
}