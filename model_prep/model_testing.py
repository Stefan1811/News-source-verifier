from tensorflow.keras.models import load_model
import pandas as pd
import numpy as np
import sys
import itertools
import seaborn as sns
import nltk, re, string
import os 
from string import punctuation
from nltk.corpus import stopwords
from sklearn import metrics
import matplotlib.pyplot as plt
from wordcloud import WordCloud,STOPWORDS
from sklearn.metrics import classification_report,confusion_matrix,accuracy_score,roc_auc_score
from sklearn.model_selection import train_test_split
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Embedding, LSTM, Dense, Conv1D, MaxPooling1D, Bidirectional, GlobalMaxPool1D, Input, Dropout
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
import model_config
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import pickle


loaded_model = pickle.load(open("model_prep/model.pkl", 'rb'))
vector = pickle.load(open("model_prep/vector.pkl", 'rb'))


def fake_news_det(news):
    lemmatizer = WordNetLemmatizer()
    stpwrds = set(stopwords.words('english'))
    corpus = []
    review = news
    review = re.sub(r'[^a-zA-Z\s]', '', review)
    review = review.lower()
    review = nltk.word_tokenize(review)
    corpus = []
    for y in review :
        if y not in stpwrds :
            corpus.append(lemmatizer.lemmatize(y))
    input_data = [' '.join(corpus)]
    vectorized_input_data = vector.transform(input_data)
    prediction = loaded_model.predict(vectorized_input_data)
     
    return prediction

def predict_news(text):
    
    prediction = fake_news_det(text)
    if prediction == 1:
        return 0
    else:
        return 1


fake_news = "Washington, D.C. — Vice President Kamala Harris continued to get the worst of the exchanges as a heated argument with a talking cactus toy entered its third hour this afternoon. The cactus seemed to have an immediate retort for everything the Vice President said, confounding Harris' intellect as she steadily lost control of the dispute. So, you think there's great significance to the passage of time, huh cactus? asked the Vice President. So, you think there's great significance to the passage of time, huh cactus? replied the cactus. Why are you calling me a cactus? I'm the Vice President! cried Harris. Why are you calling me a cactus? I'm the Vice President! retorted the cactus. But you are a cactus! said the cactus, still calm and collected as ever. The debate continued to rage on, with the cactus firmly remaining in control as the hours rolled by. Aides tried to intervene, but Harris remained determined as ever to best the succulent. At publishing time, Harris and the cactus had descended into a lengthy loop of shouting I'm the real Vice President! at each other. Gen Z keeps pulling up to new jobs, no cap. Here are their top qualifications."
real_news = "Emmanuel Macron has praised the workers who restored Paris's Notre-Dame cathedral, calling their efforts impossible and a national remedy to the wound caused by the 2019 fire that devastated the Gothic landmark. After five and a half years of intensive restoration, the cathedral has been rebuilt and renovated, offering a stunning new look while preserving its historical charm. The €700 million restoration involved over 2,000 craftsmen and women, from masons to sculptors, and the project showcased French craftsmanship globally. Macron, who had pledged to reopen the cathedral within five years, played a key role in mobilizing funds and organizing the effort, although his involvement sparked debate about his political motivations. The rebuilt Notre-Dame, set to officially reopen in December 2025, is a symbol of collective will and resilience, despite some controversy over modern elements, such as new stained-glass windows."
    
#print(fake_news_det(fake_news))
#print(fake_news_det(real_news))
    
