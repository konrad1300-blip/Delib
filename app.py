from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Entry, Settings, Category
from config import config
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config[os.environ.get('FLASK_ENV', 'default')])

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


def init_db():
    """Initialize database with default users."""
    with app.app_context():
        db.create_all()
        
        # Create default admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Create default user if not exists
        if not User.query.filter_by(username='user').first():
            user = User(username='user', role='user')
            user.set_password('user123')
            db.session.add(user)
        
        # Create default categories if not exists
        default_categories = [
            'Budżetowe',
            'Organizacyjne',
            'Infrastruktura',
            'Środowisko',
            'Społeczne'
        ]
        for cat_name in default_categories:
            if not Category.query.filter_by(name=cat_name).first():
                category = Category(name=cat_name)
                db.session.add(category)
        
        db.session.commit()


# Routes
@app.route('/')
def index():
    """Home page - redirect to login or dashboard."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout user."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with entry tree."""
    # Get root entries (threads)
    threads = Entry.query.filter_by(parent_id=None).order_by(Entry.created_at.desc()).all()
    return render_template('dashboard.html', threads=threads)


@app.route('/entry', methods=['POST'])
@login_required
def create_entry():
    """Create new thread entry."""
    title = request.form.get('title')
    content = request.form.get('content')
    
    if not content:
        flash('Content is required', 'error')
        return redirect(url_for('dashboard'))
    
    entry = Entry(
        title=title,
        content=content,
        author_id=current_user.id,
        parent_id=None
    )
    
    db.session.add(entry)
    db.session.commit()
    
    flash('Thread created successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/entry/<int:entry_id>/reply', methods=['POST'])
@login_required
def create_reply(entry_id):
    """Create reply to existing entry."""
    parent = Entry.query.get_or_404(entry_id)
    content = request.form.get('content')
    
    if not content:
        flash('Content is required', 'error')
        return redirect(url_for('dashboard'))
    
    # Check depth limit (10 levels)
    if parent.get_depth() >= 10:
        flash('Maximum nesting depth reached (10 levels)', 'error')
        return redirect(url_for('dashboard'))
    
    entry = Entry(
        content=content,
        author_id=current_user.id,
        parent_id=parent.id
    )
    
    db.session.add(entry)
    db.session.commit()
    
    flash('Reply added successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/entry/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_entry(entry_id):
    """Delete entry and all its children."""
    entry = Entry.query.get_or_404(entry_id)
    
    # Check permissions
    if not current_user.is_admin() and entry.author_id != current_user.id:
        flash('You do not have permission to delete this entry', 'error')
        return redirect(url_for('dashboard'))
    
    # Get all children to delete
    entries_to_delete = [entry] + entry.get_all_children()
    
    for e in entries_to_delete:
        db.session.delete(e)
    
    db.session.commit()
    
    flash('Entry and all replies deleted successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/entry/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    """Edit existing entry."""
    entry = Entry.query.get_or_404(entry_id)
    
    # Check permissions
    if not current_user.is_admin() and entry.author_id != current_user.id:
        flash('You do not have permission to edit this entry', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        if entry.is_thread():
            entry.title = request.form.get('title')
        entry.content = request.form.get('content')
        
        if not entry.content:
            flash('Content is required', 'error')
            return redirect(url_for('dashboard'))
        
        db.session.commit()
        
        flash('Entry updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('entry_form.html', entry=entry, edit_mode=True)


@app.route('/admin/users')
@login_required
def admin_users():
    """Admin page to manage users."""
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)


@app.route('/admin/users', methods=['POST'])
@login_required
def admin_create_user():
    """Create new user (admin only)."""
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role', 'user')
    
    if not username or not password:
        flash('Username and password are required.', 'error')
        return redirect(url_for('admin_users'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('admin_users'))
    
    new_user = User(username=username, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    flash(f'User "{username}" created successfully.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    """Delete user (admin only)."""
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_users'))
    
    # Delete user's entries first
    Entry.query.filter_by(author_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User "{user.username}" deleted successfully.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/settings')
@login_required
def admin_settings():
    """Admin page for system configuration."""
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    settings = Settings.get_settings()
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin_settings.html', settings=settings, categories=categories)


@app.route('/admin/settings', methods=['POST'])
@login_required
def admin_update_settings():
    """Update system settings (admin only)."""
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    settings = Settings.get_settings()
    
    # Update entity configuration
    settings.entity_name = request.form.get('entity_name', settings.entity_name)
    settings.entity_area = request.form.get('entity_area', settings.entity_area)
    settings.regulations = request.form.get('regulations', settings.regulations)
    
    # Update process parameters
    settings.discussion_duration_days = int(request.form.get('discussion_duration_days', 14))
    settings.priority_threshold = int(request.form.get('priority_threshold', 10))
    settings.voting_enabled = 'voting_enabled' in request.form
    
    db.session.commit()
    flash('Ustawienia zapisane pomyślnie.', 'success')
    return redirect(url_for('admin_settings'))


@app.route('/admin/categories', methods=['POST'])
@login_required
def admin_create_category():
    """Create new category (admin only)."""
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    name = request.form.get('name')
    description = request.form.get('description')
    color = request.form.get('color', '#007bff')
    
    if not name:
        flash('Category name is required.', 'error')
        return redirect(url_for('admin_settings'))
    
    category = Category(name=name, description=description, color=color)
    db.session.add(category)
    db.session.commit()
    
    flash(f'Category "{name}" created successfully.', 'success')
    return redirect(url_for('admin_settings'))


@app.route('/admin/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def admin_delete_category(category_id):
    """Delete category (admin only)."""
    if not current_user.is_admin():
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
    
    category = Category.query.get_or_404(category_id)
    
    # Move entries to uncategorized
    for entry in category.entries:
        entry.category_id = None
    
    db.session.delete(category)
    db.session.commit()
    
    flash(f'Category "{category.name}" deleted successfully.', 'success')
    return redirect(url_for('admin_settings'))


# Error handlers
@app.errorhandler(404)
def not_found(e):
    """404 error page."""
    return render_template('error.html', error='Page not found'), 404


@app.errorhandler(500)
def server_error(e):
    """500 error page."""
    return render_template('error.html', error='Internal server error'), 500


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
