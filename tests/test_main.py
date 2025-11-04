#!/usr/bin/env python3
"""
Тесты для Immich People Albums Sync
"""

import pytest
import yaml
from unittest.mock import Mock, patch, MagicMock, call
from requests.exceptions import RequestException, HTTPError
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import ImmichClient, PeopleAlbumsSync


class TestImmichClient:
    """Тесты для ImmichClient"""
    
    @patch('main.requests.Session')
    def test_init_with_api_key(self, mock_session_class):
        """Тест инициализации с API ключом"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="test-key")
        
        assert client.base_url == "http://test.com"
        assert client.api_url == "http://test.com/api"
        assert client.api_key == "test-key"
        mock_session.headers.update.assert_called_once_with({'x-api-key': 'test-key'})
    
    @patch('main.requests.Session')
    def test_init_with_email_password(self, mock_session_class):
        """Тест инициализации с email/password"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"accessToken": "token123"}
        mock_response.raise_for_status = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", email="test@test.com", password="pass")
        
        assert client.email == "test@test.com"
        assert client.password == "pass"
        mock_session.post.assert_called_once()
        mock_session.headers.update.assert_called_with({'Authorization': 'Bearer token123'})
    
    def test_init_without_credentials(self):
        """Тест инициализации без учетных данных"""
        with pytest.raises(ValueError, match="Необходимо указать"):
            ImmichClient("http://test.com")
    
    @patch('main.requests.Session')
    def test_login_failure(self, mock_session_class):
        """Тест неудачной аутентификации"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("Auth failed")
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        with pytest.raises(HTTPError):
            ImmichClient("http://test.com", email="test@test.com", password="wrong")
    
    @patch('main.requests.Session')
    def test_get_all_people(self, mock_session_class):
        """Тест получения списка людей"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "people": [
                {"id": "1", "name": "Иван"},
                {"id": "2", "name": "Мария"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        people = client.get_all_people()
        
        assert len(people) == 2
        assert people[0]["name"] == "Иван"
        mock_session.get.assert_called_once()
    
    @patch('main.requests.Session')
    def test_get_all_people_empty(self, mock_session_class):
        """Тест получения пустого списка людей"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"people": []}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        people = client.get_all_people()
        
        assert people == []
    
    @patch('main.requests.Session')
    def test_get_all_people_error(self, mock_session_class):
        """Тест обработки ошибки при получении людей"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = HTTPError("Server error")
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        people = client.get_all_people()
        
        assert people == []
    
    @patch('main.requests.Session')
    def test_find_person_by_name(self, mock_session_class):
        """Тест поиска человека по имени"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "people": [
                {"id": "1", "name": "Иван"},
                {"id": "2", "name": "Мария"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        person = client.find_person_by_name("Иван")
        
        assert person is not None
        assert person["id"] == "1"
        assert person["name"] == "Иван"
    
    @patch('main.requests.Session')
    def test_find_person_by_name_not_found(self, mock_session_class):
        """Тест поиска несуществующего человека"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "people": [
                {"id": "1", "name": "Иван"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        person = client.find_person_by_name("Несуществующий")
        
        assert person is None
    
    @patch('main.requests.Session')
    def test_get_person_by_id(self, mock_session_class):
        """Тест получения человека по ID"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"id": "123", "name": "Иван"}
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        person = client.get_person_by_id("123")
        
        assert person is not None
        assert person["id"] == "123"
        assert person["name"] == "Иван"
    
    @patch('main.requests.Session')
    def test_search_assets_by_person(self, mock_session_class):
        """Тест поиска активов по человеку"""
        mock_session = Mock()
        
        # Первая страница
        mock_response1 = Mock()
        mock_response1.json.return_value = {
            "assets": {
                "items": [
                    {"id": "asset1"},
                    {"id": "asset2"}
                ],
                "nextPage": "page2"
            }
        }
        mock_response1.raise_for_status = Mock()
        
        # Вторая страница (последняя)
        mock_response2 = Mock()
        mock_response2.json.return_value = {
            "assets": {
                "items": [
                    {"id": "asset3"}
                ],
                "nextPage": None
            }
        }
        mock_response2.raise_for_status = Mock()
        
        mock_session.post.side_effect = [mock_response1, mock_response2]
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        assets = client.search_assets_by_person("person123")
        
        assert len(assets) == 3
        assert "asset1" in assets
        assert "asset2" in assets
        assert "asset3" in assets
        assert mock_session.post.call_count == 2
    
    @patch('main.requests.Session')
    def test_search_assets_by_person_empty(self, mock_session_class):
        """Тест поиска активов когда их нет"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "assets": {
                "items": [],
                "nextPage": None
            }
        }
        mock_response.raise_for_status = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        assets = client.search_assets_by_person("person123")
        
        assert assets == []
    
    @patch('main.requests.Session')
    def test_get_all_albums(self, mock_session_class):
        """Тест получения всех альбомов"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "album1", "albumName": "Альбом 1"},
            {"id": "album2", "albumName": "Альбом 2"}
        ]
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        albums = client.get_all_albums()
        
        assert len(albums) == 2
        assert albums[0]["albumName"] == "Альбом 1"
    
    @patch('main.requests.Session')
    def test_find_album_by_name(self, mock_session_class):
        """Тест поиска альбома по имени"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = [
            {"id": "album1", "albumName": "Альбом 1"},
            {"id": "album2", "albumName": "Альбом 2"}
        ]
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        album = client.find_album_by_name("Альбом 2")
        
        assert album is not None
        assert album["id"] == "album2"
    
    @patch('main.requests.Session')
    def test_create_album(self, mock_session_class):
        """Тест создания альбома"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {"id": "new-album", "albumName": "Новый альбом"}
        mock_response.raise_for_status = Mock()
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        album = client.create_album("Новый альбом")
        
        assert album is not None
        assert album["id"] == "new-album"
        assert album["albumName"] == "Новый альбом"
        mock_session.post.assert_called_once()
    
    @patch('main.requests.Session')
    def test_get_album_assets(self, mock_session_class):
        """Тест получения активов альбома"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.json.return_value = {
            "id": "album1",
            "assets": [
                {"id": "asset1"},
                {"id": "asset2"}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        assets = client.get_album_assets("album1")
        
        assert len(assets) == 2
        assert "asset1" in assets
        assert "asset2" in assets
    
    @patch('main.requests.Session')
    def test_add_assets_to_album(self, mock_session_class):
        """Тест добавления активов в альбом"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_session.put.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        result = client.add_assets_to_album("album1", ["asset1", "asset2"])
        
        assert result is True
        mock_session.put.assert_called_once()
        call_args = mock_session.put.call_args
        assert call_args[0][0] == "http://test.com/api/albums/album1/assets"
        assert call_args[1]["json"]["ids"] == ["asset1", "asset2"]
    
    @patch('main.requests.Session')
    def test_add_assets_to_album_batch(self, mock_session_class):
        """Тест добавления большого количества активов (батчинг)"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_session.put.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        # Создаем 250 активов (должно быть 3 батча по 100)
        assets = [f"asset{i}" for i in range(250)]
        result = client.add_assets_to_album("album1", assets)
        
        assert result is True
        assert mock_session.put.call_count == 3
    
    @patch('main.requests.Session')
    def test_add_assets_to_album_empty(self, mock_session_class):
        """Тест добавления пустого списка активов"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        client = ImmichClient("http://test.com", api_key="key")
        result = client.add_assets_to_album("album1", [])
        
        assert result is True
        mock_session.put.assert_not_called()


class TestPeopleAlbumsSync:
    """Тесты для PeopleAlbumsSync"""
    
    def create_test_config(self, tmp_path):
        """Создает тестовый конфиг файл"""
        config = {
            'immich': {
                'url': 'http://test.com',
                'api_key': 'test-key'
            },
            'mappings': [
                {
                    'person_name': 'Иван',
                    'person_id': None,
                    'album_name': 'Альбом Ивана',
                    'album_id': None
                }
            ],
            'options': {
                'skip_existing': True,
                'max_assets_per_run': 0,
                'log_level': 'INFO'
            }
        }
        config_path = tmp_path / "config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        return str(config_path)
    
    @patch('main.ImmichClient')
    def test_load_config(self, mock_client_class, tmp_path):
        """Тест загрузки конфигурации"""
        config_path = self.create_test_config(tmp_path)
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        sync = PeopleAlbumsSync(config_path)
        
        assert sync.config['immich']['url'] == 'http://test.com'
        assert len(sync.config['mappings']) == 1
    
    @patch('main.ImmichClient')
    def test_sync_person_to_album_success(self, mock_client_class, tmp_path):
        """Тест успешной синхронизации"""
        config_path = self.create_test_config(tmp_path)
        
        mock_client = Mock()
        mock_client.find_person_by_name.return_value = {
            'id': 'person1',
            'name': 'Иван'
        }
        mock_client.find_album_by_name.return_value = {
            'id': 'album1',
            'albumName': 'Альбом Ивана'
        }
        mock_client.search_assets_by_person.return_value = ['asset1', 'asset2', 'asset3']
        mock_client.get_album_assets.return_value = []  # Нет существующих
        mock_client.add_assets_to_album.return_value = True
        mock_client_class.return_value = mock_client
        
        sync = PeopleAlbumsSync(config_path)
        result = sync.sync_person_to_album(sync.config['mappings'][0])
        
        assert result is True
        mock_client.find_person_by_name.assert_called_once_with('Иван')
        mock_client.search_assets_by_person.assert_called_once_with('person1')
        mock_client.add_assets_to_album.assert_called_once_with('album1', ['asset1', 'asset2', 'asset3'])
    
    @patch('main.ImmichClient')
    def test_sync_person_to_album_create_album(self, mock_client_class, tmp_path):
        """Тест создания альбома если его нет"""
        config_path = self.create_test_config(tmp_path)
        
        mock_client = Mock()
        mock_client.find_person_by_name.return_value = {
            'id': 'person1',
            'name': 'Иван'
        }
        mock_client.find_album_by_name.return_value = None  # Альбом не найден
        mock_client.create_album.return_value = {
            'id': 'new-album',
            'albumName': 'Альбом Ивана'
        }
        mock_client.search_assets_by_person.return_value = ['asset1']
        mock_client.get_album_assets.return_value = []
        mock_client.add_assets_to_album.return_value = True
        mock_client_class.return_value = mock_client
        
        sync = PeopleAlbumsSync(config_path)
        result = sync.sync_person_to_album(sync.config['mappings'][0])
        
        assert result is True
        mock_client.create_album.assert_called_once_with('Альбом Ивана')
    
    @patch('main.ImmichClient')
    def test_sync_person_to_album_person_not_found(self, mock_client_class, tmp_path):
        """Тест когда человек не найден"""
        config_path = self.create_test_config(tmp_path)
        
        mock_client = Mock()
        mock_client.find_person_by_name.return_value = None
        mock_client_class.return_value = mock_client
        
        sync = PeopleAlbumsSync(config_path)
        result = sync.sync_person_to_album(sync.config['mappings'][0])
        
        assert result is False
        mock_client.search_assets_by_person.assert_not_called()
    
    @patch('main.ImmichClient')
    def test_sync_person_to_album_skip_existing(self, mock_client_class, tmp_path):
        """Тест пропуска уже существующих активов"""
        config_path = self.create_test_config(tmp_path)
        
        mock_client = Mock()
        mock_client.find_person_by_name.return_value = {
            'id': 'person1',
            'name': 'Иван'
        }
        mock_client.find_album_by_name.return_value = {
            'id': 'album1',
            'albumName': 'Альбом Ивана'
        }
        mock_client.search_assets_by_person.return_value = ['asset1', 'asset2', 'asset3']
        mock_client.get_album_assets.return_value = ['asset2']  # asset2 уже в альбоме
        mock_client.add_assets_to_album.return_value = True
        mock_client_class.return_value = mock_client
        
        sync = PeopleAlbumsSync(config_path)
        result = sync.sync_person_to_album(sync.config['mappings'][0])
        
        assert result is True
        # Должны добавить только asset1 и asset3
        mock_client.add_assets_to_album.assert_called_once_with('album1', ['asset1', 'asset3'])
    
    @patch('main.ImmichClient')
    def test_sync_person_to_album_max_assets_limit(self, mock_client_class, tmp_path):
        """Тест ограничения количества активов"""
        config_path = self.create_test_config(tmp_path)
        # Обновляем конфиг для установки лимита
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        config['options']['max_assets_per_run'] = 2
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        
        mock_client = Mock()
        mock_client.find_person_by_name.return_value = {
            'id': 'person1',
            'name': 'Иван'
        }
        mock_client.find_album_by_name.return_value = {
            'id': 'album1',
            'albumName': 'Альбом Ивана'
        }
        mock_client.search_assets_by_person.return_value = ['asset1', 'asset2', 'asset3', 'asset4', 'asset5']
        mock_client.get_album_assets.return_value = []
        mock_client.add_assets_to_album.return_value = True
        mock_client_class.return_value = mock_client
        
        sync = PeopleAlbumsSync(config_path)
        result = sync.sync_person_to_album(sync.config['mappings'][0])
        
        assert result is True
        # Должны добавить только первые 2 актива
        mock_client.add_assets_to_album.assert_called_once_with('album1', ['asset1', 'asset2'])
    
    @patch('main.ImmichClient')
    def test_sync_person_to_album_by_id(self, mock_client_class, tmp_path):
        """Тест синхронизации по ID человека"""
        config_path = self.create_test_config(tmp_path)
        # Обновляем конфиг для использования person_id
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        config['mappings'][0]['person_id'] = 'person123'
        config['mappings'][0]['person_name'] = None
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        
        mock_client = Mock()
        mock_client.get_person_by_id.return_value = {
            'id': 'person123',
            'name': 'Иван'
        }
        mock_client.find_album_by_name.return_value = {
            'id': 'album1',
            'albumName': 'Альбом Ивана'
        }
        mock_client.search_assets_by_person.return_value = ['asset1']
        mock_client.get_album_assets.return_value = []
        mock_client.add_assets_to_album.return_value = True
        mock_client_class.return_value = mock_client
        
        sync = PeopleAlbumsSync(config_path)
        result = sync.sync_person_to_album(sync.config['mappings'][0])
        
        assert result is True
        mock_client.get_person_by_id.assert_called_once_with('person123')
        mock_client.find_person_by_name.assert_not_called()
    
    @patch('main.ImmichClient')
    def test_run_with_multiple_mappings(self, mock_client_class, tmp_path):
        """Тест запуска с несколькими соответствиями"""
        config_path = self.create_test_config(tmp_path)
        # Добавляем еще одно соответствие
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        config['mappings'].append({
            'person_name': 'Мария',
            'person_id': None,
            'album_name': 'Альбом Марии',
            'album_id': None
        })
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        
        mock_client = Mock()
        mock_client.find_person_by_name.side_effect = [
            {'id': 'person1', 'name': 'Иван'},
            {'id': 'person2', 'name': 'Мария'}
        ]
        mock_client.find_album_by_name.side_effect = [
            {'id': 'album1', 'albumName': 'Альбом Ивана'},
            {'id': 'album2', 'albumName': 'Альбом Марии'}
        ]
        mock_client.search_assets_by_person.side_effect = [
            ['asset1', 'asset2'],
            ['asset3']
        ]
        mock_client.get_album_assets.return_value = []
        mock_client.add_assets_to_album.return_value = True
        mock_client_class.return_value = mock_client
        
        sync = PeopleAlbumsSync(config_path)
        sync.run()
        
        assert mock_client.add_assets_to_album.call_count == 2
        assert mock_client.find_person_by_name.call_count == 2
    
    @patch('main.ImmichClient')
    def test_run_with_empty_mappings(self, mock_client_class, tmp_path):
        """Тест запуска без соответствий"""
        config_path = self.create_test_config(tmp_path)
        # Удаляем соответствия
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        config['mappings'] = []
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True)
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        sync = PeopleAlbumsSync(config_path)
        sync.run()  # Не должно упасть
        
        mock_client.find_person_by_name.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

