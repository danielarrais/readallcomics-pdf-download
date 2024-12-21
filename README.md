# Comic PDF Downloader

A web application to download comics from ReadAllComics and convert them to PDF format, with optional image compression for smaller file sizes.

## Features

- Web interface for easy comic downloading
- Optional image compression for smaller PDF files
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

## Configuration

The application can be configured using environment variables in the `docker-compose.yml` file:

| Variable | Description | Default |
|----------|-------------|---------|
| COMPRESS_IMAGES | Enable/disable image compression | true |
| MAX_WORKERS | Number of parallel downloads | 5 |

Example of disabling image compression:
```bash
COMPRESS_IMAGES=false docker-compose up --build
```

## Image Compression

When enabled (default), the application will:
- Reduce image resolution if larger than 1920px width
- Maintain original aspect ratio
- Convert images to optimized JPEG format
- Reduce color palette to 256 colors
- Apply aggressive compression settings:
  - Quality level: 40%
  - Progressive JPEG encoding
  - Chroma subsampling (4:2:0)
  - Color quantization
  - Additional optimization passes
- Remove alpha channels (convert to RGB)

This results in very small PDF files while maintaining readable image quality for comics. The compression is optimized for manga and comic content, where high color fidelity is less critical than readability.

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
   - Optionally compresses images to Full HD
   - Automatically cleans up images after PDF creation

3. **PDF Generation**:
   - Creates PDF with compressed or original image dimensions
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
- Image compression can significantly reduce PDF file size

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
   - Consider enabling image compression to reduce memory usage

## Logging

The application provides detailed logging:
- General operations in the console
- Detailed logs in `comic_downloader.log`
- Download progress and error information
- File cleanup confirmations
- Image compression statistics and results