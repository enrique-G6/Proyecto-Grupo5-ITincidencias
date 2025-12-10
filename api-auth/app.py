from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)

# Configuración
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 
    'postgresql://auth_user:auth_pass_2024@172.30.1.20:5432/auth_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')

# Configuración CORS para permitir peticiones desde el frontend
CORS(app, resources={r"/api/*": {"origins": "*"}})

db = SQLAlchemy(app)

# =============================================================================
# MODELOS DE BASE DE DATOS
# =============================================================================

class User(db.Model):
    """Modelo de Usuario (en DB API - auth_db)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # ← AGREGADO: Campo role
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Genera hash de la contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica la contraseña"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convierte el usuario a diccionario"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,  # ← AGREGADO: Incluir role en respuesta
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Configuración para segunda base de datos (DB WebApp - incidents_db)
# Nota: Flask-SQLAlchemy no soporta múltiples bases de datos fácilmente
# Por simplicidad, vamos a usar la misma DB para el 50% del proyecto
# En producción, deberías separar las conexiones

class IncidentStatus(db.Model):
    """Estados de incidencias"""
    __tablename__ = 'incident_status'
    
    id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    color = db.Column(db.String(20))


class Priority(db.Model):
    """Prioridades de incidencias"""
    __tablename__ = 'priorities'
    
    id = db.Column(db.Integer, primary_key=True)
    priority_name = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer)
    color = db.Column(db.String(20))


class Incident(db.Model):
    """Modelo de Incidencia"""
    __tablename__ = 'incidents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    username = db.Column(db.String(50), nullable=False, index=True)
    status_id = db.Column(db.Integer, db.ForeignKey('incident_status.id'), default=1)
    priority_id = db.Column(db.Integer, db.ForeignKey('priorities.id'), default=2)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    status = db.relationship('IncidentStatus', backref='incidents')
    priority = db.relationship('Priority', backref='incidents')
    
    def to_dict(self):
        """Convierte la incidencia a diccionario"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'username': self.username,
            'status': {
                'id': self.status.id,
                'name': self.status.status_name,
                'color': self.status.color
            } if self.status else None,
            'priority': {
                'id': self.priority.id,
                'name': self.priority.priority_name,
                'level': self.priority.level,
                'color': self.priority.color
            } if self.priority else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


# =============================================================================
# ENDPOINTS DE AUTENTICACIÓN (YA EXISTENTES)
# =============================================================================

@app.route('/')
def index():
    """Información de la API"""
    return jsonify({
        'name': 'API de Gestión de Incidencias IT',
        'version': '2.0',
        'description': 'API REST para autenticación y gestión de incidencias',
        'endpoints': {
            'auth': {
                'POST /api/register': 'Registrar nuevo usuario',
                'POST /api/login': 'Iniciar sesión',
                'GET /api/user/<username>': 'Verificar si usuario existe',
                'GET /api/users': 'Listar todos los usuarios (debug)'
            },
            'incidents': {
                'GET /api/incidents': 'Listar todas las incidencias',
                'GET /api/incidents/<id>': 'Obtener incidencia específica',
                'POST /api/incidents': 'Crear nueva incidencia',
                'PUT /api/incidents/<id>': 'Actualizar incidencia',
                'DELETE /api/incidents/<id>': 'Eliminar incidencia',
                'GET /api/incidents/user/<username>': 'Incidencias de un usuario',
                'GET /api/incidents/stats': 'Estadísticas de incidencias'
            },
            'metadata': {
                'GET /api/statuses': 'Listar estados disponibles',
                'GET /api/priorities': 'Listar prioridades disponibles'
            }
        }
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Verificar conexión a base de datos
        db.session.execute(db.text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'version': '2.0'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500


@app.route('/api/register', methods=['POST'])
def register():
    """Registrar nuevo usuario"""
    try:
        data = request.get_json()
        
        # Validaciones
        if not data.get('username') or not data.get('password') or not data.get('email'):
            return jsonify({'error': 'Faltan campos requeridos'}), 400
        
        if len(data['username']) < 3:
            return jsonify({'error': 'El usuario debe tener al menos 3 caracteres'}), 400
        
        if len(data['password']) < 4:
            return jsonify({'error': 'La contraseña debe tener al menos 4 caracteres'}), 400
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'El usuario ya existe'}), 409
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'El email ya está registrado'}), 409
        
        # Crear nuevo usuario
        user = User(username=data['username'], email=data['email'])
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Usuario creado exitosamente',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """Iniciar sesión"""
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Faltan credenciales'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Credenciales inválidas'}), 401
        
        return jsonify({
            'message': 'Login exitoso',
            'user': user.to_dict()  # Ahora incluye 'role'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/<username>', methods=['GET'])
def check_user(username):
    """Verificar si un usuario existe"""
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({
            'exists': True,
            'user': user.to_dict()
        })
    return jsonify({'exists': False}), 404


@app.route('/api/users', methods=['GET'])
def list_users():
    """Listar todos los usuarios (solo para desarrollo/debug)"""
    users = User.query.all()
    return jsonify({
        'count': len(users),
        'users': [user.to_dict() for user in users]
    })


# =============================================================================
# ENDPOINTS DE INCIDENCIAS (NUEVO - 50% RESTANTE)
# =============================================================================

@app.route('/api/incidents', methods=['GET'])
def list_incidents():
    """Listar incidencias con filtros opcionales"""
    try:
        # Obtener parámetros de consulta
        username = request.args.get('username')
        status_id = request.args.get('status_id')
        priority_id = request.args.get('priority_id')
        
        # Construir query
        query = Incident.query
        
        if username:
            query = query.filter_by(username=username)
        if status_id:
            query = query.filter_by(status_id=int(status_id))
        if priority_id:
            query = query.filter_by(priority_id=int(priority_id))
        
        # Ordenar por fecha de creación (más recientes primero)
        incidents = query.order_by(Incident.created_at.desc()).all()
        
        return jsonify({
            'count': len(incidents),
            'incidents': [incident.to_dict() for incident in incidents]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/incidents/<int:incident_id>', methods=['GET'])
def get_incident(incident_id):
    """Obtener una incidencia específica"""
    try:
        incident = Incident.query.get(incident_id)
        
        if not incident:
            return jsonify({'error': 'Incidencia no encontrada'}), 404
        
        return jsonify(incident.to_dict())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/incidents', methods=['POST'])
def create_incident():
    """Crear nueva incidencia"""
    try:
        data = request.get_json()
        
        # Validaciones
        if not data.get('title'):
            return jsonify({'error': 'El título es requerido'}), 400
        
        if not data.get('username'):
            return jsonify({'error': 'El usuario es requerido'}), 400
        
        # Crear incidencia
        incident = Incident(
            title=data['title'],
            description=data.get('description', ''),
            username=data['username'],
            status_id=data.get('status_id', 1),  # 1 = Abierto por defecto
            priority_id=data.get('priority_id', 2)  # 2 = Media por defecto
        )
        
        db.session.add(incident)
        db.session.commit()
        
        return jsonify({
            'message': 'Incidencia creada exitosamente',
            'incident': incident.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/incidents/<int:incident_id>', methods=['PUT'])
def update_incident(incident_id):
    """Actualizar una incidencia"""
    try:
        incident = Incident.query.get(incident_id)
        
        if not incident:
            return jsonify({'error': 'Incidencia no encontrada'}), 404
        
        data = request.get_json()
        
        # Actualizar campos
        if 'title' in data:
            incident.title = data['title']
        if 'description' in data:
            incident.description = data['description']
        if 'status_id' in data:
            incident.status_id = data['status_id']
            # Si se marca como resuelto, guardar fecha
            if data['status_id'] == 3:  # 3 = Resuelto
                incident.resolved_at = datetime.utcnow()
        if 'priority_id' in data:
            incident.priority_id = data['priority_id']
        
        incident.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Incidencia actualizada exitosamente',
            'incident': incident.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/incidents/<int:incident_id>', methods=['DELETE'])
def delete_incident(incident_id):
    """Eliminar una incidencia"""
    try:
        incident = Incident.query.get(incident_id)
        
        if not incident:
            return jsonify({'error': 'Incidencia no encontrada'}), 404
        
        db.session.delete(incident)
        db.session.commit()
        
        return jsonify({'message': 'Incidencia eliminada exitosamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/incidents/user/<username>', methods=['GET'])
def get_user_incidents(username):
    """Obtener todas las incidencias de un usuario"""
    try:
        incidents = Incident.query.filter_by(username=username)\
            .order_by(Incident.created_at.desc()).all()
        
        return jsonify({
            'count': len(incidents),
            'username': username,
            'incidents': [incident.to_dict() for incident in incidents]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/incidents/stats', methods=['GET'])
def get_incident_stats():
    """Obtener estadísticas de incidencias"""
    try:
        # Total de incidencias
        total = Incident.query.count()
        
        # Por estado
        by_status = db.session.query(
            IncidentStatus.status_name,
            db.func.count(Incident.id)
        ).join(Incident).group_by(IncidentStatus.status_name).all()
        
        # Por prioridad
        by_priority = db.session.query(
            Priority.priority_name,
            db.func.count(Incident.id)
        ).join(Incident).group_by(Priority.priority_name).all()
        
        return jsonify({
            'total': total,
            'by_status': [{'name': name, 'count': count} for name, count in by_status],
            'by_priority': [{'name': name, 'count': count} for name, count in by_priority]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# ENDPOINTS DE METADATA
# =============================================================================

@app.route('/api/statuses', methods=['GET'])
def list_statuses():
    """Listar estados disponibles"""
    try:
        statuses = IncidentStatus.query.all()
        return jsonify({
            'count': len(statuses),
            'statuses': [{
                'id': s.id,
                'name': s.status_name,
                'description': s.description,
                'color': s.color
            } for s in statuses]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/priorities', methods=['GET'])
def list_priorities():
    """Listar prioridades disponibles"""
    try:
        priorities = Priority.query.all()
        return jsonify({
            'count': len(priorities),
            'priorities': [{
                'id': p.id,
                'name': p.priority_name,
                'level': p.level,
                'color': p.color
            } for p in priorities]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# =============================================================================
# MANEJO DE ERRORES
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Recurso no encontrado'}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Error interno del servidor'}), 500


# =============================================================================
# INICIALIZACIÓN
# =============================================================================

# Crear tablas al iniciar (solo para desarrollo)
with app.app_context():
    db.create_all()
    print("✅ Tablas creadas/verificadas")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
