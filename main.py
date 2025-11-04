#!/usr/bin/env python3
"""
Immich People Albums Sync
Программа для автоматического добавления фотографий распознанных людей в альбомы
"""

import os
import sys
import logging
import yaml
import requests
from typing import List, Dict, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('immich-people-albums.log')
    ]
)
logger = logging.getLogger(__name__)


class ImmichClient:
    """Клиент для работы с Immich API"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, email: Optional[str] = None, password: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.session = requests.Session()
        self.api_key = api_key
        self.email = email
        self.password = password
        
        # Настройка аутентификации
        if api_key:
            self.session.headers.update({'x-api-key': api_key})
        elif email and password:
            self._login(email, password)
        else:
            raise ValueError("Необходимо указать либо api_key, либо email/password")
    
    def _login(self, email: str, password: str):
        """Аутентификация через email/password"""
        try:
            response = self.session.post(
                f"{self.api_url}/auth/login",
                json={"email": email, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            # Сохраняем токен для последующих запросов
            if 'accessToken' in data:
                self.session.headers.update({'Authorization': f"Bearer {data['accessToken']}"})
            logger.info("Успешная аутентификация")
        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
            raise
    
    def get_all_people(self, with_hidden: bool = False) -> List[Dict]:
        """Получить список всех людей"""
        try:
            response = self.session.get(
                f"{self.api_url}/people",
                params={"withHidden": with_hidden, "size": 1000}
            )
            response.raise_for_status()
            data = response.json()
            return data.get('people', [])
        except Exception as e:
            logger.error(f"Ошибка получения списка людей: {e}")
            return []
    
    def find_person_by_name(self, name: str) -> Optional[Dict]:
        """Найти человека по имени"""
        people = self.get_all_people()
        for person in people:
            if person.get('name') == name:
                return person
        return None
    
    def get_person_by_id(self, person_id: str) -> Optional[Dict]:
        """Получить человека по ID"""
        try:
            response = self.session.get(f"{self.api_url}/people/{person_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения человека {person_id}: {e}")
            return None
    
    def search_assets_by_person(self, person_id: str, limit: int = 1000) -> List[str]:
        """Получить список ID активов (фото) для конкретного человека"""
        all_asset_ids = []
        page = 1
        page_size = min(limit, 1000) if limit > 0 else 1000
        
        try:
            while True:
                # Используем эндпоинт поиска с фильтром по personIds
                response = self.session.post(
                    f"{self.api_url}/search/metadata",
                    json={
                        "personIds": [person_id],
                        "size": page_size,
                        "page": page
                    }
                )
                response.raise_for_status()
                data = response.json()
                # Извлекаем ID активов из структуры ответа SearchResponseDto
                # Ответ содержит assets.items, где items - массив AssetResponseDto
                assets_data = data.get('assets', {})
                assets = assets_data.get('items', [])
                
                if not assets:
                    break
                
                asset_ids = [asset['id'] for asset in assets if 'id' in asset]
                all_asset_ids.extend(asset_ids)
                
                # Проверяем, есть ли следующая страница
                next_page = assets_data.get('nextPage')
                if not next_page or (limit > 0 and len(all_asset_ids) >= limit):
                    break
                
                page += 1
                
                # Ограничение по лимиту
                if limit > 0 and len(all_asset_ids) >= limit:
                    all_asset_ids = all_asset_ids[:limit]
                    break
            
            return all_asset_ids
        except Exception as e:
            logger.error(f"Ошибка поиска активов для человека {person_id}: {e}")
            return all_asset_ids
    
    def get_all_albums(self) -> List[Dict]:
        """Получить список всех альбомов"""
        try:
            response = self.session.get(f"{self.api_url}/albums")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка получения списка альбомов: {e}")
            return []
    
    def find_album_by_name(self, name: str) -> Optional[Dict]:
        """Найти альбом по имени"""
        albums = self.get_all_albums()
        for album in albums:
            if album.get('albumName') == name:
                return album
        return None
    
    def create_album(self, name: str) -> Optional[Dict]:
        """Создать новый альбом"""
        try:
            response = self.session.post(
                f"{self.api_url}/albums",
                json={"albumName": name}
            )
            response.raise_for_status()
            album = response.json()
            logger.info(f"Создан альбом: {name} (ID: {album.get('id')})")
            return album
        except Exception as e:
            logger.error(f"Ошибка создания альбома {name}: {e}")
            return None
    
    def get_album_assets(self, album_id: str) -> List[str]:
        """Получить список ID активов в альбоме"""
        try:
            response = self.session.get(f"{self.api_url}/albums/{album_id}")
            response.raise_for_status()
            album = response.json()
            assets = album.get('assets', [])
            return [asset['id'] for asset in assets if 'id' in asset]
        except Exception as e:
            logger.error(f"Ошибка получения активов альбома {album_id}: {e}")
            return []
    
    def add_assets_to_album(self, album_id: str, asset_ids: List[str]) -> bool:
        """Добавить активы в альбом"""
        if not asset_ids:
            return True
        
        try:
            # Разбиваем на батчи по 100 для избежания слишком больших запросов
            batch_size = 100
            for i in range(0, len(asset_ids), batch_size):
                batch = asset_ids[i:i + batch_size]
                response = self.session.put(
                    f"{self.api_url}/albums/{album_id}/assets",
                    json={"ids": batch}
                )
                response.raise_for_status()
            logger.info(f"Добавлено {len(asset_ids)} активов в альбом {album_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления активов в альбом {album_id}: {e}")
            return False


class PeopleAlbumsSync:
    """Основной класс для синхронизации людей с альбомами"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.client = self._create_client()
        
        # Устанавливаем уровень логирования из конфига
        log_level = self.config.get('options', {}).get('log_level', 'INFO')
        logging.getLogger().setLevel(getattr(logging, log_level))
    
    def _load_config(self, config_path: str) -> Dict:
        """Загрузить конфигурацию из YAML файла"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Конфигурация загружена из {config_path}")
            return config
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            raise
    
    def _create_client(self) -> ImmichClient:
        """Создать клиент Immich"""
        immich_config = self.config['immich']
        api_key = immich_config.get('api_key')
        email = immich_config.get('email')
        password = immich_config.get('password')
        url = immich_config['url']
        
        return ImmichClient(url, api_key=api_key, email=email, password=password)
    
    def sync_person_to_album(self, mapping: Dict) -> bool:
        """Синхронизировать активы человека с альбомом"""
        person_name = mapping.get('person_name')
        person_id = mapping.get('person_id')
        album_name = mapping.get('album_name')
        album_id = mapping.get('album_id')
        
        logger.info(f"Обработка: {person_name} -> {album_name}")
        
        # Находим или получаем человека
        if person_id:
            person = self.client.get_person_by_id(person_id)
        else:
            person = self.client.find_person_by_name(person_name)
        
        if not person:
            logger.warning(f"Человек не найден: {person_name}")
            return False
        
        person_id = person['id']
        logger.info(f"Найден человек: {person_name} (ID: {person_id})")
        
        # Находим или создаем альбом
        if album_id:
            album = self.client.get_all_albums()
            album = next((a for a in album if a.get('id') == album_id), None)
        else:
            album = self.client.find_album_by_name(album_name)
        
        if not album:
            album = self.client.create_album(album_name)
            if not album:
                logger.error(f"Не удалось создать альбом: {album_name}")
                return False
        
        album_id = album['id']
        logger.info(f"Используется альбом: {album_name} (ID: {album_id})")
        
        # Получаем активы человека
        person_assets = self.client.search_assets_by_person(person_id)
        logger.info(f"Найдено {len(person_assets)} активов для {person_name}")
        
        if not person_assets:
            logger.info(f"Нет активов для добавления")
            return True
        
        # Если нужно пропускать существующие
        skip_existing = self.config.get('options', {}).get('skip_existing', True)
        if skip_existing:
            existing_assets = set(self.client.get_album_assets(album_id))
            person_assets = [aid for aid in person_assets if aid not in existing_assets]
            logger.info(f"После фильтрации осталось {len(person_assets)} новых активов")
        
        if not person_assets:
            logger.info(f"Все активы уже в альбоме")
            return True
        
        # Ограничение по количеству активов
        max_assets = self.config.get('options', {}).get('max_assets_per_run', 0)
        if max_assets > 0 and len(person_assets) > max_assets:
            logger.info(f"Ограничение: добавляем только {max_assets} из {len(person_assets)} активов")
            person_assets = person_assets[:max_assets]
        
        # Добавляем активы в альбом
        success = self.client.add_assets_to_album(album_id, person_assets)
        
        if success:
            logger.info(f"Успешно обработано: {person_name} -> {album_name} ({len(person_assets)} активов)")
        else:
            logger.error(f"Ошибка при обработке: {person_name} -> {album_name}")
        
        return success
    
    def run(self):
        """Запустить синхронизацию"""
        logger.info("=" * 60)
        logger.info("Запуск синхронизации людей с альбомами")
        logger.info("=" * 60)
        
        mappings = self.config.get('mappings', [])
        if not mappings:
            logger.warning("Нет соответствий для обработки")
            return
        
        success_count = 0
        total_count = len(mappings)
        
        for mapping in mappings:
            try:
                if self.sync_person_to_album(mapping):
                    success_count += 1
            except Exception as e:
                logger.error(f"Ошибка при обработке соответствия: {e}", exc_info=True)
        
        logger.info("=" * 60)
        logger.info(f"Синхронизация завершена: {success_count}/{total_count} успешно")
        logger.info("=" * 60)


def main():
    """Главная функция"""
    config_path = os.environ.get('CONFIG_PATH', 'config.yaml')
    
    try:
        sync = PeopleAlbumsSync(config_path)
        sync.run()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

