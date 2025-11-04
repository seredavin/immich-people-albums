"""
Тесты для ImmichClient
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from main import ImmichClient


class TestImmichClient:
    """Тесты для класса ImmichClient"""
    
    def test_init_with_api_key(self):
        """Тест инициализации с API ключом"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            
            assert client.base_url == "http://test.com"
            assert client.api_url == "http://test.com/api"
            assert client.api_key == "test-key"
            mock_session_instance.headers.update.assert_called_once_with({'x-api-key': 'test-key'})
    
    def test_init_with_email_password(self):
        """Тест инициализации с email/password"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.json.return_value = {'accessToken': 'test-token'}
            mock_response.raise_for_status = Mock()
            mock_session_instance.post.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", email="test@test.com", password="pass")
            
            assert client.email == "test@test.com"
            assert client.password == "pass"
            mock_session_instance.post.assert_called_once()
            assert 'Authorization' in mock_session_instance.headers
    
    def test_init_without_credentials(self):
        """Тест инициализации без учетных данных"""
        with patch('main.requests.Session'):
            with pytest.raises(ValueError, match="Необходимо указать"):
                ImmichClient("http://test.com")
    
    def test_get_all_people(self):
        """Тест получения списка людей"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.json.return_value = {'people': [{'id': '1', 'name': 'Test'}]}
            mock_response.raise_for_status = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            people = client.get_all_people()
            
            assert len(people) == 1
            assert people[0]['name'] == 'Test'
    
    def test_get_all_people_error(self):
        """Тест обработки ошибки при получении людей"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_session_instance.get.side_effect = requests.RequestException("Error")
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            people = client.get_all_people()
            
            assert people == []
    
    def test_find_person_by_name(self):
        """Тест поиска человека по имени"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.json.return_value = {
                'people': [
                    {'id': '1', 'name': 'Ivan'},
                    {'id': '2', 'name': 'Maria'}
                ]
            }
            mock_response.raise_for_status = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            person = client.find_person_by_name("Maria")
            
            assert person is not None
            assert person['id'] == '2'
            assert person['name'] == 'Maria'
    
    def test_find_person_by_name_not_found(self):
        """Тест поиска несуществующего человека"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.json.return_value = {'people': []}
            mock_response.raise_for_status = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            person = client.find_person_by_name("Unknown")
            
            assert person is None
    
    def test_get_person_by_id(self):
        """Тест получения человека по ID"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.json.return_value = {'id': '123', 'name': 'Test Person'}
            mock_response.raise_for_status = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            person = client.get_person_by_id("123")
            
            assert person['id'] == '123'
            assert person['name'] == 'Test Person'
    
    def test_search_assets_by_person(self):
        """Тест поиска активов по человеку"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.json.return_value = {
                'assets': {
                    'items': [
                        {'id': 'asset1'},
                        {'id': 'asset2'}
                    ],
                    'nextPage': None
                }
            }
            mock_response.raise_for_status = Mock()
            mock_session_instance.post.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            assets = client.search_assets_by_person("person123")
            
            assert len(assets) == 2
            assert 'asset1' in assets
            assert 'asset2' in assets
    
    def test_search_assets_by_person_pagination(self):
        """Тест пагинации при поиске активов"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            
            # Первая страница
            mock_response1 = Mock()
            mock_response1.json.return_value = {
                'assets': {
                    'items': [{'id': 'asset1'}],
                    'nextPage': 'page2'
                }
            }
            mock_response1.raise_for_status = Mock()
            
            # Вторая страница
            mock_response2 = Mock()
            mock_response2.json.return_value = {
                'assets': {
                    'items': [{'id': 'asset2'}],
                    'nextPage': None
                }
            }
            mock_response2.raise_for_status = Mock()
            
            mock_session_instance.post.side_effect = [mock_response1, mock_response2]
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            assets = client.search_assets_by_person("person123")
            
            assert len(assets) == 2
            assert mock_session_instance.post.call_count == 2
    
    def test_get_all_albums(self):
        """Тест получения списка альбомов"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.json.return_value = [
                {'id': '1', 'albumName': 'Album 1'},
                {'id': '2', 'albumName': 'Album 2'}
            ]
            mock_response.raise_for_status = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            albums = client.get_all_albums()
            
            assert len(albums) == 2
    
    def test_find_album_by_name(self):
        """Тест поиска альбома по имени"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.json.return_value = [
                {'id': '1', 'albumName': 'Album 1'},
                {'id': '2', 'albumName': 'Album 2'}
            ]
            mock_response.raise_for_status = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            album = client.find_album_by_name("Album 2")
            
            assert album is not None
            assert album['id'] == '2'
    
    def test_create_album(self):
        """Тест создания альбома"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.json.return_value = {'id': 'new123', 'albumName': 'New Album'}
            mock_response.raise_for_status = Mock()
            mock_session_instance.post.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            album = client.create_album("New Album")
            
            assert album is not None
            assert album['id'] == 'new123'
            mock_session_instance.post.assert_called_once()
    
    def test_get_album_assets(self):
        """Тест получения активов альбома"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.json.return_value = {
                'id': 'album1',
                'assets': [
                    {'id': 'asset1'},
                    {'id': 'asset2'}
                ]
            }
            mock_response.raise_for_status = Mock()
            mock_session_instance.get.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            assets = client.get_album_assets("album1")
            
            assert len(assets) == 2
            assert 'asset1' in assets
    
    def test_add_assets_to_album(self):
        """Тест добавления активов в альбом"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_session_instance.put.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            result = client.add_assets_to_album("album1", ["asset1", "asset2"])
            
            assert result is True
            mock_session_instance.put.assert_called_once()
    
    def test_add_assets_to_album_empty(self):
        """Тест добавления пустого списка активов"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            result = client.add_assets_to_album("album1", [])
            
            assert result is True
            mock_session_instance.put.assert_not_called()
    
    def test_add_assets_to_album_batch(self):
        """Тест добавления большого количества активов (батчи)"""
        with patch('main.requests.Session') as mock_session:
            mock_session_instance = Mock()
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_session_instance.put.return_value = mock_response
            mock_session_instance.headers = {}
            mock_session.return_value = mock_session_instance
            
            client = ImmichClient("http://test.com", api_key="test-key")
            # 250 активов должно разбиться на 3 батча по 100
            assets = [f"asset{i}" for i in range(250)]
            result = client.add_assets_to_album("album1", assets)
            
            assert result is True
            assert mock_session_instance.put.call_count == 3

