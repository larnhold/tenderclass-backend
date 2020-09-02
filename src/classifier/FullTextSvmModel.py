import re

import nltk
import pandas as pd
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split, cross_val_score
import spacy
from sklearn.base import TransformerMixin, BaseEstimator
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.svm import LinearSVC, SVC
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, TfidfTransformer
from spacy.lang.en.stop_words import STOP_WORDS
from spacy.lang.en import English
import string
from nltk.stem import WordNetLemmatizer

from src.classifier.interfaces.MLModelInterface import MlModelInterface
from src.entity.LabeledTenderCollection import LabelledTenderCollection

punctuations = string.punctuation

class FullTextSvmModel(MlModelInterface):

    def __init__(self):
        nltk.download('punkt')
        nltk.download('wordnet')
        self.stopwords = list(STOP_WORDS)
        self.nlp = spacy.load("en")
        self.lemma = WordNetLemmatizer()
        self.parser = English()
        self.stemmer = nltk.PorterStemmer()
        self.punctuations = string.punctuation
        self.domain_stopwords = ["contract", "system", "service", "tender", "company", "notice", "procurement",
                                 "work", "include", "support", "approximately", "management", "agreement",
                                 "office", "solution", "manage", "product", "design", "program", "project",
                                 "supply", "trust", "equipment"]

        self.stopwords = list(STOP_WORDS)
        self.stopwords.extend(self.domain_stopwords)

    def spacy_tokenizer(self, sentence):
        sentence_tokens = self.parser(sentence)
        sentence_tokens = [word.lemma_.lower().strip() if word.lemma_ != "-PRON-" else word.lower_ for word in sentence_tokens]
        sentence_tokens = [word for word in sentence_tokens if word not in self.stopwords and word not in punctuations]
        return sentence_tokens

    class Predictors(TransformerMixin):

        def __clean_text(self, text):
            if text is None:
                return ""
            return str(text).strip().lower()

        def transform(self, X, **transform_params):
            return [self.__clean_text(text) for text in X]

        def fit(self, X, y=None, **fit_params):
            return self

        def get_params(self, deep=True):
            return {}

    def classify(self, tenders):
        pass

    def train(self, labelled_tenders):
        labelled_tenders_collection = LabelledTenderCollection(labelled_tenders)

        #create the pandas df
        training_df = pd.DataFrame({"titles": labelled_tenders_collection.get_titles(), "descriptions": labelled_tenders_collection.get_descriptions(), "label": labelled_tenders_collection.get_labels()})
        # remove null values (description is not alway set)
        training_df = training_df
        X = training_df['titles']
        ylabels = training_df['label']
        X_train, X_test, y_train, y_test = train_test_split(X, ylabels, test_size=0.1, random_state=0)

        training_df2 = training_df
        training_df2.loc[training_df2["descriptions"].isnull(), 'descriptions'] = training_df2["titles"]
        X2 = training_df[['titles', 'descriptions']]

        #X2 text preprocessing
        def clean(data):
            data = re.sub(r'http\S+', '', data)
            data = re.sub('[^a-zA-Z]', ' ', data)
            data = str(data).lower()
            data = nltk.word_tokenize(data)
            data = [word for word in data if word not in self.stopwords and word not in punctuations]
            data = [self.lemma.lemmatize(word=w, pos='v') for w in data]
            data = [i for i in data if len(i) > 2]
            data = ' '.join(data)
            return data

        #X2['titles'] = X2['titles'].apply(clean)
        #X2['descriptions'] = X2['descriptions'].apply(clean)

        #X2.to_csv('datacleaned.csv')

        ylabels2 = training_df['label']
        X_train2, X_test2, y_train2, y_test2 = train_test_split(X2, ylabels2, test_size=0.1, random_state=0)

        # start with the classic
        # with either pure counts or tfidf features
        sgd = Pipeline([
            ("count vectorizer", CountVectorizer(stop_words="english", max_features=3000)),
            ("sgd", SGDClassifier(loss="modified_huber"))
        ])
        sgd_tfidf = Pipeline([
            ("tfidf_vectorizer", TfidfVectorizer(stop_words="english", max_features=3000)),
            ("sgd", SGDClassifier(loss="modified_huber"))
        ])

        svc = Pipeline([
            ("count_vectorizer", CountVectorizer(stop_words="english", max_features=3000)),
            ("linear svc", SVC(kernel="linear"))
        ])

        svc_tfidf = Pipeline([
            ("tfidf_vectorizer", TfidfVectorizer(stop_words="english", max_features=3000)),
            ("linear svc", SVC(kernel="linear", random_state=0))
        ])

        all_models = [
            ("sgd", sgd),
            ("sgd_tfidf", sgd_tfidf),
            ("svc", svc),
            ("svc_tfidf", svc_tfidf),
        ]

        print(X_train.shape)

        unsorted_scores = [(name, cross_val_score(model, X_train, y_train, cv=2).mean()) for name, model in all_models]
        scores = sorted(unsorted_scores, key=lambda x: -x[1])
        print(scores)
        #svc performs best

        old = Pipeline([("cleaner", self.Predictors()),
                  ('vectorizer', CountVectorizer(tokenizer=self.spacy_tokenizer, ngram_range=(1, 2))),
                  ('classifier', LinearSVC())])

        model = old
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        print("Old Score:")
        print(accuracy_score(y_test, y_pred))

        ###########NEW

        class Ectractor(BaseEstimator, TransformerMixin):

            def __init__(self, column):
                self.column = column
                pass

            def transform(self, df, y=None):
                return df[self.column]

            def fit(self, df, y=None):
                return self

        pipeline = Pipeline([
            ('union', FeatureUnion(
                transformer_list=[
                    ('titles', Pipeline([
                        ('selector', Ectractor(column="titles")),
                        ('vect', CountVectorizer( max_features=1000, tokenizer=self.spacy_tokenizer, ngram_range=(1, 2))),
                        ('tfidf', TfidfTransformer())
                    ])),
                    ('descriptions', Pipeline([
                        ('selector', Ectractor(column="descriptions")),
                        ('vect', CountVectorizer( max_features=1000, tokenizer=self.spacy_tokenizer, ngram_range=(1, 2))),
                        ('tfidf', TfidfTransformer())
                    ])),
                ],
            )),
            ('svc', SVC(kernel="linear", random_state=0)),
        ])

        model = pipeline
        model.fit(X_train2, y_train2)
        y_pred2 = model.predict(X_test2)
        print("Newest Score:")
        print(accuracy_score(y_test2, y_pred2))

    def create_new_model(self):
        pass