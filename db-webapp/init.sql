-- Base de Datos para Aplicación Web (Incidencias)
-- Contenedor 2: DB WebApp

-- Tabla de estados de incidencias
CREATE TABLE IF NOT EXISTS incident_status (
    id SERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR(7)
);

-- Tabla de prioridades
CREATE TABLE IF NOT EXISTS priorities (
    id SERIAL PRIMARY KEY,
    priority_name VARCHAR(50) NOT NULL UNIQUE,
    level INTEGER NOT NULL,
    color VARCHAR(7)
);

-- Tabla principal de incidencias
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    username VARCHAR(50) NOT NULL,
    status_id INTEGER REFERENCES incident_status(id),
    priority_id INTEGER REFERENCES priorities(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_incidents_username ON incidents(username);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status_id);
CREATE INDEX IF NOT EXISTS idx_incidents_created ON incidents(created_at DESC);

-- Insertar estados predefinidos
INSERT INTO incident_status (status_name, description, color) VALUES
('Abierto', 'Incidencia reportada pero no asignada', '#dc3545'),
('En Progreso', 'Incidencia en proceso de resolución', '#ffc107'),
('Resuelto', 'Incidencia resuelta pendiente de cierre', '#28a745'),
('Cerrado', 'Incidencia completamente cerrada', '#6c757d')
ON CONFLICT (status_name) DO NOTHING;

-- Insertar prioridades predefinidas
INSERT INTO priorities (priority_name, level, color) VALUES
('Baja', 1, '#17a2b8'),
('Media', 2, '#ffc107'),
('Alta', 3, '#ff6b6b'),
('Crítica', 4, '#dc3545')
ON CONFLICT (priority_name) DO NOTHING;

-- Insertar incidencias de ejemplo
INSERT INTO incidents (title, description, username, status_id, priority_id) VALUES
('Error en servidor de correo', 'El servidor de correo no está enviando emails correctamente', 'admin', 1, 3),
('Actualización de sistema', 'Se requiere actualizar el sistema operativo de los servidores', 'admin', 2, 2),
('Problema con impresora', 'La impresora del piso 3 no está funcionando', 'admin', 3, 1)
ON CONFLICT DO NOTHING;
