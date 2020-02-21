"""
Functions for Regularised OT 
Author Lawrence Stewart <lawrence.stewart@ens.fr>
Liscence: Mit License
"""
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt


def euclidean_dist(X,Y):
    """
    Calculates the euclidean distance from a 

    """

    #obtain number of samples for both X and Y 
    n=X.shape[0]
    m=Y.shape[0]

    #sum over second dimension for each
    X2=tf.reduce_sum(X**2,1) # (n,) 
    Y2=tf.reduce_sum(Y**2,1) # (m,) 

    #add axis 
    X2=tf.expand_dims(X2,1)  #(n ,1)
    Y2=tf.expand_dims(Y2,0) # (1,m)

    #broadcast:
    X2=tf.tile(X2,[1,m])
    Y2=tf.tile(Y2,[n,1])

    return tf.cast(tf.math.sqrt(X2+Y2-2.*X@tf.transpose(Y)),tf.float32)

