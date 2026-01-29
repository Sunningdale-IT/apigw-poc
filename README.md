# 🐕 City Dog Catcher Application

A web-based application for city dog catchers to manage information about caught dogs. The application allows dog catchers to record details of found dogs and browse the database through a user-friendly web interface.

## Features

- **Add Dog Entries**: Record details of caught dogs including:
  - Name
  - GPS coordinates (latitude/longitude) where found
  - Breed
  - Photo upload
  - Additional comments
- **Browse Database**: View all caught dogs with their information in an easy-to-browse interface
- **Photo Management**: Upload and view photos of caught dogs
- **Location Mapping**: Direct links to Google Maps for found locations
- **Containerized Deployment**: Easy deployment using Docker Compose

## Prerequisites

- Docker (version 20.10 or later)
- Docker Compose (version 2.0 or later)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd apigw-poc
```

### 2. Start the Application

```bash
docker-compose up -d
```

This will:
- Build the Flask web application container
- Start a PostgreSQL database container
- Create the necessary database tables
- Start the web server on port 5000

### 3. Access the Application

Open your web browser and navigate to:

```
http://localhost:5000
```

## Usage

### Adding a Dog

1. Click on "Add Dog" in the navigation menu
2. Fill in the form with the dog's details:
   - **Name**: Enter the dog's name (required)
   - **Breed**: Specify the breed (required)
   - **Latitude/Longitude**: Enter GPS coordinates where the dog was found (required)
   - **Photo**: Upload a photo of the dog (optional, max 16MB)
   - **Comments**: Add any additional notes (optional)
3. Click "Submit Dog Entry"

### Finding GPS Coordinates

You can obtain GPS coordinates using:
- **Google Maps**: Right-click on a location and copy the coordinates
- **Smartphone GPS**: Use a location-sharing app or GPS coordinates app
- **GPS Device**: Direct reading from the device

Example coordinates:
- Latitude: 51.5074 (London)
- Longitude: -0.1278 (London)

### Browsing Dogs

1. Click on "Browse Dogs" in the navigation menu
2. View all caught dogs displayed as cards
3. Each card shows:
   - Dog photo (if uploaded)
   - Name and breed
   - GPS coordinates with link to Google Maps
   - Date and time caught
   - Comments
4. Click on the location coordinates to view the exact spot on Google Maps
5. Use the "Delete Entry" button to remove a dog from the database

## Project Structure

```
.
├── app/                      # Application directory
│   ├── app.py               # Main Flask application
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile           # Docker image for web app
│   ├── static/              # Static files
│   │   └── uploads/         # Dog photo uploads
│   └── templates/           # HTML templates
│       ├── base.html        # Base template
│       ├── index.html       # Home page
│       ├── admin.html       # Add dog form
│       └── browse.html      # Browse dogs page
├── docker-compose.yml       # Docker Compose configuration
└── README.md               # This file
```

## Configuration

### Environment Variables

The application uses the following environment variables (configured in docker-compose.yml):

**Database:**
- `POSTGRES_DB`: Database name (default: dogcatcher)
- `POSTGRES_USER`: Database user (default: dogcatcher)
- `POSTGRES_PASSWORD`: Database password (default: dogcatcher123)

**Web Application:**
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Flask secret key for sessions (change in production!)

### Ports

- **Web Application**: `5000` (mapped to host port 5000)
- **PostgreSQL Database**: `5432` (mapped to host port 5432)

## Development

### Viewing Logs

```bash
# View all logs
docker-compose logs -f

# View web application logs only
docker-compose logs -f web

# View database logs only
docker-compose logs -f db
```

### Stopping the Application

```bash
docker-compose down
```

### Stopping and Removing Data

To stop the application and remove all data (including uploaded photos and database):

```bash
docker-compose down -v
```

### Rebuilding After Changes

If you make changes to the application code:

```bash
docker-compose down
docker-compose up -d --build
```

## Database

The application uses PostgreSQL 16 with a single table:

**dogs table:**
- `id`: Primary key (auto-increment)
- `name`: Dog's name (varchar)
- `latitude`: GPS latitude (float)
- `longitude`: GPS longitude (float)
- `breed`: Dog breed (varchar)
- `photo_filename`: Uploaded photo filename (varchar, nullable)
- `comments`: Additional notes (text, nullable)
- `caught_date`: Timestamp when record was created (datetime)

## Security Notes

⚠️ **Important**: This is a sample application. Before deploying to production:

1. Change the `SECRET_KEY` environment variable
2. Use strong database passwords
3. Implement user authentication
4. Add SSL/TLS encryption
5. Configure proper file upload validation
6. Set up database backups
7. Review and implement security best practices

## Troubleshooting

### Port Already in Use

If port 5000 or 5432 is already in use on your system, edit `docker-compose.yml` and change the port mappings:

```yaml
ports:
  - "8080:5000"  # Change 5000 to 8080 or any available port
```

### Database Connection Issues

If the web application can't connect to the database:

1. Check if the database container is healthy:
   ```bash
   docker-compose ps
   ```

2. View database logs:
   ```bash
   docker-compose logs db
   ```

3. Restart the services:
   ```bash
   docker-compose restart
   ```

### Photo Upload Issues

If photos aren't uploading:

1. Check the uploads directory exists:
   ```bash
   docker-compose exec web ls -la /app/static/uploads
   ```

2. Check available disk space
3. Ensure the photo is under 16MB

## Technology Stack

- **Backend**: Flask 3.0 (Python web framework)
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy
- **Containerization**: Docker & Docker Compose
- **Frontend**: HTML, CSS (embedded in templates)

## License

This is a sample application for demonstration purposes.

## Support

For issues or questions, please open an issue in the repository.
