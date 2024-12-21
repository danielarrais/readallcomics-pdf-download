import os
from flask import Flask, render_template, request, jsonify, send_file, abort
from main import download_images_and_create_pdf
from pathlib import Path

app = Flask(__name__)
app.config.update(
    UPLOAD_FOLDER='pdfs',
    MAX_WORKERS=5,  # Número máximo de downloads paralelos
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # Limite de 16MB para uploads
)

Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL inválida'}), 400
        
        if not url.startswith('https://readallcomics.com/'):
            return jsonify({'error': 'URL inválida'}), 400
        
        # Extrai o nome do PDF do URL
        pdf_name = f"{url.rstrip('/').split('/')[-1]}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
        
        # Faz o download e cria o PDF
        download_images_and_create_pdf(
            url=url,
            xpath="/html/body/center[3]/center/div[1]",
            output_path=pdf_path,
            max_workers=app.config['MAX_WORKERS']
        )
        
        return jsonify({'filename': pdf_name})
        
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            abort(404)
        
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
        
        @response.call_on_close
        def remove_file():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    app.logger.info(f"PDF removed: {file_path}")
            except Exception as e:
                app.logger.error(f"Error removing PDF {file_path}: {str(e)}")
        
        return response
        
    except Exception as e:
        app.logger.error(f"Error downloading file: {str(e)}")
        abort(404)

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Arquivo não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 