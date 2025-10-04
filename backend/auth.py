from flask import Blueprint, request, jsonify
from flask_bcrypt import Bcrypt
import mysql.connector
from mysql.connector import Error
import secrets
import string
import os

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# MySQL Configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'database': os.getenv('DB_DATABASE', 'minemind'),
    'user': os.getenv('DB_USER', 'user'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

# Database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Initialize auth tables
def init_auth_db():
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(200),
                role VARCHAR(50) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                INDEX idx_password (password(50))
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("✓ Auth database initialized successfully")

# Generate secure random password
def generate_password(length=12):
    """Generate a random password with letters and numbers"""
    characters = string.ascii_letters + string.digits
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password

# Routes
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validation - now password is NOT required
    required_fields = ['username', 'email', 'full_name']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    username = data['username']
    email = data['email']
    full_name = data['full_name']
    
    # Generate random password
    generated_password = generate_password(12)
    
    # Hash password for storage
    hashed_password = bcrypt.generate_password_hash(generated_password).decode('utf-8')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, email, password, full_name) VALUES (%s, %s, %s, %s)',
            (username, email, hashed_password, full_name)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Return the generated password to user (ONLY TIME IT'S SHOWN!)
        return jsonify({
            'message': 'User registered successfully',
            'password': generated_password,
            'warning': 'Save this password! It will not be shown again.'
        }), 201
    
    except mysql.connector.IntegrityError:
        return jsonify({'message': 'Username or email already exists'}), 409
    except Error as e:
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Only password is required for login
    if not data or not data.get('password'):
        return jsonify({'message': 'Password is required'}), 400
    
    password = data['password']
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        # Find user by checking password against all hashed passwords
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        
        authenticated_user = None
        for user in users:
            if bcrypt.check_password_hash(user['password'], password):
                authenticated_user = user
                break
        
        if authenticated_user:
            # Update last login
            cursor.execute('UPDATE users SET last_login = NOW() WHERE id = %s', (authenticated_user['id'],))
            conn.commit()
            cursor.close()
            conn.close()
            
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': authenticated_user['id'],
                    'username': authenticated_user['username'],
                    'email': authenticated_user['email'],
                    'full_name': authenticated_user['full_name'],
                    'role': authenticated_user['role']
                }
            }), 200
        
        cursor.close()
        conn.close()
        return jsonify({'message': 'Invalid password'}), 401
    
    except Error as e:
        return jsonify({'message': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['POST'])
def get_profile():
    """Get profile using password (no JWT needed)"""
    data = request.get_json()
    
    if not data or not data.get('password'):
        return jsonify({'message': 'Password is required'}), 400
    
    password = data['password']
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection failed'}), 500
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        
        authenticated_user = None
        for user in users:
            if bcrypt.check_password_hash(user['password'], password):
                authenticated_user = user
                break
        
        cursor.close()
        conn.close()
        
        if authenticated_user:
            # Remove password from response
            del authenticated_user['password']
            return jsonify({'user': authenticated_user}), 200
        
        return jsonify({'message': 'Invalid password'}), 401
    
    except Error as e:
        return jsonify({'message': f'Error fetching profile: {str(e)}'}), 500

# Function to register auth blueprint
def register_auth_routes(app):
    """Register authentication routes with Flask app"""
    bcrypt.init_app(app)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    init_auth_db()
    print("✓ Password-only authentication routes registered at /api/auth/*")