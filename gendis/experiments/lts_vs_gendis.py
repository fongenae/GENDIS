import time
from collections import Counter
import warnings; warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sys
sys.path.append('..')

from genetic import GeneticExtractor

from sklearn.metrics import accuracy_score, log_loss
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV

from tslearn.shapelets import ShapeletModel
from tslearn.datasets import UCR_UEA_datasets


def grabocka_params_to_shapelet_size_dict(n_ts, ts_sz, n_shapelets, l, r):
    base_size = int(l * ts_sz)
    d = {}
    for sz_idx in range(r):
        shp_sz = base_size * (sz_idx + 1)
        d[shp_sz] = n_shapelets
    return d

def fit_lr(X_distances_train, y_train, X_distances_test, y_test, out_path):
    lr = GridSearchCV(
            LogisticRegression(random_state=1337), 
            {
              'penalty': ['l1', 'l2'], 
              'C': [10**i for i in range(-2, 6)] + [5**i for i in range(-2, 6)],
              'class_weight': [None, 'balanced']
            }
        )
    lr.fit(X_distances_train, y_train)
    
    hard_preds = lr.predict(X_distances_test)
    proba_preds = lr.predict_proba(X_distances_test)
    
    hard_preds_train = lr.predict(X_distances_train)
    proba_preds_train = lr.predict_proba(X_distances_train)

    print("[LR] TRAIN Accuracy = {}".format(accuracy_score(y_train, hard_preds_train)))
    print("[LR] TRAIN Logloss = {}".format(log_loss(y_train, proba_preds_train)))
    print("[LR] TEST Accuracy = {}".format(accuracy_score(y_test, hard_preds)))
    print("[LR] TEST Logloss = {}".format(log_loss(y_test, proba_preds)))

    hard_preds = pd.DataFrame(hard_preds, columns=['prediction'])
    proba_preds = pd.DataFrame(proba_preds, columns=['proba_{}'.format(x) for x in set(list(y_train) + list(y_test))])

    hard_preds.to_csv(out_path.split('.')[0]+'_lr_hard.csv')
    proba_preds.to_csv(out_path.split('.')[0]+'_lr_proba.csv')

def lts_discovery(X_train, y_train, X_test, y_test,  nr_shap, l, r, reg, max_it, shap_out_path, pred_out_path, timing_out_path):
    # Fit LTS model, print metrics on test-set, write away predictions and shapelets
    shapelet_dict = grabocka_params_to_shapelet_size_dict(
            X_train.shape[0], X_train.shape[1], int(nr_shap*X_train.shape[1]), l, r
    )
    
    clf = ShapeletModel(n_shapelets_per_size=shapelet_dict, 
                        max_iter=max_it, verbose_level=1, batch_size=1,
                        optimizer='sgd', weight_regularizer=reg)

    start = time.time()
    clf.fit(
        np.reshape(
            X_train, 
            (X_train.shape[0], X_train.shape[1], 1)
        ), 
        y_train
    )
    learning_time = time.time() - start

    print([len(x) for x in clf.shapelets_])
    print(clf.get_weights())

    print('Learning shapelets took {}s'.format(learning_time))

    with open(shap_out_path, 'w+') as ofp:
        for shap in clf.shapelets_:
            ofp.write(str(np.reshape(shap, (-1))) + '\n')

    with open(timing_out_path, 'w+') as ofp:
        ofp.write(str(learning_time))

    X_distances_train = clf.transform(X_train)
    X_distances_test = clf.transform(X_test)

    fit_lr(X_distances_train, y_train, X_distances_test, y_test, pred_out_path)

def gendis_discovery(X_train, y_train, X_test, y_test, shap_out_path, pred_out_path, timing_out_path):
    genetic_extractor = GeneticExtractor(verbose=True, population_size=50, iterations=100, wait=10, plot=None)
    start = time.time()
    genetic_extractor.fit(X_train, y_train)
    genetic_time = time.time() - start

    print('Genetic shapelet discovery took {}s'.format(genetic_time))

    with open(shap_out_path, 'w+') as ofp:
        for shap in genetic_extractor.shapelets:
            ofp.write(str(np.reshape(shap, (-1))) + '\n')

    with open(timing_out_path, 'w+') as ofp:
        ofp.write(str(genetic_time))

    X_distances_train = genetic_extractor.transform(X_train)
    X_distances_test = genetic_extractor.transform(X_test)

    fit_lr(X_distances_train, y_train, X_distances_test, y_test, pred_out_path)

# For each dataset we specify the:
#    * Number of shapelets to extract of each length (specified as a fraction of TS length)
#    * Minimal shapelet length (specified as a fraction of TS length)
#    * Different scales of shapelet lengths
#    * Weight regularizer
#    * Number of iterations
hyper_parameters_lts = {
	#'Adiac': 					[0.3,  0.2,   3, 0.01, 10000],
	#'Beef': 					[0.15, 0.125, 3, 0.01, 10000],
	#'BeetleFly': 				[0.15, 0.125, 1, 0.01, 5000],
    #'BirdChicken': 				[0.3,  0.075, 1, 0.1,  10000],
	#'ChlorineConcentration':    [0.3,  0.2,   3, 0.01, 10000],
	#'Coffee': 					[0.05, 0.075, 2, 0.01, 5000],
	#'DiatomSizeReduction': 		[0.3,  0.175, 2, 0.01, 10000],
	#'ECGFiveDays': 				[0.05, 0.125, 2, 0.01, 10000],
	#'FaceFour': 				[0.3,  0.175, 3, 1.0,  5000],
	#'GunPoint': 				[0.15, 0.2,   3, 0.1,  10000],
	'ItalyPowerDemand':			[0.3,  0.2,   3, 0.01, 5000],
	#'Lightning7': 				[0.05, 0.075, 3, 1,    5000],
	#'MedicalImages': 			[0.3,  0.2,   2, 1,    10000],
	#'MoteStrain': 				[0.3,  0.2,   3, 1,    10000],
	#'SonyAIBORobotSurface1': 	[0.3,  0.125, 2, 0.01, 1000],
	#'SonyAIBORobotSurface2': 	[0.3,  0.125, 2, 0.01, 10000],
	#'Symbols': 					[0.05, 0.175, 1, 0.1,  5000],
	#'SyntheticControl': 		[0.15, 0.125, 3, 0.01, 5000],
	#'Trace': 					[0.15, 0.125, 2, 0.1,  10000],
	#'TwoLeadECG': 				[0.3,  0.075, 1, 0.1,  10000]
}

result_vectors = []
data_loader = UCR_UEA_datasets()

for dataset in hyper_parameters_lts:
    print(dataset)

    # Load the training and testing dataset (features + label vector)
    X_train, y_train, X_test, y_test = data_loader.load_dataset(dataset)

    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1]))
    X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1]))

    # Map labels to [0, .., C-1]
    map_dict = {}
    for j, c in enumerate(np.unique(y_train)):
        map_dict[c] = j
    y_train = pd.Series(y_train).map(map_dict).values
    y_test = pd.Series(y_test).map(map_dict).values

    # Get the best hyper-parameters for LTS (from original paper)
    nr_shap, l, r, reg, max_it = hyper_parameters_lts[dataset]

    # GENDIS Discovery & write away results to disk
    gendis_discovery(X_train, y_train, X_test, y_test,  
            'results/lts_vs_genetic/{}_genetic_shapelets_{}.txt'.format(dataset, int(time.time())), 
            'results/lts_vs_genetic/{}_genetic_shapelets_predictions_{}.csv'.format(dataset, int(time.time())),
            'results/lts_vs_genetic/{}_genetic_runtime_{}.csv'.format(dataset, int(time.time()))
    )

    # LTS Discovery & write away results to disk
    #lts_discovery(X_train, y_train, X_test, y_test, nr_shap, l, r, reg, max_it,
    #        'results/lts_vs_genetic/{}_learned_shapelets_{}.txt'.format(dataset, int(time.time())), 
    #        'results/lts_vs_genetic/{}_learned_shapelets_predictions_{}.csv'.format(dataset, int(time.time())), 
    #        'results/lts_vs_genetic/{}_learned_runtime_{}.csv'.format(dataset, int(time.time()))
    #)
