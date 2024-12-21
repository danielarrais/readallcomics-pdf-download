from flask import Blueprint, render_template, request, jsonify, send_file, abort, current_app
from app.services.comic_service import ComicService
from app.utils.logger import logger
import os
from pathlib import Path
from functools import wraps

main = Blueprint('main', __name__)

def delete_file_after_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        if response.status_code == 200:
            filename = kwargs.get('filename')
            if filename:
                file_path = Path(current_app.config['UPLOAD_FOLDER']) / filename
                try:
                    if file_path.exists():
                        os.remove(str(file_path))
                        logger.info("Successfully deleted PDF after download: %s", file_path)
                except Exception as e:
                    logger.error("Error deleting PDF %s: %s", file_path, str(e))
        return response
    return decorated_function

@main.route('/')
def index():
    logger.info("Accessing index page")
    return render_template('index.html')

@main.route('/download', methods=['POST'])
def download():
    logger.info("Received download request")
    try:
        data = request.get_json()
        url = data.get('url')
        compress = data.get('compress', True)
        logger.info("Processing URL: %s with compression: %s", url, compress)
        
        if not url:
            logger.warning("Invalid request: URL is empty")
            return jsonify({'error': 'URL inválida'}), 400
        
        if not url.startswith('https://readallcomics.com/'):
            logger.warning("Invalid request: URL is not from readallcomics.com - %s", url)
            return jsonify({'error': 'URL inválida'}), 400
        
        logger.info("Creating comic service instance")
        comic_service = ComicService()
        comic_service.compress_images = compress
        pdf_name = comic_service.process_comic(url)
        logger.info("Successfully generated PDF: %s", pdf_name)
        
        return jsonify({'filename': pdf_name})
        
    except Exception as e:
        logger.error("Error processing request: %s", str(e), exc_info=True)
        return jsonify({'error': 'Erro interno do servidor'}), 500

@main.route('/download/<filename>')
@delete_file_after_request
def download_file(filename):
    logger.info("Received file download request for: %s", filename)
    try:
        file_path = Path(current_app.config['UPLOAD_FOLDER']) / filename
        logger.debug("Full file path: %s", file_path)
        
        if not file_path.exists():
            logger.warning("File not found: %s", file_path)
            return jsonify({'error': 'Arquivo não encontrado'}), 404
        
        logger.info("Sending file: %s", filename)
        try:
            return send_file(
                str(file_path),
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        except Exception as e:
            logger.error("Error sending file: %s", str(e), exc_info=True)
            return jsonify({'error': 'Erro ao enviar arquivo'}), 500
        
    except Exception as e:
        logger.error("Error in download route: %s", str(e), exc_info=True)
        return jsonify({'error': 'Erro interno do servidor'}), 500

@main.errorhandler(404)
def not_found_error(error):
    logger.warning("404 error occurred")
    return jsonify({'error': 'Arquivo não encontrado'}), 404

@main.errorhandler(500)
def internal_error(error):
    logger.error("500 error occurred", exc_info=True)
    return jsonify({'error': 'Erro interno do servidor'}), 500 