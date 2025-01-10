import unittest
import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import tempfile
from unittest.mock import patch, MagicMock
from tensorflow.keras.models import Sequential
from models.ml_model import MLModel  

class TestMLModel(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.model = MLModel()
        self.model.initialize_stopwords()
        
   
        self.sample_data = pd.DataFrame({
            'title': ['Sample Title 1', 'Sample Title 2'],
            'text': ['This is fake news content', 'This is true news content'],
            'target': ['FAKE', 'TRUE']
        })
        
  
        self.sample_text = "This is a sample news article for testing purposes."

    def tearDown(self):
        """Clean up after each test method."""
        self.model = None

    def test_singleton_pattern(self):
        """Test if the singleton pattern is working correctly."""
        model1 = MLModel()
        model2 = MLModel()
        self.assertEqual(id(model1), id(model2))

    def test_initialize_stopwords(self):
        """Test if stopwords are initialized correctly."""
        self.assertIsNotNone(self.model.stop_words)
        self.assertIsInstance(self.model.stop_words, list)
        self.assertTrue(len(self.model.stop_words) > 0)

    def test_preprocess_text(self):
        """Test text preprocessing functionality."""
        test_text = "This is a TEST message with Numbers 123!"
        processed_text = self.model.preprocess_text(test_text)
    
        self.assertEqual(processed_text, processed_text.lower())
    
        self.assertFalse(any(char.isdigit() for char in processed_text))
        
        self.assertFalse(any(char in "!@#$%^&*()" for char in processed_text))

    def test_prepare_data(self):
        """Test data preparation functionality."""
        processed_data = self.model.prepare_data(self.sample_data)
        
        self.assertTrue('final_news' in processed_data.columns)
        self.assertTrue('target' in processed_data.columns)
        
        self.assertTrue(set(processed_data['target'].unique()).issubset({0, 1}))
        
        self.assertIsNotNone(self.model.total_words)
        self.assertGreater(self.model.total_words, 0)

    @patch('tensorflow.keras.models.Sequential')
    def test_build_model(self, mock_sequential):
        """Test model building functionality."""
        self.model.total_words = 1000  
        model = self.model.build_model()
        
        self.assertIsNotNone(model)
        
        mock_sequential.assert_called()

    @patch('tensorflow.keras.models.Sequential')
    def test_train_model(self, mock_sequential):
        """Test model training functionality."""

        X = ["This is test text 1", "This is test text 2"]
        y = np.array([0, 1])
        
        self.model.total_words = 1000
        self.model.build_model()
        
        history = self.model.train_model(X, y, epochs=1)
        
        self.assertIsNotNone(history)

    def test_predict(self):
        """Test prediction functionality."""
 
        self.model.model = MagicMock()
        self.model.tokenizer = MagicMock()
        self.model.model.predict.return_value = np.array([[0.8]])
        self.model.tokenizer.texts_to_sequences.return_value = [[1, 2, 3]]
        
        prediction = self.model.predict(self.sample_text)
        
        self.assertIn('prediction', prediction)
        self.assertIn('probability', prediction)
        self.assertIn('label', prediction)
        
        self.assertIsInstance(prediction['prediction'], int)
        self.assertIsInstance(prediction['probability'], float)
        self.assertIsInstance(prediction['label'], str)

    def test_save_and_load_model(self):
        """Test model saving and loading functionality."""
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as tmp:
            model_path = tmp.name
            
            self.model.total_words = 1000
            self.model.build_model()
            
            self.model.save_model(model_path)
            self.assertTrue(os.path.exists(model_path))
            
            self.model.load_model(model_path)
            self.assertIsNotNone(self.model.model)
            
            os.unlink(model_path)

    def test_invalid_input_handling(self):
        """Test handling of invalid inputs."""

        with self.assertRaises(ValueError):
            self.model.preprocess_text("")

        with self.assertRaises(ValueError):
            self.model.save_model("")
        
        self.model.model = None
        with self.assertRaises(ValueError):
            self.model.predict("test text")

    @patch('pandas.read_csv')
    def test_integration(self, mock_read_csv):
        """Test the entire pipeline integration."""

        mock_read_csv.return_value = self.sample_data
        
        self.model.initialize_stopwords()
        processed_data = self.model.prepare_data(self.sample_data)
        self.model.build_model()
        

        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            processed_data['final_news'],
            processed_data['target'],
            test_size=0.2,
            random_state=42
        )
        

        self.model.train_model(X_train, y_train, epochs=1)
        
        prediction = self.model.predict(X_test.iloc[0])
        
        self.assertIn('prediction', prediction)
        self.assertIn('probability', prediction)
        self.assertIn('label', prediction)

if __name__ == '__main__':
    unittest.main()