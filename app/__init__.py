from flask import Flask
from config import config
from pathlib import Path
import urllib3

# Desabilitar avisos de SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Carregar configurações
    app.config.from_object(config[config_name])
    
    # Garantir que os diretórios existam
    Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
    Path(app.config['IMAGES_FOLDER']).mkdir(exist_ok=True)
    
    # Registrar blueprints
    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app