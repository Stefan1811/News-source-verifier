import tensorflow as tf
from abc import ABC

class MLModel(ABC):
    """
    Base class for a TensorFlow ML model with Singleton Pattern.
    Ensures only one model instance is active.
    """
    
    _instance = None  # Singleton instance
    model = None      # Placeholder for TensorFlow model

    def __new__(cls):
        """
        Singleton implementation to ensure only one instance of the model exists.
        """
        if cls._instance is None:
            cls._instance = super(MLModel, cls).__new__(cls)
        return cls._instance

    def load_model(self, model_path: str):
        """
        Loads the TensorFlow model from a given path.
        """
        pass


    def preprocess(self, article_text: str):
        """
        Preprocesses raw article text for prediction.
        """
        pass


    def predict(self, processed_text):
        """
        Runs the prediction on preprocessed text.
        """
        pass

    def get_prediction(self, article_text: str):
        """
        Handles full prediction pipeline: preprocesses and predicts.
        """
        processed_text = self.preprocess(article_text)
        return self.predict(processed_text)
