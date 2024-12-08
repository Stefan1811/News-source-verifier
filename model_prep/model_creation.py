import pandas as pd
import numpy as np
import itertools
import seaborn as sns
import nltk, re, string
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
from tensorflow.keras.models import load_model

import model_config
import os 

#nltk.download('stopwords')

data = pd.read_csv('model_prep/news.csv')
#print(data.head())

def extract_text(text):
    regex = re.search(r"(?<=\(Reuters\)\s\-\s).*",text)
    if regex:
        return regex.group(0)
    return text

data['text_processed'] = data['text'].apply(extract_text)
data.drop(['Unnamed: 0'], axis=1, inplace=True)

#print(data.head())

data['final_news'] = data['title'] + ' ' + data['text_processed']

#print(data.head())

data = data.drop(['title', 'text', 'text_processed'], axis=1)

#print(data.head())

stop = stopwords.words('english')
def clean_text(text):
    text = text.lower()
    text = ' '.join(word for word in text.split() if word not in stop)
    text = re.sub(r'[^a-z]',' ',text)
    return text

data['final_news'] = data['final_news'].apply(clean_text)

#print(data.head())

data['target'] = data['target'].apply(lambda x: 0 if x == 'FAKE' else 1)

#print(data.head())  

y = data['target'].values
X = data.drop(['target'], axis=1)

#print(X.shape, y.shape)

word_to_vector = {} 
with open(model_config.EMBEDDING_FILE, encoding='utf-8') as f:
    for line in f:
        values = line.split()
        word = values[0]
        vec = np.asarray(values[1:], dtype='float32')
        word_to_vector[word] = vec
        
#print('Found %s word vectors.' % len(word_to_vector))

tokenizer = Tokenizer(num_words=model_config.MAX_VOCAB_SIZE)
tokenizer.fit_on_texts(list(X['final_news']))
X = tokenizer.texts_to_sequences(list(X['final_news']))
X = pad_sequences(X, maxlen=model_config.MAX_SEQUENCE_LENGTH)
#print(X.shape)

word_to_index = tokenizer.word_index
#print('Found %s unique tokens.' % len(word_to_index))   

# get the embedding matrix for the words we have in the dataset
number_of_words = min(model_config.MAX_VOCAB_SIZE, len(word_to_index) + 1)
embedding_matrix = np.zeros((number_of_words, model_config.EMBEDDING_DIM))
for word, i in word_to_index.items():
    if i < model_config.MAX_VOCAB_SIZE:
        embedding_vector = word_to_vector.get(word)
        if embedding_vector is not None:
            embedding_matrix[i] = embedding_vector
            
embedding_layer = Embedding(number_of_words, model_config.EMBEDDING_DIM, weights=[embedding_matrix], input_length=model_config.MAX_SEQUENCE_LENGTH, trainable=False)

input_ = Input(shape=(model_config.MAX_SEQUENCE_LENGTH,))
x = embedding_layer(input_)
x = Bidirectional(LSTM(15, return_sequences=True))(x)
x = GlobalMaxPool1D()(x)
output = Dense(1, activation='sigmoid')(x)

model = Model(input_, output)

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])
model.summary()

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=18)

prediciton = model.fit(X_train, y_train, batch_size=model_config.BATCH_SIZE, epochs=model_config.EPOCHS, validation_split=model_config.VALIDATION_SPLIT)

pred_test = model.predict(X_test)

print(pred_test)
print('Accuracy: ', accuracy_score(y_test, pred_test.round()))

model.save('fake_news_model.h5')

