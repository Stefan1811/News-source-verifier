import unittest
from unittest.mock import MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.ml_model import MLModel
class TestMLModel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Prepare MLModel for testing by creating a mocked subclass on-the-fly.
        """
        cls.mock_mlmodel = MLModel.__new__(MLModel)

        cls.mock_mlmodel.load_model = MagicMock(name="load_model")
        cls.mock_mlmodel.preprocess = MagicMock(name="preprocess")
        cls.mock_mlmodel.predict = MagicMock(name="predict")

    def test_singleton_behavior(self):
        """
        Test that MLModel enforces singleton behavior.
        """
        instance1 = MLModel()
        instance2 = MLModel()
        self.assertIs(instance1, instance2, "MLModel should only allow one instance.")

    def test_load_model(self):
        """
        Test that load_model method can be called.
        """
        self.mock_mlmodel.load_model("dummy_path")
        self.mock_mlmodel.load_model.assert_called_once_with("dummy_path")

    def test_preprocess(self):
        """
        Test that preprocess method can be called and processes text correctly.
        """
        self.mock_mlmodel.preprocess.return_value = "processed_text"
        self.mock_mlmodel.get_prediction("test_article")
        self.mock_mlmodel.preprocess.assert_called_once_with("test_article")

    def test_predict(self):
        """
        Test that predict method can be called and returns expected output.
        """
        self.mock_mlmodel.predict.return_value = "prediction_result"
        self.mock_mlmodel.get_prediction("test_article")
        self.mock_mlmodel.predict.assert_called_once_with("processed_text")
        
    def test_get_prediction(self):
        """
        Test that get_prediction method runs the full pipeline of preprocess and predict.
        """
        self.mock_mlmodel.preprocess.return_value = "mocked_processed_text"
        self.mock_mlmodel.predict.return_value = "mocked_prediction"
        
        result = self.mock_mlmodel.get_prediction("some_article")
        
        self.mock_mlmodel.preprocess.assert_called_once_with("some_article")
        self.mock_mlmodel.predict.assert_called_once_with("mocked_processed_text")
        self.assertEqual(result, "mocked_prediction", "get_prediction should return the final prediction result")

if __name__ == '__main__':
    unittest.main()
