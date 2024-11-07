import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.ml_model import MLModel

class TestMLModel(unittest.TestCase):

    def test_singleton_instance(self):
        instance1 = MLModel()
        instance2 = MLModel()
        self.assertIs(instance1, instance2, "MLModel ar trebui să fie un Singleton (aceeași instanță).")

    def test_load_model(self):
        model = MLModel()
        model.load_model("dummy_path")
        self.assertIsNotNone(model.model, "Modelul ar trebui să fie încărcat și să nu fie None.")

    def test_preprocess(self):
        model = MLModel()
        article_text = "Test text pentru articol."
        processed_text = model.preprocess(article_text)
        self.assertIsNotNone(processed_text, "Textul procesat nu ar trebui să fie None.")
        self.assertIsInstance(processed_text, str, "Textul procesat ar trebui să fie de tip string.")

    def test_predict(self):
        model = MLModel()
        processed_text = "TEXT PROCESAT"
        prediction = model.predict(processed_text)
        self.assertIsInstance(prediction, dict, "Predicția ar trebui să fie un dicționar.")
        

    def test_get_prediction(self):
        model = MLModel()
        article_text = "Exemplu de text al articolului."
        prediction = model.get_prediction(article_text)
        
        self.assertIsInstance(prediction, dict, "Predicția finală ar trebui să fie un dicționar.")
       

if __name__ == '__main__':
    unittest.main()
