import requests
import base64


"""Класс для работы с API"""
class APIClient:
    def __init__(self, base_url="http://82.202.129.245:8002"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.timeout = 500
    
    def detect_image(self, image_path):
        """Отправка изображения на удаленный сервер для обработки"""
        try:
            api_url = f"{self.base_url}/detect_images"
            
            with open(image_path, 'rb') as f:
                response = self.session.post(
                    api_url,
                    files={'file': f},
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            data = response.json()
            
            image_bytes = base64.b64decode(data["image_base64"])
            return image_bytes, data["detection_results"]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка соединения с сервером {self.base_url}: {str(e)}")
        except Exception as e:
            raise Exception(f"Ошибка обработки ответа сервера: {str(e)}")