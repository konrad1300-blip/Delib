from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class Settings(db.Model):
    """System settings model for SDD configuration."""
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Entity Configuration (Konfiguracja Podmiotu)
    entity_name = db.Column(db.String(200), nullable=False, default='Moja Organizacja')
    entity_area = db.Column(db.String(200), nullable=True)  # Obszar działania
    regulations = db.Column(db.Text, nullable=True)  # Regulaminy i statuty
    
    # Process Parameters (Parametry Procesu)
    discussion_duration_days = db.Column(db.Integer, default=14)  # Czas trwania dyskusji
    priority_threshold = db.Column(db.Integer, default=10)  # Próg priorytetowy
    voting_enabled = db.Column(db.Boolean, default=False)  # Czy głosowanie jest włączone
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_settings():
        """Get or create settings instance."""
        settings = Settings.query.first()
        if not settings:
            settings = Settings()
            db.session.add(settings)
            db.session.commit()
        return settings
    
    def __repr__(self):
        return f'<Settings {self.entity_name}>'


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to entries
    entries = db.relationship('Entry', backref='author', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin."""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'


class Entry(db.Model):
    """Entry model for tree-structured posts (threads/comments)."""
    __tablename__ = 'entries'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)  # Nullable for comments
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('entries.id'), nullable=True)  # null for root threads
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)  # Kategoria kwestii
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    priority = db.Column(db.Integer, default=0)  # Priorytet (głosy użytkowników)
    status = db.Column(db.String(20), default='discussion')  # discussion, voting, completed
    
    # Self-referential relationship for tree structure
    children = db.relationship('Entry', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    category = db.relationship('Category', backref=db.backref('entries', lazy='dynamic'))
    
    def is_thread(self):
        """Check if entry is a thread (root level)."""
        return self.parent_id is None
    
    def get_depth(self):
        """Calculate depth of entry in tree."""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth
    
    def get_all_children(self):
        """Get all descendants recursively."""
        result = []
        for child in self.children:
            result.append(child)
            result.extend(child.get_all_children())
        return result
    
    def __repr__(self):
        return f'<Entry {self.id}: {self.title or "Comment"}>'


class Category(db.Model):
    """Category model for issue types (kategorie kwestii)."""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(7), default='#007bff')  # Hex color for UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Category {self.name}>'
