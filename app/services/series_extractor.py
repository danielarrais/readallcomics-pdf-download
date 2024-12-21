from bs4 import BeautifulSoup
import requests

class SeriesExtractor:
    def __init__(self, url):
        self.url = url
        self.chapters = []

    def extract_chapters(self):
        try:
            response = requests.get(self.url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontra a div que contém a lista de capítulos
            chapter_list = soup.find('div', class_='group-box list')
            if not chapter_list:
                return []

            # Encontra todos os links dos capítulos
            chapters = []
            for link in chapter_list.find_all('a'):
                chapter = {
                    'title': link.text.strip(),
                    'url': link['href'],
                }
                chapters.append(chapter)

            self.chapters = chapters
            return chapters

        except Exception as e:
            print(f"Error extracting chapters: {str(e)}")
            return [] 