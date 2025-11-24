-- Base de Datos para API de Autenticación
-- Contenedor 4: DB API

-- Crear tabla de usuarios (será creada por SQLAlchemy, pero la definimos por si acaso)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Insertar usuario de prueba (password: test1234)
INSERT INTO users (username, email, password_hash) VALUES 
('admin', 'admin@incidencias.com', 'scrypt:32768:8:1$zX7Y9wB2vA3cD4eF$1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef')
ON CONFLICT (username) DO NOTHING;

