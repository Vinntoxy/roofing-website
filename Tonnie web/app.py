from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import os
from datetime import datetime, timedelta
from functools import wraps
import hashlib
import secrets
import uuid

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'tonnie-roofing-secret-key-change-this')

# Database file path
DB_PATH = 'database.json'

# Ensure upload directories exist
UPLOAD_FOLDER = 'static/uploads'
PROJECTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'projects')
PROFILE_FOLDER = os.path.join(UPLOAD_FOLDER, 'profile')
THUMBNAILS_FOLDER = os.path.join(UPLOAD_FOLDER, 'thumbnails')

for folder in [UPLOAD_FOLDER, PROJECTS_FOLDER, PROFILE_FOLDER, THUMBNAILS_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Database helper functions
def read_db():
    """Read data from JSON database"""
    if not os.path.exists(DB_PATH):
        # Create default database structure
        default_db = {
            "admins": [],
            "profile": {
                "company_name": "Tonnie Roofing",
                "company_logo": "/static/uploads/profile/logo.png",
                "hero_image": "/static/uploads/thumbnails/hero.jpg",
                "tagline": "Professional Roofing & Interior Design Services",
                "description": "Your trusted partner in quality construction since 2015",
                "ceo": {
                    "name": "John Tonnie",
                    "photo": "/static/uploads/profile/ceo.jpg",
                    "title": "Founder & CEO",
                    "bio": "With over 20 years of experience in the construction industry..."
                },
                "active_since": "2015",
                "contact": {
                    "phone": "+254 700 000 000",
                    "phone2": "+254 711 111 111",
                    "emergency": "+254 722 222 222",
                    "email": "info@tonnieroofing.co.ke",
                    "email2": "sales@tonnieroofing.co.ke"
                },
                "social": [
                    {"platform": "Facebook", "icon": "📘", "url": "#", "active": True},
                    {"platform": "Instagram", "icon": "📷", "url": "#", "active": True},
                    {"platform": "Twitter", "icon": "🐦", "url": "#", "active": True},
                    {"platform": "WhatsApp", "icon": "💬", "url": "#", "active": True}
                ],
                "address": {
                    "street": "Kilimani Business Centre",
                    "city": "Nairobi",
                    "county": "Nairobi",
                    "country": "Kenya"
                },
                "hours": {
                    "weekdays": "8:00 AM - 6:00 PM",
                    "saturday": "9:00 AM - 3:00 PM",
                    "sunday": "Closed",
                    "repairs": "Mon-Fri 8:00 AM - 6:00 PM",
                    "consultation": "Mon-Fri 8:00 AM - 6:00 PM"
                }
            },
            "services": [
                {
                    "id": "serv_001",
                    "name": "Roofing",
                    "slug": "roofing",
                    "icon": "🏠",
                    "image": "/static/uploads/thumbnails/roofing.jpg",
                    "detail_image": "/static/uploads/thumbnails/roofing-detail.jpg",
                    "short_description": "Professional roof installation and maintenance",
                    "full_description": "Complete roofing solutions using quality materials including mabati, concrete tiles, and more.",
                    "features": [
                        "New roof installation",
                        "Roof replacement",
                        "Leak repairs",
                        "Maintenance"
                    ],
                    "active": True,
                    "project_count": 0
                },
                {
                    "id": "serv_002",
                    "name": "Interior Design",
                    "slug": "interior",
                    "icon": "✨",
                    "image": "/static/uploads/thumbnails/interior.jpg",
                    "detail_image": "/static/uploads/thumbnails/interior-detail.jpg",
                    "short_description": "Modern interior design solutions",
                    "full_description": "Transform your space with gypsum installations, custom fittings, and modern designs.",
                    "features": [
                        "Gypsum ceilings",
                        "Wall partitions",
                        "Custom fittings",
                        "Space planning"
                    ],
                    "active": True,
                    "project_count": 0
                },
                {
                    "id": "serv_003",
                    "name": "Repairs",
                    "slug": "repairs",
                    "icon": "🔧",
                    "image": "/static/uploads/thumbnails/repairs.jpg",
                    "detail_image": "/static/uploads/thumbnails/repairs-detail.jpg",
                    "short_description": "Professional repair services",
                    "full_description": "Quick and reliable repair services for roofing, ceilings, and structural issues.",
                    "features": [
                        "Roof leak repairs",
                        "Ceiling repairs",
                        "Structural fixes",
                        "Maintenance"
                    ],
                    "active": True,
                    "project_count": 0
                },
                {
                    "id": "serv_004",
                    "name": "Quoting Service",
                    "slug": "quoting",
                    "icon": "📋",
                    "image": "/static/uploads/thumbnails/quoting.jpg",
                    "detail_image": "/static/uploads/thumbnails/quoting-detail.jpg",
                    "short_description": "Detailed project quotes",
                    "full_description": "Get accurate, detailed quotes for roofing and interior design projects.",
                    "features": [
                        "Project assessment",
                        "Material calculation",
                        "Cost estimation",
                        "Timeline planning"
                    ],
                    "active": True,
                    "project_count": 0
                }
            ],
            "projects": [],
            "inquiries": [],
            "visits": {
                "total": 0,
                "monthly": {},
                "daily": {},
                "devices": {}
            },
            "settings": {
                "admin_count": 0,
                "max_admins": 2
            }
        }
        write_db(default_db)
        return default_db
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def write_db(data):
    """Write data to JSON database"""
    with open(DB_PATH, 'w') as f:
        json.dump(data, f, indent=2)

# Kenyan counties list
KENYAN_COUNTIES = [
    "Baringo", "Bomet", "Bungoma", "Busia", "Elgeyo Marakwet", "Embu", "Garissa",
    "Homa Bay", "Isiolo", "Kajiado", "Kakamega", "Kericho", "Kiambu", "Kilifi",
    "Kirinyaga", "Kisii", "Kisumu", "Kitui", "Kwale", "Laikipia", "Lamu",
    "Machakos", "Makueni", "Mandera", "Marsabit", "Meru", "Migori", "Mombasa",
    "Murang'a", "Nairobi", "Nakuru", "Nandi", "Narok", "Nyamira", "Nyandarua",
    "Nyeri", "Samburu", "Siaya", "Taita Taveta", "Tana River", "Tharaka Nithi",
    "Trans Nzoia", "Turkana", "Uasin Gishu", "Vihiga", "Wajir", "West Pokot"
]

# Mabati options (Kenyan roofing materials)
MABATI_OPTIONS = [
    "Dumu zas", "Versatile", "Box Profile", "Roman Tile", "Corrugated Sheets",
    "Gutters", "Ridge Caps", "Flashings", "Insulated Panels"
]

# Auth decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    data = read_db()
    featured_projects = [p for p in data['projects'] if p.get('featured', False)][:4]
    return render_template('index.html', 
                         profile=data['profile'], 
                         services=data['services'],
                         projects=featured_projects,
                         mabati_options=MABATI_OPTIONS)

@app.route('/services')
def services():
    data = read_db()
    return render_template('services.html', 
                         profile=data['profile'], 
                         services=data['services'])

@app.route('/projects')
def projects():
    data = read_db()
    service = request.args.get('service', 'all')
    return render_template('projects.html', 
                         profile=data['profile'], 
                         projects=data['projects'],
                         service=service,
                         counties=KENYAN_COUNTIES)

@app.route('/project')
def project_detail():
    data = read_db()
    project_id = request.args.get('id')
    project = None
    for p in data['projects']:
        if p['id'] == project_id:
            project = p
            break
    return render_template('project.html', 
                         profile=data['profile'], 
                         project=project)

@app.route('/profile')
def company_profile():
    data = read_db()
    return render_template('profile.html', 
                         profile=data['profile'], 
                         services=data['services'])

@app.route('/contact')
def contact():
    data = read_db()
    service = request.args.get('service', 'general')
    return render_template('contact.html', 
                         profile=data['profile'], 
                         service=service,
                         counties=KENYAN_COUNTIES)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = read_db()
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication (in production, use proper hashing)
        for admin in data['admins']:
            if admin['username'] == username and admin['password'] == password:
                session['admin_logged_in'] = True
                session['admin_id'] = admin['id']
                session['admin_username'] = username
                return redirect(url_for('admin_dashboard'))
        
        return render_template('admin/login.html', error='Invalid credentials')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    data = read_db()
    return render_template('admin/dashboard.html', 
                         profile=data['profile'],
                         stats={
                             'projects': len(data['projects']),
                             'inquiries': len(data['inquiries']),
                             'services': len(data['services']),
                             'admins': data['settings']['admin_count']
                         })

@app.route('/admin/projects')
@admin_required
def admin_projects():
    data = read_db()
    return render_template('admin/projects.html', 
                         projects=data['projects'],
                         services=data['services'])

@app.route('/admin/project-edit', methods=['GET', 'POST'])
@admin_required
def admin_project_edit():
    data = read_db()
    project_id = request.args.get('id')
    project = None
    
    if project_id:
        for p in data['projects']:
            if p['id'] == project_id:
                project = p
                break
    
    return render_template('admin/project-edit.html',
                         project=project,
                         services=data['services'],
                         counties=KENYAN_COUNTIES,
                         mabati_options=MABATI_OPTIONS)

@app.route('/admin/services')
@admin_required
def admin_services():
    data = read_db()
    return render_template('admin/services.html', services=data['services'])

@app.route('/admin/profile')
@admin_required
def admin_profile():
    data = read_db()
    return render_template('admin/profile.html', 
                         profile=data['profile'],
                         counties=KENYAN_COUNTIES)

@app.route('/admin/inquiries')
@admin_required
def admin_inquiries():
    data = read_db()
    return render_template('admin/inquiries.html', inquiries=data['inquiries'])

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    data = read_db()
    return render_template('admin/analytics.html', visits=data['visits'])

@app.route('/admin/create-account', methods=['GET', 'POST'])
def admin_create_account():
    data = read_db()
    
    # Check if max admins reached
    if data['settings']['admin_count'] >= data['settings']['max_admins']:
        return render_template('admin/create-account.html', max_reached=True)
    
    if request.method == 'POST':
        # Create new admin account
        new_admin = {
            'id': str(uuid.uuid4()),
            'username': request.form.get('username'),
            'password': request.form.get('password'),  # In production, hash this
            'full_name': request.form.get('fullName'),
            'email': request.form.get('email'),
            'created_at': datetime.now().isoformat()
        }
        
        data['admins'].append(new_admin)
        data['settings']['admin_count'] += 1
        write_db(data)
        
        return redirect(url_for('admin_login'))
    
    return render_template('admin/create-account.html', 
                         max_reached=False,
                         current_count=data['settings']['admin_count'],
                         max_count=data['settings']['max_admins'])

if __name__ == '__main__':
    app.run(debug=True)