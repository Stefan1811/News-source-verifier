import tensorflow as tf
import numpy as np
from abc import ABC
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
from models.ml_model_aop import Aspect
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Embedding, LSTM, Dense, Conv1D, MaxPooling1D, Bidirectional, GlobalMaxPool1D, Input, Dropout
from tensorflow.keras.models import load_model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../model_prep')))
import model_config
import mop 
=======

from models.aop_wrapper import Aspect


class MLModel:
    """
    Base class for a TensorFlow ML model with Singleton Pattern.
    Ensures only one model instance is active.
    """
    
    _instance = None 
    model = None      
    tokenizer = None  
    embedding_matrix = None  
    word_to_vector = None 
    
    def __new__(cls):
        """
        Singleton implementation to ensure only one instance of the model exists.
        """
        if cls._instance is None:
            cls._instance = super(MLModel, cls).__new__(cls)
        return cls._instance
    
    def load_word_vectors(self, embedding_file: str, max_vocab_size: int, embedding_dim: int):
        """
        Loads word vectors and prepares embedding matrix.
        """
        self.word_to_vector = {}
        with open(embedding_file, encoding='utf-8') as f:
            for line in f:
                values = line.split()
                word = values[0]
                vec = np.asarray(values[1:], dtype='float32')
                self.word_to_vector[word] = vec
        
        print(f'Found {len(self.word_to_vector)} word vectors.')
        self.tokenizer = Tokenizer(num_words=max_vocab_size)
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @mop.monitor(
        lambda model_path: isinstance(model_path, str) and os.path.exists(model_path),
        lambda model_path: f"Model file {model_path} does not exist or invalid file path."
    )
    def load_model(self, model_path: str):
        """
        Loads the TensorFlow model from a given path.
        """
        self.model = load_model(model_path)
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @mop.monitor(
        lambda article_text: isinstance(article_text, str) and len(article_text.strip()) > 0,
        lambda article_text: "Article text must be a non-empty string."
    )
    def preprocess(self, article_text: str):
        """
        Preprocesses raw article text for prediction.
        """
        article_text = article_text.lower()
        article_text = re.sub(r'[^a-z\s]', '', article_text)
        return article_text
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @mop.monitor(
        lambda word_to_index, max_vocab_size, embedding_dim: isinstance(word_to_index, dict) and isinstance(max_vocab_size, int) and isinstance(embedding_dim, int),
        lambda word_to_index, max_vocab_size, embedding_dim: f"Invalid parameters: word_to_index is {type(word_to_index)}, max_vocab_size is {type(max_vocab_size)}, embedding_dim is {type(embedding_dim)}."
    )
    def get_embedding_matrix(self, word_to_index: dict, max_vocab_size: int, embedding_dim: int):
        """
        Generates the embedding matrix from the word vectors.
        """
        embedding_matrix = np.zeros((max_vocab_size, embedding_dim))
        for word, i in word_to_index.items():
            if i < max_vocab_size:
                embedding_vector = self.word_to_vector.get(word)
                if embedding_vector is not None:
                    embedding_matrix[i] = embedding_vector
        return embedding_matrix
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    @mop.monitor(
        lambda article_text: len(article_text.strip()) > 0,
        lambda article_text: "Input text is empty."
    )
    def predict(self, article_text: str, max_sequence_length: int):
        """
        Runs the prediction on preprocessed text.
        """
        # Validăm dacă modelul este încărcat corect
        if self.model is None:
            raise ValueError("Model has not been loaded. Please load the model before prediction.")
        
        # Validăm dacă vectorii de cuvinte sunt încărcați
        if self.word_to_vector is None:
            raise ValueError("Word vectors have not been loaded. Please load word vectors before prediction.")

        # Preprocesăm textul de intrare
        article_text = self.preprocess(article_text)

        sequences = self.tokenizer.texts_to_sequences([article_text])
        padded_sequences = pad_sequences(sequences, maxlen=max_sequence_length)
        
        prediction = self.model.predict(padded_sequences)
        return {"raw_prediction": prediction[0][0]}  
    
    @Aspect.log_execution
    @Aspect.measure_time
    @Aspect.handle_exceptions
    def get_prediction(self, article_text: str, max_sequence_length: int):
        """
        Handles full prediction pipeline: preprocesses and predicts.
        """
        return self.predict(article_text, max_sequence_length)


def main():
    model = MLModel()
    
 
    model.load_word_vectors(embedding_file=model_config.EMBEDDING_FILE, max_vocab_size=model_config.MAX_VOCAB_SIZE, embedding_dim=model_config.EMBEDDING_DIM)

    model.load_model("fake_news_model.h5")

    article_text = "Acesta este un text de test pentru modelul ML."
    prediction = model.get_prediction(article_text, max_sequence_length=500)
    print("Rezultatul predicției:", prediction)

    

if __name__ == "__main__":
    main()