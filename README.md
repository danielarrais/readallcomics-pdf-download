# Comic PDF Downloader

A web application to download comics from ReadAllComics and convert them to PDF format, preserving the original image quality and dimensions.

## Features

- Web interface for easy comic downloading
- Maintains original image quality and dimensions
- Parallel image downloading for better performance
- Automatic cleanup of temporary files and PDFs after download
- Docker containerized for easy deployment
- Optimized page loading (downloads only necessary content)

## Requirements

- Docker
- Docker Compose

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd readallcomics-pdf-download
```

2. Build and run with Docker Compose:
```bash
docker-compose up --build
```

3. Access the application:
   - Open your browser and navigate to: http://localhost:5000
   - Paste a ReadAllComics URL (e.g., https://readallcomics.com/kingdom-come-2019-part-1/)
   - Click "Download PDF"
   - The PDF will be automatically downloaded and removed from the server

## Project Structure

```
.
├── app/                # Application package
│   ├── __init__.py    # App initialization
│   ├── routes/        # Route handlers
│   ├── services/      # Business logic
│   ├── utils/         # Utilities
│   ├── static/        # Static files
│   └── templates/     # HTML templates
├── config.py          # Configuration
├── main.py           # Application entry point
├── requirements.txt  # Python dependencies
├── Dockerfile       # Docker image configuration
└── docker-compose.yml # Docker Compose configuration
```

## How It Works

1. **Page Processing**:
   - Downloads only the HTML content of the comic page
   - Ignores unnecessary resources (CSS, JS, etc.)
   - Extracts image URLs efficiently

2. **Image Download**:
   - Downloads images in parallel for better performance
   - Uses streaming to optimize memory usage
   - Automatically cleans up images after PDF creation

3. **PDF Generation**:
   - Creates PDF with original image dimensions
   - Optimizes memory usage during creation
   - Automatically deletes the PDF after download

4. **File Management**:
   - All temporary files are automatically cleaned up
   - Images are deleted after being added to the PDF
   - PDFs are deleted immediately after successful download

## Notes

- The application is optimized for memory usage and performance
- All files (images and PDFs) are automatically cleaned up
- The application runs on port 5000 by default
- For production deployment, consider adding proper security measures

## Troubleshooting

1. If downloads are not starting:
   - Check if the URL is from ReadAllComics
   - Ensure the URL format is correct
   - Check browser console for any errors

2. If PDFs are not downloading:
   - Check your browser's download settings
   - Ensure you have enough disk space
   - Check the application logs for errors

3. If the application is slow:
   - Check your internet connection
   - The site might be rate-limiting requests
   - Try reducing the number of parallel downloads in config.py

## Logging

The application provides detailed logging:
- General operations in the console
- Detailed logs in `comic_downloader.log`
- Download progress and error information
- File cleanup confirmations