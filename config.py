import os
from pathlib import Path

class Config:
    # Flask configs
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-12345'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Application configs
    UPLOAD_FOLDER = '/app/pdfs'
    IMAGES_FOLDER = '/app/images'
    MAX_WORKERS = 5
    
    # Ensure directories exist
    Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
    Path(IMAGES_FOLDER).mkdir(exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 