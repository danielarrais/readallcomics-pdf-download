from dataclasses import dataclass
from typing import List, Tuple, Optional
from pathlib import Path
import os
import requests
from bs4 import BeautifulSoup
from PIL import Image
import fitz
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import current_app
from app.utils.logger import logger
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

@dataclass
class ImageInfo:
    path: str
    index: int
    width: int
    height: int

class ComicService:
    def __init__(self):
        self.selector = "body > center:nth-child(5) > center > div:nth-child(2)"
        self.compress_images = True  # Será sobrescrito pela escolha do usuário
        self.target_width = 1920
        self.max_workers = int(os.environ.get('MAX_WORKERS', '5'))
        self.session = self._create_session()
        logger.info("ComicService initialized with selector: %s, max_workers: %d", 
                   self.selector, self.max_workers)
    
    def _create_session(self) -> requests.Session:
        """
        Cria uma sessão HTTP com retry e timeouts
        """
        session = requests.Session()
        
        # Configurar retry para requisições falhas
        retry_strategy = Retry(
            total=3,  # número total de tentativas
            backoff_factor=1,  # tempo entre tentativas
            status_forcelist=[500, 502, 503, 504]  # códigos HTTP para retry
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers padrão
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        })
        
        return session
    
    def process_comic(self, url: str) -> str:
        """
        Processa uma URL de quadrinho e retorna o nome do PDF gerado
        """
        logger.info("Starting comic processing for URL: %s", url)
        pdf_name = self._generate_pdf_name(url)
        pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_name)
        logger.info("PDF will be saved as: %s", pdf_path)
        
        try:
            images_info = self._download_images(url)
            if not images_info:
                raise ValueError("No images were downloaded")
                
            logger.info("Successfully downloaded %d images", len(images_info))
            self._create_pdf(images_info, pdf_path)
            logger.info("Successfully created PDF: %s", pdf_path)
            
            return pdf_name
        except Exception as e:
            logger.error("Failed to process comic: %s", str(e))
            self._cleanup_on_error(images_info if 'images_info' in locals() else None)
            raise
    
    def _generate_pdf_name(self, url: str) -> str:
        """
        Gera um nome seguro para o PDF baseado na URL
        """
        base_name = url.rstrip('/').split('/')[-1]
        # Remove caracteres inválidos
        safe_name = "".join(c for c in base_name if c.isalnum() or c in ('-', '_'))
        return f"{safe_name}.pdf"
    
    def _cleanup_on_error(self, images_info: Optional[List[ImageInfo]] = None) -> None:
        """
        Limpa arquivos temporários em caso de erro
        """
        if images_info:
            for img_info in images_info:
                try:
                    if os.path.exists(img_info.path):
                        os.remove(img_info.path)
                        logger.debug("Cleaned up temporary file: %s", img_info.path)
                except Exception as e:
                    logger.error("Error cleaning up file %s: %s", img_info.path, str(e))
    
    def _download_images(self, url: str) -> List[ImageInfo]:
        """
        Faz download das imagens e retorna suas informações
        """
        logger.info("Starting image download process")
        images_dir = Path(current_app.config['IMAGES_FOLDER'])
        images_dir.mkdir(exist_ok=True)
        logger.debug("Using images directory: %s", images_dir)
        
        try:
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
            
        except Exception as e:
            logger.error("Error in download process: %s", str(e))
            raise
    
    def _get_image_urls(self, url: str) -> List[str]:
        """
        Extrai URLs das imagens da página
        """
        logger.info("Fetching image URLs from: %s", url)
        
        try:
            response = self.session.get(
                url,
                stream=True,
                verify=False,
                timeout=(5, 15)  # (connect timeout, read timeout)
            )
            response.raise_for_status()
            logger.debug("Successfully fetched page content")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            target_div = soup.select_one(self.selector)
            
            if not target_div:
                raise ValueError(f"Target element not found using selector: {self.selector}")
            
            img_urls = [img['src'] for img in target_div.find_all("img") if 'src' in img.attrs]
            
            if not img_urls:
                raise ValueError("No images found in target element")
            
            logger.info("Successfully extracted %d image URLs", len(img_urls))
            return img_urls
            
        except requests.RequestException as e:
            logger.error("Network error fetching page: %s", str(e))
            raise
        except Exception as e:
            logger.error("Error parsing page: %s", str(e))
            raise
    
    def _parallel_download(self, urls: List[str], output_dir: Path) -> List[Tuple[str, int]]:
        """
        Realiza download paralelo das imagens com controle de erros
        """
        logger.info("Starting parallel download of %d images with %d workers", 
                   len(urls), self.max_workers)
        img_paths = []
        failed_downloads = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._download_single_image, url, idx, output_dir): (idx, url)
                for idx, url in enumerate(urls)
            }
            
            for future in as_completed(futures):
                idx, url = futures[future]
                try:
                    img_path, idx = future.result()
                    img_paths.append((img_path, idx))
                    logger.debug("Successfully downloaded image %d/%d", idx + 1, len(urls))
                except Exception as e:
                    logger.error("Failed to download image %d from %s: %s", idx + 1, url, str(e))
                    failed_downloads.append((idx + 1, url))
        
        if failed_downloads:
            failed_msg = "\n".join(f"Image {idx}: {url}" for idx, url in failed_downloads)
            logger.error("Failed downloads:\n%s", failed_msg)
            raise ValueError(f"Failed to download {len(failed_downloads)} images")
        
        logger.info("Successfully completed all downloads")
        return img_paths
    
    def _download_single_image(self, url: str, idx: int, output_dir: Path) -> Tuple[str, int]:
        """
        Faz download de uma única imagem com retry
        """
        logger.debug("Downloading image %d from %s", idx + 1, url)
        try:
            response = self.session.get(url, stream=True, timeout=(5, 30))
            response.raise_for_status()
            
            img_path = output_dir / f"image_{idx + 1}.jpg"
            with open(img_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if self.compress_images:
                self._compress_image(str(img_path))
            
            logger.debug("Successfully saved image %d to %s", idx + 1, img_path)
            return str(img_path), idx
            
        except Exception as e:
            logger.error("Error downloading image %d: %s", idx + 1, str(e))
            raise
    
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

    def _compress_image(self, image_path: str) -> None:
        """
        Comprime a imagem para reduzir o tamanho do arquivo final
        """
        if not self.compress_images:
            return

        try:
            with Image.open(image_path) as img:
                # Converte para RGB se necessário (remove canal alpha)
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    img = img.convert('RGB')
                
                # Calcula as dimensões mantendo proporção
                if img.width > self.target_width:
                    ratio = self.target_width / img.width
                    new_size = (self.target_width, int(img.height * ratio))
                    logger.debug("Resizing image %s from %dx%d to %dx%d", 
                               image_path, img.width, img.height, 
                               new_size[0], new_size[1])
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Reduz a quantidade de cores
                img = img.quantize(colors=256, method=2).convert('RGB')
                
                # Comprime a imagem com configurações otimizadas
                logger.debug("Compressing image %s", image_path)
                img.save(
                    image_path,
                    'JPEG',
                    quality=40,  # Qualidade JPEG reduzida ainda mais
                    optimize=True,  # Otimização adicional
                    progressive=True,  # JPEG progressivo
                    subsampling='4:2:0',  # Subamostragem de crominância mais agressiva
                )
                
                logger.info("Successfully compressed image: %s", image_path)
                
        except Exception as e:
            logger.error("Error compressing image %s: %s", image_path, str(e))
            raise