import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import datetime

app = Flask(__name__)
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
    # Debug mode controlled by environment variable, defaults to False for safety
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
