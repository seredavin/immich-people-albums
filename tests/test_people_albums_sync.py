"""
Тесты для PeopleAlbumsSync
"""

import pytest
import yaml
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from main import PeopleAlbumsSync, ImmichClient


class TestPeopleAlbumsSync:
    """Тесты для класса PeopleAlbumsSync"""
    
    def create_test_config(self, content):
        """Создать временный конфиг файл"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(content, f, allow_unicode=True)
            return f.name
    
    def test_init_loads_config(self):
        """Тест загрузки конфигурации"""
        config = {
            'immich': {
                'url': 'http://test.com',
                'api_key': 'test-key'
            },
            'mappings': [],
            'options': {'log_level': 'INFO'}
        }
        
        config_path = self.create_test_config(config)
        
        try:
            with patch('main.ImmichClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                sync = PeopleAlbumsSync(config_path)
                
                assert sync.config == config
                assert sync.client == mock_client
        finally:
            os.unlink(config_path)
    
    def test_load_config_error(self):
        """Тест обработки ошибки загрузки конфига"""
        with pytest.raises(Exception):
            PeopleAlbumsSync("nonexistent.yaml")
    
    def test_sync_person_to_album_success(self):
        """Тест успешной синхронизации"""
        config = {
            'immich': {
                'url': 'http://test.com',
                'api_key': 'test-key'
            },
            'mappings': [],
            'options': {'skip_existing': True}
        }
        
        config_path = self.create_test_config(config)
        
        try:
            with patch('main.ImmichClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                # Настройка моков
                mock_client.find_person_by_name.return_value = {
                    'id': 'person1',
                    'name': 'Ivan'
                }
                mock_client.find_album_by_name.return_value = {
                    'id': 'album1',
                    'albumName': 'Album Ivan'
                }
                mock_client.search_assets_by_person.return_value = ['asset1', 'asset2']
                mock_client.get_album_assets.return_value = []
                mock_client.add_assets_to_album.return_value = True
                
                sync = PeopleAlbumsSync(config_path)
                
                mapping = {
                    'person_name': 'Ivan',
                    'album_name': 'Album Ivan'
                }
                
                result = sync.sync_person_to_album(mapping)
                
                assert result is True
                mock_client.add_assets_to_album.assert_called_once_with('album1', ['asset1', 'asset2'])
        finally:
            os.unlink(config_path)
    
    def test_sync_person_to_album_person_not_found(self):
        """Тест обработки случая, когда человек не найден"""
        config = {
            'immich': {
                'url': 'http://test.com',
                'api_key': 'test-key'
            },
            'mappings': [],
            'options': {}
        }
        
        config_path = self.create_test_config(config)
        
        try:
            with patch('main.ImmichClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                mock_client.find_person_by_name.return_value = None
                
                sync = PeopleAlbumsSync(config_path)
                
                mapping = {
                    'person_name': 'Unknown',
                    'album_name': 'Album'
                }
                
                result = sync.sync_person_to_album(mapping)
                
                assert result is False
        finally:
            os.unlink(config_path)
    
    def test_sync_person_to_album_create_album(self):
        """Тест создания альбома, если он не существует"""
        config = {
            'immich': {
                'url': 'http://test.com',
                'api_key': 'test-key'
            },
            'mappings': [],
            'options': {}
        }
        
        config_path = self.create_test_config(config)
        
        try:
            with patch('main.ImmichClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                mock_client.find_person_by_name.return_value = {
                    'id': 'person1',
                    'name': 'Ivan'
                }
                mock_client.find_album_by_name.return_value = None
                mock_client.create_album.return_value = {
                    'id': 'new_album1',
                    'albumName': 'New Album'
                }
                mock_client.search_assets_by_person.return_value = ['asset1']
                mock_client.get_album_assets.return_value = []
                mock_client.add_assets_to_album.return_value = True
                
                sync = PeopleAlbumsSync(config_path)
                
                mapping = {
                    'person_name': 'Ivan',
                    'album_name': 'New Album'
                }
                
                result = sync.sync_person_to_album(mapping)
                
                assert result is True
                mock_client.create_album.assert_called_once_with('New Album')
        finally:
            os.unlink(config_path)
    
    def test_sync_person_to_album_skip_existing(self):
        """Тест пропуска уже существующих активов"""
        config = {
            'immich': {
                'url': 'http://test.com',
                'api_key': 'test-key'
            },
            'mappings': [],
            'options': {'skip_existing': True}
        }
        
        config_path = self.create_test_config(config)
        
        try:
            with patch('main.ImmichClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                mock_client.find_person_by_name.return_value = {
                    'id': 'person1',
                    'name': 'Ivan'
                }
                mock_client.find_album_by_name.return_value = {
                    'id': 'album1',
                    'albumName': 'Album'
                }
                mock_client.search_assets_by_person.return_value = ['asset1', 'asset2', 'asset3']
                mock_client.get_album_assets.return_value = ['asset2']  # asset2 уже в альбоме
                mock_client.add_assets_to_album.return_value = True
                
                sync = PeopleAlbumsSync(config_path)
                
                mapping = {
                    'person_name': 'Ivan',
                    'album_name': 'Album'
                }
                
                result = sync.sync_person_to_album(mapping)
                
                assert result is True
                # Должны быть добавлены только asset1 и asset3
                mock_client.add_assets_to_album.assert_called_once_with('album1', ['asset1', 'asset3'])
        finally:
            os.unlink(config_path)
    
    def test_sync_person_to_album_no_new_assets(self):
        """Тест случая, когда все активы уже в альбоме"""
        config = {
            'immich': {
                'url': 'http://test.com',
                'api_key': 'test-key'
            },
            'mappings': [],
            'options': {'skip_existing': True}
        }
        
        config_path = self.create_test_config(config)
        
        try:
            with patch('main.ImmichClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                mock_client.find_person_by_name.return_value = {
                    'id': 'person1',
                    'name': 'Ivan'
                }
                mock_client.find_album_by_name.return_value = {
                    'id': 'album1',
                    'albumName': 'Album'
                }
                mock_client.search_assets_by_person.return_value = ['asset1', 'asset2']
                mock_client.get_album_assets.return_value = ['asset1', 'asset2']  # Все уже есть
                
                sync = PeopleAlbumsSync(config_path)
                
                mapping = {
                    'person_name': 'Ivan',
                    'album_name': 'Album'
                }
                
                result = sync.sync_person_to_album(mapping)
                
                assert result is True
                # Не должно быть вызова добавления
                mock_client.add_assets_to_album.assert_not_called()
        finally:
            os.unlink(config_path)
    
    def test_sync_person_to_album_max_assets_limit(self):
        """Тест ограничения по количеству активов"""
        config = {
            'immich': {
                'url': 'http://test.com',
                'api_key': 'test-key'
            },
            'mappings': [],
            'options': {'max_assets_per_run': 2}
        }
        
        config_path = self.create_test_config(config)
        
        try:
            with patch('main.ImmichClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                mock_client.find_person_by_name.return_value = {
                    'id': 'person1',
                    'name': 'Ivan'
                }
                mock_client.find_album_by_name.return_value = {
                    'id': 'album1',
                    'albumName': 'Album'
                }
                mock_client.search_assets_by_person.return_value = ['asset1', 'asset2', 'asset3', 'asset4']
                mock_client.get_album_assets.return_value = []
                mock_client.add_assets_to_album.return_value = True
                
                sync = PeopleAlbumsSync(config_path)
                
                mapping = {
                    'person_name': 'Ivan',
                    'album_name': 'Album'
                }
                
                result = sync.sync_person_to_album(mapping)
                
                assert result is True
                # Должно быть добавлено только 2 актива
                mock_client.add_assets_to_album.assert_called_once_with('album1', ['asset1', 'asset2'])
        finally:
            os.unlink(config_path)
    
    def test_sync_person_to_album_by_id(self):
        """Тест синхронизации по ID человека и альбома"""
        config = {
            'immich': {
                'url': 'http://test.com',
                'api_key': 'test-key'
            },
            'mappings': [],
            'options': {}
        }
        
        config_path = self.create_test_config(config)
        
        try:
            with patch('main.ImmichClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                mock_client.get_person_by_id.return_value = {
                    'id': 'person1',
                    'name': 'Ivan'
                }
                mock_client.get_all_albums.return_value = [
                    {'id': 'album1', 'albumName': 'Album'}
                ]
                mock_client.search_assets_by_person.return_value = ['asset1']
                mock_client.get_album_assets.return_value = []
                mock_client.add_assets_to_album.return_value = True
                
                sync = PeopleAlbumsSync(config_path)
                
                mapping = {
                    'person_id': 'person1',
                    'album_id': 'album1',
                    'person_name': 'Ivan',
                    'album_name': 'Album'
                }
                
                result = sync.sync_person_to_album(mapping)
                
                assert result is True
                mock_client.get_person_by_id.assert_called_once_with('person1')
        finally:
            os.unlink(config_path)
    
    def test_run_no_mappings(self):
        """Тест запуска без соответствий"""
        config = {
            'immich': {
                'url': 'http://test.com',
                'api_key': 'test-key'
            },
            'mappings': [],
            'options': {}
        }
        
        config_path = self.create_test_config(config)
        
        try:
            with patch('main.ImmichClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                sync = PeopleAlbumsSync(config_path)
                sync.run()  # Не должно быть ошибок
                
                assert True  # Если дошли сюда, все ок
        finally:
            os.unlink(config_path)
    
    def test_run_with_mappings(self):
        """Тест запуска с несколькими соответствиями"""
        config = {
            'immich': {
                'url': 'http://test.com',
                'api_key': 'test-key'
            },
            'mappings': [
                {
                    'person_name': 'Ivan',
                    'album_name': 'Album Ivan'
                },
                {
                    'person_name': 'Maria',
                    'album_name': 'Album Maria'
                }
            ],
            'options': {}
        }
        
        config_path = self.create_test_config(config)
        
        try:
            with patch('main.ImmichClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                # Настройка для первого человека
                def find_person_side_effect(name):
                    if name == 'Ivan':
                        return {'id': 'person1', 'name': 'Ivan'}
                    elif name == 'Maria':
                        return {'id': 'person2', 'name': 'Maria'}
                    return None
                
                mock_client.find_person_by_name.side_effect = find_person_side_effect
                mock_client.find_album_by_name.return_value = {'id': 'album1', 'albumName': 'Album'}
                mock_client.search_assets_by_person.return_value = ['asset1']
                mock_client.get_album_assets.return_value = []
                mock_client.add_assets_to_album.return_value = True
                
                sync = PeopleAlbumsSync(config_path)
                sync.run()
                
                # Должно быть вызвано дважды (по одному для каждого соответствия)
                assert mock_client.add_assets_to_album.call_count == 2
        finally:
            os.unlink(config_path)

