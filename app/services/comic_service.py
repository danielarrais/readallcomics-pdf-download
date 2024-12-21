from dataclasses import dataclass
from typing import List, Tuple
from pathlib import Path
import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
import fitz
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import current_app
from app.utils.logger import logger

@dataclass
class ImageInfo:
    path: str
    index: int
    width: int
    height: int

class ComicService:
    def __init__(self):
        self.selector = "body > center:nth-child(5) > center > div:nth-child(2)"
        logger.info("ComicService initialized with selector: %s", self.selector)
    
    def process_comic(self, url: str) -> str:
        """
        Processa uma URL de quadrinho e retorna o nome do PDF gerado
        """
        logger.info("Starting comic processing for URL: %s", url)
        pdf_name = f"{url.rstrip('/').split('/')[-1]}.pdf"
        pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_name)
        logger.info("PDF will be saved as: %s", pdf_path)
        
        try:
            images_info = self._download_images(url)
            logger.info("Successfully downloaded %d images", len(images_info))
            
            self._create_pdf(images_info, pdf_path)
            logger.info("Successfully created PDF: %s", pdf_path)
            
            return pdf_name
        except Exception as e:
            logger.error("Failed to process comic: %s", str(e))
            raise
    
    def _download_images(self, url: str) -> List[ImageInfo]:
        """
        Faz download das imagens e retorna suas informações
        """
        logger.info("Starting image download process")
        images_dir = Path(current_app.config['IMAGES_FOLDER'])
        images_dir.mkdir(exist_ok=True)
        logger.debug("Using images directory: %s", images_dir)
        
        # Obtém URLs das imagens
        img_urls = self._get_image_urls(url)
        logger.info("Found %d image URLs to download", len(img_urls))
        
        # Download paralelo
        img_paths = self._parallel_download(img_urls, images_dir)
        logger.info("Completed parallel download of %d images", len(img_paths))
        
        # Processa informações das imagens
        images_info = [self._get_image_info(path, idx) for path, idx in sorted(img_paths)]
        logger.debug("Processed information for %d images", len(images_info))
        return images_info
    
    def _get_image_urls(self, url: str) -> List[str]:
        """
        Extrai URLs das imagens da página
        """
        logger.info("Fetching image URLs from: %s", url)
        
        # Headers para simular um navegador e otimizar o carregamento
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        # Configurar a sessão para otimizar o carregamento
        session = requests.Session()
        session.headers.update(headers)
        
        # Desabilitar carregamento de recursos extras
        response = session.get(
            url,
            stream=True,  # Usar streaming para melhor performance
            verify=False,  # Ignorar verificação SSL para melhor performance
            timeout=10,    # Timeout razoável
        )
        response.raise_for_status()
        logger.debug("Successfully fetched page content")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        target_div = soup.select_one(self.selector)
        
        if not target_div:
            logger.error("Target element not found using selector: %s", self.selector)
            raise ValueError("Target element not found")
        
        img_urls = [img['src'] for img in target_div.find_all("img") if 'src' in img.attrs]
        
        if not img_urls:
            logger.error("No images found in target element")
            raise ValueError("No images found")
        
        logger.info("Successfully extracted %d image URLs", len(img_urls))
        return img_urls
    
    def _parallel_download(self, urls: List[str], output_dir: Path) -> List[Tuple[str, int]]:
        """
        Realiza download paralelo das imagens
        """
        logger.info("Starting parallel download of %d images", len(urls))
        img_paths = []
        max_workers = current_app.config['MAX_WORKERS']
        logger.debug("Using %d workers for parallel download", max_workers)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._download_single_image, url, idx, output_dir): idx 
                for idx, url in enumerate(urls)
            }
            
            for future in as_completed(futures):
                try:
                    img_path, idx = future.result()
                    img_paths.append((img_path, idx))
                    logger.debug("Successfully downloaded image %d/%d", idx + 1, len(urls))
                except Exception as e:
                    logger.error("Failed to download image %d: %s", futures[future], str(e))
                    raise
        
        logger.info("Completed parallel download of all images")
        return img_paths
    
    def _download_single_image(self, url: str, idx: int, output_dir: Path) -> Tuple[str, int]:
        """
        Faz download de uma única imagem
        """
        logger.debug("Downloading image %d from %s", idx + 1, url)
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        img_path = output_dir / f"image_{idx + 1}.jpg"
        with open(img_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        
        logger.debug("Successfully saved image %d to %s", idx + 1, img_path)
        return str(img_path), idx
    
    def _get_image_info(self, img_path: str, idx: int) -> ImageInfo:
        """
        Obtém informações de uma imagem
        """
        logger.debug("Getting information for image %d: %s", idx + 1, img_path)
        with Image.open(img_path) as img:
            info = ImageInfo(
                path=img_path,
                index=idx,
                width=img.width,
                height=img.height
            )
            logger.debug("Image %d info - width: %d, height: %d", idx + 1, info.width, info.height)
            return info
    
    def _create_pdf(self, images_info: List[ImageInfo], output_path: str):
        """
        Cria o PDF a partir das imagens
        """
        logger.info("Starting PDF creation with %d images", len(images_info))
        pdf = fitz.open()
        
        for idx, img_info in enumerate(images_info, 1):
            logger.debug("Processing image %d/%d for PDF", idx, len(images_info))
            # Adiciona página com tamanho da imagem
            page = pdf.new_page(width=img_info.width, height=img_info.height)
            
            # Adiciona imagem
            rect = fitz.Rect(0, 0, img_info.width, img_info.height)
            page.insert_image(rect, filename=img_info.path)
            logger.debug("Added image %d to PDF", idx)
            
            # Remove imagem após uso
            try:
                os.remove(img_info.path)
                logger.debug("Removed temporary image file: %s", img_info.path)
            except Exception as e:
                logger.error("Error removing image %s: %s", img_info.path, str(e))
        
        pdf.save(output_path)
        pdf.close()
        logger.info("Successfully created and saved PDF to: %s", output_path) 