import pandas as pd
import numpy as np
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.neighbors import DistanceMetric
from utils.DBCV import DBCV
from scipy.spatial.distance import euclidean

def evaluate_clusters(data:np.ndarray=None, labels:np.ndarray=None, )->dict:
  '''
    This function takes as input the data as well as the labels from the clustering
    and return the Silhouette, Calinski-Harabasz and Davies-Bouldin scores

    Parameters
    ----------
    data: (np.ndarray)
        data in matrix form
    labels: (np.ndarray)
        labels from clustering

    Returns
    -------
    Dictionary with the scores
  '''
  silhouette = silhouette_score(data, labels)
  cal_har = calinski_harabasz_score(data, labels)
  dav_bould = davies_bouldin_score(data, labels)
  dbcv = DBCV(data, labels, dist_function=euclidean)

  return {'Silhouette_score': silhouette, 'Calinski_Harabasz_score': cal_har, 'Davies_Bouldin_score': dav_bould, "DBCV": dbcv}



def calculate_gower_distance(df:pd.DataFrame=None, categorical_features:list=None)->np.ndarray:
  '''
    Takes a dataframe as an input and returns a gower distance matrix.
    code taken from https://datascience.stackexchange.com/questions/8681/clustering-for-mixed-numeric-and-nominal-discrete-data

    Parameters
    ----------
    df: (pd.DataFrame)
        DataFrame
    categorical_features: (list)
        list with the categorical features of the DataFrame

    Returns
    -------
    A matrix with the pairwise distances
  '''

  variable_distances = []
  
  for col in range(df.shape[1]):
    
    feature = df.iloc[:,[col]]
    if col in categorical_features:
      
      feature_dist = DistanceMetric.get_metric('dice').pairwise(pd.get_dummies(feature, drop_first=True))
        
    else:
      
      feature_dist = DistanceMetric.get_metric('manhattan').pairwise(feature) / max(np.ptp(feature.values),1)


      variable_distances.append(feature_dist)
      

  return np.array(variable_distances).mean(0)