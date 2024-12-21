# Comic PDF Downloader

A web application to download comics from ReadAllComics and convert them to PDF format, preserving the original image quality and dimensions.

## Features

- Web interface for easy comic downloading
- Maintains original image quality and dimensions
- Parallel image downloading for better performance
- Automatic cleanup of temporary files
- Docker containerized for easy deployment

## Requirements

- Docker
- Docker Compose

## Quick Start

1. Clone the repository:
```
git clone <repository-url>
cd readallcomics-pdf-download
```

2. Create required directories:
```bash
mkdir -p pdfs images
```

3. Build and run with Docker Compose:
```bash
docker-compose up --build
```

4. Access the application:
   - Open your browser and navigate to: http://localhost:5000
   - Paste a ReadAllComics URL (e.g., https://readallcomics.com/kingdom-come-2019-part-1/)
   - Click "Download PDF"
   - Wait for the PDF to be generated and downloaded automatically

## Running Without Docker

If you prefer to run without Docker:

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create required directories:
```bash
mkdir -p pdfs images
```

4. Run the application:
```bash
python app.py
```

5. Access the application at http://localhost:5000

## Project Structure

```
.
├── app.py              # Flask web application
├── main.py            # Core download and PDF generation logic
├── requirements.txt   # Python dependencies
├── Dockerfile         # Docker image configuration
├── docker-compose.yml # Docker Compose configuration
├── templates/         # HTML templates
│   └── index.html    # Main page template
├── pdfs/             # Generated PDFs storage (created at runtime)
└── images/           # Temporary image storage (created at runtime)
```

## Notes

- PDFs are saved temporarily and automatically deleted after download
- Images are automatically cleaned up after PDF generation
- The application runs on port 5000 by default
- For production deployment, consider adding proper security measures

## Troubleshooting

1. If the application can't create directories:
   - Ensure you have write permissions in the project directory
   - Manually create the `pdfs` and `images` directories

2. If PDFs aren't downloading:
   - Check your browser's download settings
   - Look for the PDF in the `pdfs` directory

3. If images aren't downloading:
   - Verify your internet connection
   - Check if the comic URL is accessible
   - Ensure the URL follows the ReadAllComics format