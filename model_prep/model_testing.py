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



model = load_model('model_prep/fake_news_model.h5')
test_data = ["Trey Gowdy destroys this clueless DHS employee when asking about the due process of getting on the terror watch list. Her response is priceless:  I m sorry, um, there s not a process afforded the citizen prior to getting on the list.  ",
       "Donald Trump is afraid of strong, powerful women. He is a horrific misogynist, and has shown himself to be so over and over again. That is nothing new. He has mocked the weight of a beauty queen, made repeated suggestions about women s menstrual cycles, and had repeatedly called women who accuse men   including himself   of sexual harassment and sexual assault of being liars and threatened to sue him. Now, he has gone even lower with an attack on Democratic Senator Kirsten Gillibrand (NY).In an early morning tweet, Trump actually suggested that Senator Gillibrand would have sex with him for campaign money. No, I m not kidding. Here is the tweet:Lightweight Senator Kirsten Gillibrand, a total flunky for Chuck Schumer and someone who would come to my office  begging  for campaign contributions not so long ago (and would do anything for them), is now in the ring fighting against Trump. Very disloyal to Bill & Crooked-USED!  Donald J. Trump (@realDonaldTrump) December 12, 2017For one thing, I don t think Kirsten Gillibrand has to beg the likes of Donald Trump for anything, and she certainly would not stoop anywhere near doing what Trump is suggesting for campaign money. Think about this, folks: the sitting  president  is actually saying that a sitting Senator offered him sex in exchange for campaign money. That is truly beyond the pale. We already knew that Donald Trump was a sexist asshole, but this is a new low, even for him.General Kelly, General McMaster, and whomever else is running that White House   DO SOMETHING about this fool s Twitter habit. It is way out of control, and he does great damage to the nation with ever 140 280 character outburst. This is outrageous. Forget the fact that the orange overlord is currently squatting in the Oval Office   no adult, period, should be acting like this.In this watershed  Me Too  moment in America, it is time to call out the Sexist-in-Chief for what he is   a complete misogynist who has no respect for women and never has. Ivanka, Melania, Sarah Huckabee Sanders, Hope Hicks, and all the other women in Trump s orbit need to step up and say that there s been more than enough. Curtail this man s sexist behavior, or turn in your woman card. Every last one of you.Featured image via Alex Wong/Getty Images.",
      ]
stop = stopwords.words('english')
def cleanText(txt):
    txt = txt.lower()
    txt = ' '.join([word for word in txt.split() if word not in (stop)])
    txt = re.sub('[^a-z]',' ',txt)
    return txt  

def predict_news(text):

    tokenizer = Tokenizer(num_words=model_config.MAX_VOCAB_SIZE)
    tokenizer.fit_on_texts(text)  
    
    test = tokenizer.texts_to_sequences(text)
    X_test = pad_sequences(test, maxlen=model_config.MAX_SEQUENCE_LENGTH)

    df_test = pd.DataFrame(text, columns=['test_sent'])
    prediction = model.predict(X_test)
    
    df_test['prediction'] = prediction
    df_test["test_sent"] = df_test["test_sent"].apply(cleanText)
    #df_test['prediction'] = df_test['prediction'].apply(lambda x: "Real" if x >= 0.5 else "Fake")
    
    return df_test['prediction']

#print(predict_news(test_data))
    
    
    
    
