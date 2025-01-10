import tensorflow as tf
import numpy as np
import pandas as pd
import nltk
import re
import gensim
from abc import ABC
import functools
import sys
import os
from typing import Callable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from nltk.corpus import stopwords
import re
from models.ml_model_aop import Aspect
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential, Model, load_model
from tensorflow.keras.layers import Embedding, LSTM, Dense, Conv1D, MaxPooling1D, Bidirectional
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from models.ml_model_aop import Aspect

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../model_prep')))

import mop
import os
import logging
import traceback
import time
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='ml_model_monitoring.log'
)
logger = logging.getLogger('MLModel_MOP')

def monitor(precondition: Callable, error_message: Callable) -> Callable:
    """
    A decorator that implements monitor-oriented programming for MLModel methods.
    
    Args:
        precondition (Callable): A function that checks if the input meets required conditions
        error_message (Callable): A function that returns an error message if precondition fails
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
    
            func_name = func.__name__
            
            try:
            
                logger.info(f"Entering {func_name}")
                
                if not precondition(self, *args):
                    msg = error_message(self, *args)
                    logger.error(f"Precondition failed for {func_name}: {msg}")
                    raise ValueError(msg)
                

                start_time = time.time()
                result = func(self, *args, **kwargs)
                execution_time = time.time() - start_time
                
                self._monitor_post_execution(func_name, result, execution_time)
                
                return result
                
            except Exception as e:
                logger.error(f"Error in {func_name}: {str(e)}\n{traceback.format_exc()}")
                raise
            
            finally:
                logger.info(f"Exiting {func_name}")
                
        return wrapper
    return decorator

def performance_monitor() -> Callable:
    """Decorator for monitoring method performance."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Log performance metrics
            logger.info(f"{func.__name__} execution time: {execution_time:.2f} seconds")
            
            return result
        return wrapper
    return decorator

def resource_monitor() -> Callable:
    """Decorator for monitoring resource usage."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import psutil
            
            # Capture initial resource usage
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            result = func(*args, **kwargs)
            
            # Capture final resource usage
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_used = final_memory - initial_memory
            
            # Log resource usage
            logger.info(f"{func.__name__} memory usage: {memory_used:.2f} MB")
            
            return result
        return wrapper
    return decorator

def model_state_monitor() -> Callable:
    """Decorator for monitoring model state changes."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            initial_state = {
                'has_model': hasattr(self, 'model') and self.model is not None,
                'has_tokenizer': hasattr(self, 'tokenizer') and self.tokenizer is not None,
                'total_words': getattr(self, 'total_words', None)
            }
            
            result = func(self, *args, **kwargs)
 
            final_state = {
                'has_model': hasattr(self, 'model') and self.model is not None,
                'has_tokenizer': hasattr(self, 'tokenizer') and self.tokenizer is not None,
                'total_words': getattr(self, 'total_words', None)
            }
            
            for key in initial_state:
                if initial_state[key] != final_state[key]:
                    logger.info(f"{func.__name__} changed {key}: {initial_state[key]} -> {final_state[key]}")
            
            return result
        return wrapper
    return decorator

def data_quality_monitor(min_samples: int = 100, min_features: int = 2) -> Callable:
    """Monitor for data quality checks."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            import pandas as pd
            
            if args and isinstance(args[0], pd.DataFrame):
                data = args[0]
                
                if len(data) < min_samples:
                    logger.warning(f"Data has fewer than {min_samples} samples")
                if len(data.columns) < min_features:
                    logger.warning(f"Data has fewer than {min_features} features")
                
                missing_values = data.isnull().sum()
                if missing_values.any():
                    logger.warning(f"Missing values detected:\n{missing_values[missing_values > 0]}")
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

def model_metrics_monitor() -> Callable:
    """Monitor for tracking model metrics during training."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            
            if hasattr(result, 'history'):
                metrics = result.history
                for metric, values in metrics.items():
                    final_value = values[-1]
                    logger.info(f"Final {metric}: {final_value:.4f}")
            
            return result
        return wrapper
    return decorator
import model_config
import mop 
=======

from models.aop_wrapper import Aspect


from models.aop_wrapper import Aspect


class MLModel:
    """
    Enhanced ML model class for fake news detection with Singleton Pattern.
    Incorporates text preprocessing, model training, and prediction capabilities.
    """
    
    _instance = None
    model = None
    tokenizer = None
    total_words = None
    stop_words = None
    
    def __new__(cls):
        """
        Singleton implementation to ensure only one instance of the model exists.
        """
        if cls._instance is None:
            cls._instance = super(MLModel, cls).__new__(cls)
            cls._initialize_nltk()
        return cls._instance
    
    @staticmethod
    def _initialize_nltk():
        """
        Initialize NLTK resources needed for text processing.
        """
        try:
            nltk.download('stopwords', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
        except Exception as e:
            print(f"Warning: NLTK resource initialization failed: {str(e)}")
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @data_quality_monitor(min_samples=100, min_features=2)
    def initialize_stopwords(self):
        """
        Initialize stopwords for text preprocessing.
        """
        self.stop_words = stopwords.words('english')
        self.stop_words.extend(['from', 'subject', 're', 'edu', 'use'])
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @mop.monitor(
        lambda self, text: isinstance(text, str) and len(text.strip()) > 0,
        lambda self, text: "Input text must be a non-empty string."
    )
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text by cleaning and tokenizing.
        """

        text = text.lower()
        #print("Textul a fost facut mic")
        text = ' '.join(word for word in text.split() if word not in self.stop_words)
        #print("Textul a fost curatat de stopwords")
        text = re.sub(r'[^a-z]', ' ', text)
        #print("Textul a fost curatat de caracterele speciale")
    
        return text
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @mop.monitor(
        lambda self, text: isinstance(text, str) and len(text.strip()) > 0,
        lambda self, text: "Input text must be a non-empty string."
    )
    @model_state_monitor()
    @performance_monitor()
    def tokenize_text(self, text: str):
        """
        Tokenize text into individual words.
        """
        tokens = [token for token in gensim.utils.simple_preprocess(text)
                 if token not in gensim.parsing.preprocessing.STOPWORDS 
                 and len(token) > 3 
                 and token not in self.stop_words]
        return tokens
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @mop.monitor(
        lambda self, data: isinstance(data, pd.DataFrame) and not data.empty,
        lambda self, data: "Input data must be a non-empty DataFrame."
    )
    @model_state_monitor()
    @performance_monitor()
    @data_quality_monitor(min_samples=100, min_features=2)
    def prepare_data(self, data: pd.DataFrame):
        """
        Prepare and preprocess the training data.
        """
        
        data['final_news'] = data['title'] + ' ' + data['text']
        data['final_news'] = data['final_news'].apply(self.preprocess_text)
        print(data.head())
        data['final_news'] = data['final_news'].apply(self.tokenize_text)
        print(data.head())
        data['target'] = data['target'].map({'FAKE': 1, 'TRUE': 0})
  
        words = [word for text in data.final_news for word in text.split()]
        self.total_words = len(set(words))
        print(f"Total unique words in the dataset: {self.total_words}")
        
        return data
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @model_state_monitor()
    @performance_monitor()
    @resource_monitor()
    def build_model(self, max_sequence_length: int = 40):
        """
        Build and compile the LSTM model architecture.
        """
        self.model = Sequential([
            Embedding(self.total_words, output_dim=128),
            Bidirectional(LSTM(128)),
            Dense(128, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        
        self.model.build(input_shape=(None, max_sequence_length))
        self.model.compile(optimizer='adam', 
                         loss='binary_crossentropy', 
                         metrics=['acc'])
        
        return self.model
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @mop.monitor(
        lambda self, X, y: len(X) == len(y),
        lambda self, X, y: "Features and labels must have the same length."
    )
    @model_metrics_monitor()
    @model_state_monitor()
    @performance_monitor()
    def train_model(self, X, y, max_sequence_length: int = 40, 
                   batch_size: int = 64, epochs: int = 5):
        """
        Train the model with the provided data.
        """

        if self.tokenizer is None:
            self.tokenizer = Tokenizer(num_words=self.total_words)
            self.tokenizer.fit_on_texts(X)

        sequences = self.tokenizer.texts_to_sequences(X)
        padded_sequences = pad_sequences(sequences, maxlen=max_sequence_length, 
                                      padding='post', truncating='post')
        
        y = np.asarray(y)
        
        history = self.model.fit(padded_sequences, y, 
                               batch_size=batch_size,
                               validation_split=0.1, 
                               epochs=epochs)
        
        return history
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @mop.monitor(
        lambda self, text: isinstance(text, str) and len(text.strip()) > 0,
        lambda self, text: "Prediction text must be a non-empty string."
    )
    @model_state_monitor()
    @performance_monitor()
    def predict(self, text: str, max_sequence_length: int = 40, threshold: float = 0.95):
        """
        Make predictions on new text.
        """
        if self.model is None:
            raise ValueError("Model has not been loaded or trained.")
            
        processed_text = self.preprocess_text(text)
  
        sequence = self.tokenizer.texts_to_sequences([processed_text])
        padded_sequence = pad_sequences(sequence, maxlen=max_sequence_length, 
                                     truncating='post')
        
        pred_probability = self.model.predict(padded_sequence)[0][0]
        prediction = 1 if pred_probability > threshold else 0
        
        return {
            "prediction": prediction,
            "probability": float(pred_probability),
            "label": "FAKE" if prediction == 1 else "TRUE"
        }
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @mop.monitor(
        lambda self, model_path: isinstance(model_path, str) and model_path.endswith('.h5'),
        lambda self, model_path: "Model path must be a string ending with .h5"
    )
    @model_state_monitor()
    @performance_monitor()
    def save_model(self, model_path: str):
        """
        Save the trained model to disk.
        """
        if self.model is None:
            raise ValueError("No model to save. Train or load a model first.")
        self.model.save(model_path)
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @mop.monitor(
        lambda self, model_path: isinstance(model_path, str) and os.path.exists(model_path),
        lambda self, model_path: f"Model file {model_path} does not exist."
    )
    @model_state_monitor()
    @performance_monitor()
    def load_model(self, model_path: str):
        """
        Load a trained model from disk.
        """
        self.model = load_model(model_path)


def main():

    model_ml = MLModel()
    model_ml.initialize_stopwords()
    
    data = pd.read_csv('C:/Users/bodes/Documents/GitHub/News-source-verifier/NSV-app/models/news.csv')
    processed_data = model_ml.prepare_data(data)
    #print(processed_data.head())
    X_train, X_test, y_train, y_test = train_test_split(
        processed_data['final_news'], 
        processed_data['target'], 
        test_size=0.2
    )
    
    model_ml.build_model()
    model_ml.train_model(X_train, y_train)
    
    model_ml.save_model('fake_news_detector.h5')
    
    predictions = []
    for text in X_test:
        pred = model_ml.predict(text)
        predictions.append(pred['prediction'])
    
    print("\nModel Performance Metrics:")
    print(classification_report(y_test, predictions))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions))
    print(f"\nAccuracy: {accuracy_score(y_test, predictions):.2f}")

if __name__ == "__main__":
    main()