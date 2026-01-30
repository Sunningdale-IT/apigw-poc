import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource, fields, Namespace
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)

# API Key Configuration
# Multiple API keys can be configured as comma-separated values
API_KEYS_RAW = os.environ.get('API_KEYS', '')
API_KEYS = set(key.strip() for key in API_KEYS_RAW.split(',') if key.strip())
API_KEY_REQUIRED = os.environ.get('API_KEY_REQUIRED', 'true').lower() == 'true'

# Authorizations for Swagger UI
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'X-API-Key',
        'description': 'API key for authentication. Pass in the X-API-Key header.'
    }
}

# Configure Flask-RESTX API with Swagger
api = Api(
    app,
    version='1.1',
    title='Dogcatcher API',
    description='API for exporting and managing caught dog data. Requires API key authentication via X-API-Key header.',
    doc='/api/docs',
    prefix='/api',
    authorizations=authorizations,
    security='apikey'
)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://dogcatcher:dogcatcher123@db:5432/dogcatcher')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/app/static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

def allowed_file(filename):
    """Check if file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def require_api_key(f):
    """Decorator to require API key for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not API_KEY_REQUIRED:
            return f(*args, **kwargs)
        
        if not API_KEYS:
            # No API keys configured, deny all requests
            api.abort(500, 'API key authentication is enabled but no API keys are configured')
        
        # Check for API key in header
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            api.abort(401, 'API key is required. Please provide X-API-Key header.')
        
        if api_key not in API_KEYS:
            api.abort(403, 'Invalid API key')
        
        return f(*args, **kwargs)
    return decorated_function

def validate_coordinates(latitude, longitude):
    """Validate GPS coordinates are within valid ranges"""
    return -90 <= latitude <= 90 and -180 <= longitude <= 180

# Database model for dogs
class Dog(db.Model):
    __tablename__ = 'dogs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    photo_filename = db.Column(db.String(255))
    comments = db.Column(db.Text)
    caught_date = db.Column(db.DateTime, default=lambda: datetime.datetime.utcnow())
    
    def __repr__(self):
        return f'<Dog {self.name}>'

# Create tables
with app.app_context():
    db.create_all()

# API Namespace
ns = Namespace('dogs', description='Dog operations')
api.add_namespace(ns)

# API Models for Swagger documentation
dog_model = api.model('Dog', {
    'id': fields.Integer(readonly=True, description='Unique identifier'),
    'name': fields.String(required=True, description='Dog name'),
    'latitude': fields.Float(required=True, description='GPS latitude (-90 to 90)'),
    'longitude': fields.Float(required=True, description='GPS longitude (-180 to 180)'),
    'breed': fields.String(required=True, description='Dog breed'),
    'photo_filename': fields.String(description='Photo filename'),
    'photo_url': fields.String(description='Static URL to photo'),
    'photo_download_url': fields.String(description='API endpoint to download photo'),
    'comments': fields.String(description='Additional comments'),
    'caught_date': fields.DateTime(description='Date and time when the dog was caught')
})

export_model = api.model('Export', {
    'total_count': fields.Integer(description='Total number of dogs'),
    'exported_at': fields.DateTime(description='Export timestamp'),
    'dogs': fields.List(fields.Nested(dog_model), description='List of all dogs')
})

dog_input_model = api.model('DogInput', {
    'name': fields.String(required=True, description='Dog name'),
    'latitude': fields.Float(required=True, description='GPS latitude (-90 to 90)'),
    'longitude': fields.Float(required=True, description='GPS longitude (-180 to 180)'),
    'breed': fields.String(required=True, description='Dog breed'),
    'comments': fields.String(description='Additional comments')
})


def dog_to_dict(dog):
    """Convert Dog object to dictionary for JSON serialization"""
    return {
        'id': dog.id,
        'name': dog.name,
        'latitude': dog.latitude,
        'longitude': dog.longitude,
        'breed': dog.breed,
        'photo_filename': dog.photo_filename,
        'photo_url': f'/static/uploads/{dog.photo_filename}' if dog.photo_filename else None,
        'photo_download_url': f'/api/dogs/{dog.id}/photo' if dog.photo_filename else None,
        'comments': dog.comments,
        'caught_date': dog.caught_date.isoformat() if dog.caught_date else None
    }


@ns.route('/')
class DogList(Resource):
    @ns.doc('list_dogs', security='apikey')
    @ns.response(401, 'API key required')
    @ns.response(403, 'Invalid API key')
    @ns.marshal_list_with(dog_model)
    @require_api_key
    def get(self):
        """List all dogs"""
        dogs = Dog.query.order_by(Dog.caught_date.desc()).all()
        return [dog_to_dict(dog) for dog in dogs]

    @ns.doc('create_dog', security='apikey')
    @ns.expect(dog_input_model)
    @ns.marshal_with(dog_model, code=201)
    @ns.response(400, 'Validation error')
    @ns.response(401, 'API key required')
    @ns.response(403, 'Invalid API key')
    @require_api_key
    def post(self):
        """Create a new dog entry"""
        data = api.payload

        # Validate required fields
        if not data.get('name') or not data.get('breed'):
            api.abort(400, 'Name and breed are required fields')

        # Validate coordinates
        try:
            latitude = float(data.get('latitude'))
            longitude = float(data.get('longitude'))
        except (TypeError, ValueError):
            api.abort(400, 'Invalid GPS coordinates')

        if not validate_coordinates(latitude, longitude):
            api.abort(400, 'GPS coordinates out of valid range')

        new_dog = Dog(
            name=data['name'],
            latitude=latitude,
            longitude=longitude,
            breed=data['breed'],
            comments=data.get('comments', '')
        )

        db.session.add(new_dog)
        db.session.commit()

        return dog_to_dict(new_dog), 201


@ns.route('/<int:dog_id>')
@ns.param('dog_id', 'The dog identifier')
class DogResource(Resource):
    @ns.doc('get_dog', security='apikey')
    @ns.marshal_with(dog_model)
    @ns.response(401, 'API key required')
    @ns.response(403, 'Invalid API key')
    @ns.response(404, 'Dog not found')
    @require_api_key
    def get(self, dog_id):
        """Get a dog by ID"""
        dog = Dog.query.get_or_404(dog_id)
        return dog_to_dict(dog)

    @ns.doc('delete_dog', security='apikey')
    @ns.response(204, 'Dog deleted')
    @ns.response(401, 'API key required')
    @ns.response(403, 'Invalid API key')
    @ns.response(404, 'Dog not found')
    @require_api_key
    def delete(self, dog_id):
        """Delete a dog by ID"""
        dog = Dog.query.get_or_404(dog_id)

        # Delete photo file if it exists
        if dog.photo_filename:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], dog.photo_filename)
            if os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except OSError:
                    pass

        db.session.delete(dog)
        db.session.commit()

        return '', 204


@ns.route('/export')
class DogExport(Resource):
    @ns.doc('export_all_dogs', security='apikey')
    @ns.response(401, 'API key required')
    @ns.response(403, 'Invalid API key')
    @ns.marshal_with(export_model)
    @require_api_key
    def get(self):
        """Export all dogs data"""
        dogs = Dog.query.order_by(Dog.caught_date.desc()).all()
        return {
            'total_count': len(dogs),
            'exported_at': datetime.datetime.utcnow().isoformat(),
            'dogs': [dog_to_dict(dog) for dog in dogs]
        }


@ns.route('/<int:dog_id>/photo')
@ns.param('dog_id', 'The dog identifier')
class DogPhoto(Resource):
    @ns.doc('get_dog_photo', security='apikey')
    @ns.response(200, 'Photo file')
    @ns.response(401, 'API key required')
    @ns.response(403, 'Invalid API key')
    @ns.response(404, 'Dog or photo not found')
    @ns.produces(['image/jpeg', 'image/png', 'image/gif'])
    @require_api_key
    def get(self, dog_id):
        """Download a dog's photo by dog ID"""
        dog = Dog.query.get_or_404(dog_id)

        if not dog.photo_filename:
            api.abort(404, 'No photo available for this dog')

        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], dog.photo_filename)
        if not os.path.exists(photo_path):
            api.abort(404, 'Photo file not found')

        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            dog.photo_filename,
            as_attachment=True,
            download_name=f"{dog.name}_{dog.photo_filename}"
        )


@app.route('/')
def index():
    """Home page with navigation"""
    return render_template('index.html')

@app.route('/admin')
def admin():
    """Admin page to add new dog entries"""
    return render_template('admin.html')

@app.route('/add_dog', methods=['POST'])
def add_dog():
    """Handle form submission to add a new dog"""
    try:
        # Validate required fields
        name = request.form.get('name', '').strip()
        breed = request.form.get('breed', '').strip()
        
        if not name or not breed:
            flash('Name and breed are required fields.', 'error')
            return redirect(url_for('admin'))
        
        # Validate and convert coordinates
        try:
            latitude = float(request.form.get('latitude'))
            longitude = float(request.form.get('longitude'))
        except (TypeError, ValueError):
            flash('Invalid GPS coordinates. Please enter valid numbers.', 'error')
            return redirect(url_for('admin'))
        
        # Validate coordinate ranges
        if not validate_coordinates(latitude, longitude):
            flash('GPS coordinates out of valid range. Latitude must be between -90 and 90, longitude between -180 and 180.', 'error')
            return redirect(url_for('admin'))
        
        comments = request.form.get('comments', '')
        
        # Handle file upload with validation
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '':
                if not allowed_file(photo.filename):
                    flash('Invalid file type. Only PNG, JPG, JPEG, and GIF images are allowed.', 'error')
                    return redirect(url_for('admin'))
                
                filename = secure_filename(photo.filename)
                # Add timestamp to avoid filename collisions
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_')
                photo_filename = timestamp + filename
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        
        # Create new dog entry
        new_dog = Dog(
            name=name,
            latitude=latitude,
            longitude=longitude,
            breed=breed,
            photo_filename=photo_filename,
            comments=comments
        )
        
        db.session.add(new_dog)
        db.session.commit()
        
        flash(f'Successfully added {name} to the database!', 'success')
        return redirect(url_for('admin'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding dog: {str(e)}', 'error')
        return redirect(url_for('admin'))

@app.route('/browse')
def browse():
    """Browse all dogs in the database"""
    dogs = Dog.query.order_by(Dog.caught_date.desc()).all()
    return render_template('browse.html', dogs=dogs)

@app.route('/delete_dog/<int:dog_id>', methods=['POST'])
def delete_dog(dog_id):
    """Delete a dog from the database"""
    try:
        dog = Dog.query.get_or_404(dog_id)
        dog_name = dog.name
        
        # Delete photo file if it exists
        if dog.photo_filename:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], dog.photo_filename)
            if os.path.exists(photo_path):
                try:
                    os.remove(photo_path)
                except OSError as e:
                    # Log the error but continue with database deletion
                    print(f"Warning: Could not delete photo file: {e}")
        
        db.session.delete(dog)
        db.session.commit()
        
        flash(f'Successfully deleted {dog_name} from the database.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting dog: {str(e)}', 'error')
    
    return redirect(url_for('browse'))

if __name__ == '__main__':
    import ssl
    
    # Debug mode controlled by environment variable, defaults to False for safety
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # mTLS Configuration
    mtls_enabled = os.environ.get('MTLS_ENABLED', 'false').lower() == 'true'
    
    if mtls_enabled:
        # Certificate paths
        cert_dir = os.environ.get('CERT_DIR', '/app/certs')
        server_cert = os.environ.get('SERVER_CERT', f'{cert_dir}/server.crt')
        server_key = os.environ.get('SERVER_KEY', f'{cert_dir}/server.key')
        ca_cert = os.environ.get('CA_CERT', f'{cert_dir}/ca.crt')
        
        # Verify certificates exist
        for cert_file in [server_cert, server_key, ca_cert]:
            if not os.path.exists(cert_file):
                raise FileNotFoundError(f"Certificate file not found: {cert_file}")
        
        # Create SSL context with client certificate verification
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain(server_cert, server_key)
        ssl_context.load_verify_locations(ca_cert)
        ssl_context.verify_mode = ssl.CERT_REQUIRED  # Require client certificate
        
        print(f"Starting Dogcatcher API with mTLS enabled on port 5000")
        print(f"  Server cert: {server_cert}")
        print(f"  CA cert: {ca_cert}")
        
        app.run(host='0.0.0.0', port=5000, debug=debug_mode, ssl_context=ssl_context)
    else:
        print("Starting Dogcatcher API without mTLS on port 5000")
        app.run(host='0.0.0.0', port=5000, debug=debug_mode)
