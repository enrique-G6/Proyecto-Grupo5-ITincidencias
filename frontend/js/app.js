cat > frontend/js/app.js << 'EOFJS'
// Configuración global
const API_AUTH_URL = 'http://localhost:5001/api';

// Verificar autenticación
function checkAuth() {
    const user = localStorage.getItem('currentUser');
    const currentPath = window.location.pathname;
    
    // Si no hay usuario y no está en la página de login
    if (!user && currentPath !== '/index.html' && currentPath !== '/') {
        window.location.href = '/index.html';
        return null;
    }
    return user;
}

// Cerrar sesión
function logout() {
    if (confirm('¿Estás seguro de que deseas cerrar sesión?')) {
        localStorage.clear();
        window.location.href = '/index.html';
    }
}

// Obtener usuario actual
function getCurrentUser() {
    return localStorage.getItem('currentUser');
}

// Función para mostrar mensajes
function showMessage(message, type = 'info') {
    console.log(`[${type}] ${message}`);
}

console.log('✅ Sistema de Incidencias IT - Cargado correctamente');
EOFJS
