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

db = SQLAlchemy(app)

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
    caught_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
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
        name = request.form.get('name')
        latitude = float(request.form.get('latitude'))
        longitude = float(request.form.get('longitude'))
        breed = request.form.get('breed')
        comments = request.form.get('comments', '')
        
        # Handle file upload
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename != '':
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
        
        # Delete photo file if it exists
        if dog.photo_filename:
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], dog.photo_filename)
            if os.path.exists(photo_path):
                os.remove(photo_path)
        
        db.session.delete(dog)
        db.session.commit()
        
        flash(f'Successfully deleted {dog.name} from the database.', 'success')
    except Exception as e:
        flash(f'Error deleting dog: {str(e)}', 'error')
    
    return redirect(url_for('browse'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
