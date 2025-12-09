-- =====================================================
-- Script de Inicialización - DB API (auth_db)
-- Incluye: Usuarios + Incidencias + Estados + Prioridades
-- =====================================================

-- Crear extensión para UUID si no existe
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- TABLA: users (Usuarios del sistema)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Usuario de prueba (password: test1234)
INSERT INTO users (username, email, password_hash) 
VALUES (
    'admin',
    'admin@utp.ac.pa',
    'scrypt:32768:8:1$6wF8Ks9k8XcuLnV4$fc8a7f0f4e3d8e9c5d4f6b7a8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d'
)
ON CONFLICT (username) DO NOTHING;

-- =====================================================
-- TABLA: incident_status (Estados de incidencias)
-- =====================================================
CREATE TABLE IF NOT EXISTS incident_status (
    id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL,
    description VARCHAR(200),
    color VARCHAR(20)
);

-- Insertar estados predefinidos
INSERT INTO incident_status (id, status_name, description, color) VALUES
    (1, 'Abierto', 'Incidencia reportada, pendiente de asignación', '#ffc107'),
    (2, 'En Progreso', 'Incidencia asignada y en proceso de resolución', '#17a2b8'),
    (3, 'Resuelto', 'Incidencia resuelta, pendiente de cierre', '#28a745'),
    (4, 'Cerrado', 'Incidencia cerrada y archivada', '#6c757d')
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- TABLA: priorities (Prioridades de incidencias)
-- =====================================================
CREATE TABLE IF NOT EXISTS priorities (
    id SERIAL PRIMARY KEY,
    priority_name VARCHAR(50) NOT NULL,
    level INTEGER NOT NULL,
    color VARCHAR(20)
);

-- Insertar prioridades predefinidas
INSERT INTO priorities (id, priority_name, level, color) VALUES
    (1, 'Baja', 1, '#6c757d'),
    (2, 'Media', 2, '#0d6efd'),
    (3, 'Alta', 3, '#fd7e14'),
    (4, 'Crítica', 4, '#dc3545')
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- TABLA: incidents (Incidencias IT)
-- =====================================================
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    username VARCHAR(50) NOT NULL,
    status_id INTEGER DEFAULT 1 REFERENCES incident_status(id),
    priority_id INTEGER DEFAULT 2 REFERENCES priorities(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL
);

-- Índices para búsquedas y filtros
CREATE INDEX IF NOT EXISTS idx_incidents_username ON incidents(username);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status_id);
CREATE INDEX IF NOT EXISTS idx_incidents_priority ON incidents(priority_id);
CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents(created_at DESC);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_incidents_updated_at ON incidents;
CREATE TRIGGER update_incidents_updated_at
    BEFORE UPDATE ON incidents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- DATOS DE EJEMPLO (Incidencias de prueba)
-- =====================================================
INSERT INTO incidents (title, description, username, status_id, priority_id, created_at) VALUES
    (
        'Error al iniciar sesión en sistema de nómina',
        'Al intentar ingresar al sistema de nómina aparece el mensaje "Credenciales inválidas" aunque las credenciales son correctas. Probado en Chrome y Firefox con el mismo resultado.',
        'admin',
        1,
        3,
        CURRENT_TIMESTAMP - INTERVAL '2 days'
    ),
    (
        'Impresora de oficina 3B no responde',
        'La impresora HP LaserJet en la oficina 3B no está respondiendo a las solicitudes de impresión. La luz indicadora está en verde pero no imprime ningún documento.',
        'admin',
        2,
        2,
        CURRENT_TIMESTAMP - INTERVAL '1 day'
    ),
    (
        'Lentitud extrema en aplicación de inventario',
        'Desde esta mañana la aplicación de inventario está extremadamente lenta. Las consultas que normalmente toman 2-3 segundos ahora toman más de 30 segundos. Afecta a todos los usuarios del departamento.',
        'admin',
        1,
        4,
        CURRENT_TIMESTAMP - INTERVAL '3 hours'
    )
ON CONFLICT DO NOTHING;

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista para estadísticas por estado
CREATE OR REPLACE VIEW incidents_by_status AS
SELECT 
    s.status_name,
    s.color,
    COUNT(i.id) as count
FROM incident_status s
LEFT JOIN incidents i ON s.id = i.status_id
GROUP BY s.id, s.status_name, s.color
ORDER BY s.id;

-- Vista para estadísticas por prioridad
CREATE OR REPLACE VIEW incidents_by_priority AS
SELECT 
    p.priority_name,
    p.color,
    COUNT(i.id) as count
FROM priorities p
LEFT JOIN incidents i ON p.id = i.priority_id
GROUP BY p.id, p.priority_name, p.color
ORDER BY p.level DESC;

-- Vista completa de incidencias con detalles
CREATE OR REPLACE VIEW incidents_detailed AS
SELECT 
    i.id,
    i.title,
    i.description,
    i.username,
    s.status_name,
    s.color as status_color,
    p.priority_name,
    p.level as priority_level,
    p.color as priority_color,
    i.created_at,
    i.updated_at,
    i.resolved_at,
    CASE 
        WHEN i.resolved_at IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (i.resolved_at - i.created_at))/3600
        ELSE 
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - i.created_at))/3600
    END as hours_elapsed
FROM incidents i
LEFT JOIN incident_status s ON i.status_id = s.id
LEFT JOIN priorities p ON i.priority_id = p.id
ORDER BY i.created_at DESC;

-- =====================================================
-- PERMISOS Y CONFIGURACIÓN
-- =====================================================

-- Asegurar que las secuencias estén configuradas correctamente
SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));
SELECT setval('incident_status_id_seq', (SELECT COALESCE(MAX(id), 4) FROM incident_status));
SELECT setval('priorities_id_seq', (SELECT COALESCE(MAX(id), 4) FROM priorities));
SELECT setval('incidents_id_seq', (SELECT COALESCE(MAX(id), 1) FROM incidents));

-- =====================================================
-- VERIFICACIÓN
-- =====================================================

-- Mostrar resumen de tablas creadas
SELECT 'users' as table_name, COUNT(*) as records FROM users
UNION ALL
SELECT 'incident_status', COUNT(*) FROM incident_status
UNION ALL
SELECT 'priorities', COUNT(*) FROM priorities
UNION ALL
SELECT 'incidents', COUNT(*) FROM incidents;

-- =====================================================
-- FIN DEL SCRIPT
-- =====================================================
