# API de Autenticación Simple - Basada en REST-auth de Miguel Grinberg
# Adaptada para el Sistema de Gestión de Incidencias IT

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 
    'postgresql://auth_user:auth_pass_2024@db-api:5432/auth_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')

db = SQLAlchemy(app)

# Modelo de Usuario
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash de contraseña simple"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Crear tablas al iniciar
with app.app_context():
    db.create_all()

# ============== ENDPOINTS ==============

@app.route('/')
def index():
    """Endpoint raíz"""
    return jsonify({
        'message': 'API de Autenticación - Sistema de Incidencias IT',
        'version': '1.0',
        'endpoints': {
            'register': 'POST /api/register',
            'login': 'POST /api/login',
            'user': 'GET /api/user/<username>',
            'health': 'GET /api/health'
        }
    })

@app.route('/api/health')
def health():
    """Health check"""
    try:
        # Verificar conexión a BD
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Registrar nuevo usuario"""
    try:
        data = request.get_json()
        
        # Validaciones
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username y password son requeridos'}), 400
        
        username = data.get('username').strip()
        password = data.get('password')
        email = data.get('email', f"{username}@example.com").strip()
        
        # Validar longitud
        if len(username) < 3:
            return jsonify({'error': 'Username debe tener al menos 3 caracteres'}), 400
        
        if len(password) < 4:
            return jsonify({'error': 'Password debe tener al menos 4 caracteres'}), 400
        
        # Verificar si ya existe
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'El username ya existe'}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'El email ya está registrado'}), 409
        
        # Crear usuario
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuario creado exitosamente',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al crear usuario: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login de usuario"""
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username y password son requeridos'}), 400
        
        username = data.get('username').strip()
        password = data.get('password')
        
        # Buscar usuario
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        # Verificar password
        if not user.check_password(password):
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        return jsonify({
            'message': 'Login exitoso',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error en login: {str(e)}'}), 500

@app.route('/api/user/<username>', methods=['GET'])
def get_user(username):
    """Obtener información de usuario"""
    try:
        user = User.query.filter_by(username=username).first()
        
        if not user:
            return jsonify({'exists': False}), 404
        
        return jsonify({
            'exists': True,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error al buscar usuario: {str(e)}'}), 500

@app.route('/api/users', methods=['GET'])
def list_users():
    """Listar todos los usuarios (para debug)"""
    try:
        users = User.query.all()
        return jsonify({
            'count': len(users),
            'users': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Manejador de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
