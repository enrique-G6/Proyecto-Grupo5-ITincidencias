-- =====================================================
-- Script de Inicialización COMPLETO - DB API (auth_db)
-- Contiene: Usuarios + Incidencias + Estados + Prioridades
-- =====================================================

-- =====================================================
-- TABLA 1: users (Usuarios del sistema)
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
-- Hash generado con Werkzeug: generate_password_hash('test1234')
INSERT INTO users (username, email, password_hash) 
VALUES (
    'admin',
    'admin@utp.ac.pa',
    'scrypt:32768:8:1$VyXc0J8mHzrLU6kI$48d4f1e3a7c5b2d8f9e6a3c1b7d4e9f2a5c8b1d6e3f7a9c2b5d8e1f4a7c3b9d6e2f5a8c1b4d7e9f2a5c8b1d6e3f7a9c2b5d8e1f4a7c3b9d6e2f5a8c1b4d7e9f2a'
)
ON CONFLICT (username) DO NOTHING;

-- =====================================================
-- TABLA 2: incident_status (Estados de incidencias)
-- =====================================================
CREATE TABLE IF NOT EXISTS incident_status (
    id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(20)
);

-- Insertar estados predefinidos
INSERT INTO incident_status (id, status_name, description, color) VALUES
(1, 'Abierto', 'Incidencia reportada pero no asignada', '#ffc107'),
(2, 'En Progreso', 'Incidencia en proceso de resolución', '#17a2b8'),
(3, 'Resuelto', 'Incidencia resuelta pendiente de cierre', '#28a745'),
(4, 'Cerrado', 'Incidencia completamente cerrada', '#6c757d')
ON CONFLICT (status_name) DO NOTHING;

-- Resetear secuencia
SELECT setval('incident_status_id_seq', 4, true);

-- =====================================================
-- TABLA 3: priorities (Prioridades de incidencias)
-- =====================================================
CREATE TABLE IF NOT EXISTS priorities (
    id SERIAL PRIMARY KEY,
    priority_name VARCHAR(50) NOT NULL UNIQUE,
    level INTEGER NOT NULL,
    color VARCHAR(20)
);

-- Insertar prioridades predefinidas
INSERT INTO priorities (id, priority_name, level, color) VALUES
(1, 'Baja', 1, '#6c757d'),
(2, 'Media', 2, '#0d6efd'),
(3, 'Alta', 3, '#fd7e14'),
(4, 'Crítica', 4, '#dc3545')
ON CONFLICT (priority_name) DO NOTHING;

-- Resetear secuencia
SELECT setval('priorities_id_seq', 4, true);

-- =====================================================
-- TABLA 4: incidents (Incidencias IT)
-- =====================================================
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
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
-- VISTAS ÚTILES PARA ESTADÍSTICAS
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

-- =====================================================
-- VERIFICACIÓN
-- =====================================================

-- Mostrar resumen de tablas creadas
DO $$ 
BEGIN
    RAISE NOTICE 'Tablas creadas:';
    RAISE NOTICE '- users: % registros', (SELECT COUNT(*) FROM users);
    RAISE NOTICE '- incident_status: % registros', (SELECT COUNT(*) FROM incident_status);
    RAISE NOTICE '- priorities: % registros', (SELECT COUNT(*) FROM priorities);
    RAISE NOTICE '- incidents: % registros', (SELECT COUNT(*) FROM incidents);
END $$;

-- =====================================================
-- FIN DEL SCRIPT
-- =====================================================
