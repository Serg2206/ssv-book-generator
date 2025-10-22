
"""
Модульные тесты для ai_content_generator
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from modules import ai_content_generator


class TestLoadConfig:
    """Тесты для функции load_config"""
    
    def test_load_valid_config(self, config_file):
        """Тест загрузки валидной конфигурации"""
        config = ai_content_generator.load_config(config_file)
        
        assert config is not None
        assert 'project' in config
        assert 'book' in config
        assert config['project']['name'] == 'SSVproff Book Generator Test'
    
    def test_load_nonexistent_config(self):
        """Тест загрузки несуществующего файла"""
        with pytest.raises(FileNotFoundError):
            ai_content_generator.load_config('nonexistent.yaml')


class TestExtractKeyThemes:
    """Тесты для функции _extract_key_themes"""
    
    def test_extract_themes_from_text(self, sample_transcript):
        """Тест извлечения ключевых тем"""
        themes = ai_content_generator._extract_key_themes(sample_transcript)
        
        assert isinstance(themes, list)
        assert len(themes) > 0
        assert all(isinstance(theme, str) for theme in themes)


class TestGenerateContentFromTranscript:
    """Тесты для основной функции генерации контента"""
    
    @patch('modules.ai_content_generator._call_ai_model')
    def test_generate_content_success(self, mock_ai_call, config_file, sample_transcript):
        """Тест успешной генерации контента"""
        # Моки для разных вызовов ИИ
        mock_ai_call.side_effect = [
            'Test Book Title',  # title
            'Test book description',  # description
            'Глава 1: Intro\nГлава 2: Main\nГлава 3: Conclusion',  # outline
            'Chapter 1 content here...',  # chapter 1
            'Chapter 2 content here...',  # chapter 2
            'Chapter 3 content here...',  # chapter 3
        ]
        
        result = ai_content_generator.generate_content_from_transcript(
            sample_transcript,
            config_file
        )
        
        assert result is not None
        assert 'title' in result
        assert 'description' in result
        assert 'chapters' in result
        assert len(result['chapters']) == 3
    
    def test_generate_content_short_transcript(self, config_file):
        """Тест с короткой транскрипцией"""
        with pytest.raises(ValueError, match="слишком короткая"):
            ai_content_generator.generate_content_from_transcript(
                "Short text",
                config_file
            )
    
    @patch('modules.ai_content_generator._call_ai_model')
    def test_generate_content_ai_error(self, mock_ai_call, config_file, sample_transcript):
        """Тест обработки ошибок ИИ API"""
        mock_ai_call.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            ai_content_generator.generate_content_from_transcript(
                sample_transcript,
                config_file
            )
