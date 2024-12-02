import tensorflow as tf
from abc import ABC
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.aop_wrapper import Aspect


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
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def load_model(self, model_path: str):
        """
        Loads the TensorFlow model from a given path.
        For testing, we will simulate model loading.
        """
        self.model = "mock_model"
          
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def preprocess(self, article_text: str):
        """
        Preprocesses raw article text for prediction.
        For testing, we will simulate preprocessing by returning the uppercase text.
        """
        return article_text.upper()
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def predict(self, processed_text):
        """
        Runs the prediction on preprocessed text.
        For testing, this will return a mock prediction result.
        """
      
        return {"raw_prediction": 0.8}  
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def get_prediction(self, article_text: str):
        """
        Handles full prediction pipeline: preprocesses and predicts.
        """
        processed_text = self.preprocess(article_text)
        return self.predict(processed_text)

def main():
   
    model = MLModel()
    model.load_model("dummy_path") 
    article_text = "Acesta este un text de test pentru modelul ML."
    prediction = model.get_prediction(article_text)
    print("Rezultatul predicției:", prediction)

if __name__ == "__main__":
    main()