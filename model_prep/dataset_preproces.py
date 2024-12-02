import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import re
import nltk
import preprocess_kgptalkie as ps
import gensim
from wordcloud import WordCloud

from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Conv1D, MaxPooling1D
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

fake_data = pd.read_csv('model_prep\Fake.csv')
real_data = pd.read_csv('model_prep\True.csv')
#print(fake_data.head())
fake_data = fake_data.drop(['subject', 'date'], axis=1)
real_data = real_data.drop(['subject', 'date'], axis=1)
#print(fake_data.head())
#print(fake_data.shape, real_data.shape)

fake_data['target'] = 'FAKE'
real_data['target'] = 'TRUE'

data = pd.concat([fake_data, real_data], ignore_index=True)
#print(data.shape)

#data.to_csv('news.csv')