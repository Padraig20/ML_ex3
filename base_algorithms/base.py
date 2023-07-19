import torch
from transformers import AutoTokenizer, AutoModel
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import LabelEncoder
import pandas as pd

def initialize_tokenizer():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")
    model = AutoModel.from_pretrained("distilbert-base-uncased").to(device)

    return device, tokenizer, model

def tokenize_df(df):
    tokenized = tokenizer(df["text"].values.tolist(), padding = True, truncation = True, return_tensors="pt")

    print(tokenized.keys())

    #move on device (GPU)
    #tokenized = {k:torch.tensor(v).to(device) for k,v in tokenized.items()}

    with torch.no_grad():
        hidden = model(**tokenized) #dim : [batch_size(nr_sentences), tokens, emb_dim]

    #get only the [CLS] hidden states
    cls = hidden.last_hidden_state[:,0,:]

    x = cls.to("cpu")
    y = df["label"]

    print(x.shape, y.shape)

    return x, y

def print_results_test(y_test, y_pred, classifier_name):
    with open(output, 'a') as file:
        file.write("--------------" + classifier_name + "--------------\n\n\n")
        file.write(str(confusion_matrix(y_test, y_pred)))
        file.write("\n\n\n")
        file.write(str(classification_report(y_test, y_pred)))
        file.write("\n\n")
        file.write("--------------" + classifier_name + "--------------\n\n\n")

def print_results_opt(gs, classifier_name):
    results = gs.cv_results_
    i = gs.best_index_
    with open(output, 'a') as file:
        file.write("--------------" + classifier_name + "--------------\n")
        file.write("BEST SCORE: " + str(gs.best_score_) + "\n")
        file.write("BEST PARAMS: " + str(gs.best_params_) + "\n")
        file.write("BEST ESTIMATOR: " + str(gs.best_estimator_) + "\n")
        file.write("MEAN ACCURACY: " + str(results['mean_test_accuracy'][i]) + "\n")
        file.write("STANDARD ACCURACY: " + str(results['std_test_accuracy'][i]) + "\n")
        file.write("MEAN F1 SCORE: " + str(results['mean_test_f1_weighted'][i]) + "\n")
        file.write("STANDARD F1 SCORE: " + str(results['std_test_f1_weighted'][i]) + "\n")
        file.write("MEAN PRECISION: " + str(results['mean_test_precision_weighted'][i]) + "\n")
        file.write("STANDARD PRECISION: " + str(results['std_test_precision_weighted'][i]) + "\n")
        file.write("MEAN RECALL: " + str(results['mean_test_recall_weighted'][i]) + "\n")
        file.write("STANDARD RECALL: " + str(results['std_test_recall_weighted'][i]) + "\n")
        file.write("MEAN FITTING TIME: " + str(results['mean_fit_time'][i]) + "\n")
        file.write("MEAN SCORING TIME: " + str(results['mean_score_time'][i]) + "\n")
        file.write("--------------" + classifier_name + "--------------\n\n")

def gs_random_forest_classifier(X, y, scoring):
    param_grid = {
            "n_estimators": [10,50,100]
            }

    gs = GridSearchCV(estimator=RandomForestClassifier(),
                      param_grid=param_grid,
                      scoring=scoring,
                      refit='accuracy',
                      cv=5,
                      verbose=3)
    gs.fit(X, y)

    print_results_opt(gs, "RANDOM FOREST CLASSIFIER")

def gs_k_nearest_neighbors_classifier(X, y, scoring):
    param_grid = {
            "n_neighbors": [1, 3, 5, 10]
            }

    gs = GridSearchCV(estimator=KNeighborsClassifier(),
                      param_grid=param_grid,
                      scoring=scoring,
                      refit='accuracy',
                      cv=5,
                      verbose=5)
    gs.fit(X,y)

    print_results_opt(gs, "K NEAREST NEIGHBORS CLASSIFIER")

def gs_mlp_classifier(X, y, scoring):
    param_grid = {
            "hidden_layer_sizes": [(50,), (100,), (150,)]
            }

    gs = GridSearchCV(estimator=MLPClassifier(),
                      param_grid=param_grid,
                      scoring=scoring,
                      refit='accuracy',
                      cv=5,
                      verbose=3)
    gs.fit(X,y)

    print_results_opt(gs, "MLP CLASSIFIER")

def gs_decision_tree_classifier(X, y, scoring):
    param_grid = { }
    
    gs = GridSearchCV(estimator=DecisionTreeClassifier(),
                      param_grid=param_grid,
                      scoring=scoring,
                      refit='accuracy',
                      cv=5,
                      verbose=3)
    gs.fit(X,y)

    print_results_opt(gs, "DECISION TREE CLASSIFIER")

def test_random_forest_classifier(X_train, y_train, X_test, y_test):
    classifier = RandomForestClassifier()
    classifier.fit(X_train, y_train)
    y_pred = classifier.predict(X_test)
    print_results_test(y_test, y_pred, "RANDOM FOREST CLASSIFIER")

def test_k_nearest_neighbor_classifier(X_train, y_train, X_test, y_test):
    classifier = KNeighborsClassifier()
    classifier.fit(X_train, y_train)
    y_pred = classifier.predict(X_test)
    print_results_test(y_test, y_pred, "K NEAREST NEIGHBOR CLASSIFIER")

def test_mlp_classifier(X_train, y_train, X_test, y_test):
    classifier = MLPClassifier()
    classifier.fit(X_train, y_train)
    y_pred = classifier.predict(X_test)
    print_results_test(y_test, y_pred, "MLP CLASSIFIER")

def test_decision_tree_classifier(X_train, y_train, X_test, y_test):
    classifier = DecisionTreeClassifier()
    classifier.fit(X_train, y_train)
    y_pred = classifier.predict(X_test)
    print_results_test(y_test, y_pred, "DECISION TREE CLASSIFIER")

def test_dummy_classifier(X_train, y_train, X_test, y_test):
    classifier = DummyClassifier(strategy='uniform')
    classifier.fit(X_train, y_train)
    y_pred = classifier.predict(X_test)
    print_results_test(y_test, y_pred, "DUMMY CLASSIFIER")

def train_test_split(data, train_size):
    train = data[:train_size]
    test = data[train_size:]
    return train, test

import sys

if len(sys.argv) != 4:
    print("Usage:\t\tpython base.py (\"opt\"|\"test\") path/to/dataset output.txt")
    sys.exit(1)

mode = sys.argv[1]
path = sys.argv[2]
output = sys.argv[3]

# ...get dataset

## BBC dataset
## https://storage.googleapis.com/dataset-uploader/bbc/bbc-text.csv
df = pd.read_csv(path).sample(frac=1).head(100)

## preprocessing
LE = LabelEncoder()
df['label'] = LE.fit_transform(df['category'])

df.head()

if mode == "opt":
    device, tokenizer, model = initialize_tokenizer()

    df_x, df_y = tokenize_df(df)

    scoring = ['accuracy', 'recall_weighted', 'f1_weighted', 'precision_weighted']

    gs_mlp_classifier(df_x, df_y, scoring)
    gs_decision_tree_classifier(df_x, df_y, scoring)
    gs_random_forest_classifier(df_x, df_y, scoring)
    gs_k_nearest_neighbors_classifier(df_x, df_y, scoring)
elif mode == "test":
    ##dataset splitting... 80/20 rule
    df_train, df_test = train_test_split(df, int(len(df) * .8))

    # https://towardsdatascience.com/feature-extraction-with-bert-for-text-classification-533dde44dc2f

    device, tokenizer, model = initialize_tokenizer()

    df_train_x, df_train_y = tokenize_df(df_train)
    df_test_x, df_test_y = tokenize_df(df_test)

    test_mlp_classifier(df_train_x, df_train_y, df_test_x, df_test_y)
    test_decision_tree_classifier(df_train_x, df_train_y, df_test_x, df_test_y)
    test_random_forest_classifier(df_train_x, df_train_y, df_test_x, df_test_y)
    test_k_nearest_neighbor_classifier(df_train_x, df_train_y, df_test_x, df_test_y)
    test_dummy_classifier(df_train_x, df_train_y, df_test_x, df_test_y)
else:
    print("Unknown Mode!")
    print("Usage:\t\tpython base.py (\"opt\"|\"test\") path/to/dataset output.txt")
    sys.exit(1)



