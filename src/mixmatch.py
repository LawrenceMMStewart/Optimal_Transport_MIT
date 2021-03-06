"""
File: mixmatch
Description: Contains functions for mixmatch
Author Lawrence Stewart <lawrence.stewart@ens.fr>
License: Mit License 
"""

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import pandas as pd
from ot.ot1d import *
from src.mixup import *
from sklearn.utils import shuffle
from ot.sinkhorn import *



def generate_noise(X,stddev=0.01):
    """
    Generates noise from a 0 centered normal 
    with stddev as an input parameter with shape
    equal to the shape of X

    Parameters
    --------
    X : array (n,m)
    stddev : float

    Output
    -------
    noise : array (n,m)
    """
    noise = np.random.normal(size=X.shape, scale=stddev)
    return noise


def noisy_augment(X,stddev=0.01,K=10):
    """
    Creates a list of K noisy augmentations of 
    data X using the generate_noise function

    Parameters
    ----------
    X : array (n,m)
    stddev : float 
    K : int

    Output
    --------
    augs : list of size k (containing size (n,m) arrays)
    """
    augs = [X+generate_noise(X,stddev=stddev) for i in range(K)]
    return augs



def mixmatch_ot1d(model,X,Y,U,
    stddev=0.01,alpha=0.75,K=3,naug=5):

    """
    Computes to OT formulation of Mixmatch
    for two batches (X,Y) [labelled data] and
    (U,) [unlabelled data].

    Parameters
    ----------
    model : f() -> tf.tensor (n,1) 
    X : array (n,m) labelled data
    Y : array (n,1) data labels 
    U : array (n,m) unlabelled data
    stddev : float (for noise augmentations)
    alpha : float (for mixup beta dist)
    K : int (size of barycentre)
    naug : int (number of augmentations)


    Output
    -------
    Xprime : array (n1,m) 
    Yprime : array (n1,K)
    Uprime : array (n2,m)
    Qprime : array (n2,K)

    """
    #size of the x batch 
    l = X.shape[0]
    
    #generate noisy augmentations of X
    Xhat = X + generate_noise(X,stddev=stddev)

    #generate K noisy augmentations of U 
    Uaugs = noisy_augment(U,stddev=stddev,K=naug)
    # Uhat = Uaugs[-1] #OLD VERSION
    Uhat = np.concatenate(Uaugs,axis=0)

    #predict labels and convert to numpy arrays
    modeln = lambda x : model(x).numpy()
    preds = list(map(modeln,Uaugs))

    #labels for unlabelled data
    Q = np.concatenate(preds,axis=1)
    #sort labels into increasing order for barycentre calcs
    Q.sort(axis=1)
    #repeat the labels for each augmentation
    Q = np.tile(Q,[naug,1])

    #mix of data X and U
    W = np.concatenate((Xhat,Uhat),axis=0)

    #mix of labels for X and U 
    Wlabels = Y.tolist()+Q.tolist()
    Wlabels = np.array(Wlabels)

    #shuffle W and its labels together
    W,Wlabels = shuffle(W,Wlabels)

    #mixup Xhat and W
    Xprime,Yprime = mixup_ot1d(Xhat,W[:l],Y,Wlabels[:l],alpha=alpha,K=K)

    #mixup Uhat and W 
    Uprime,Qprime = mixup_ot1d(Uhat,W[l:],Q,Wlabels[l:],alpha=alpha,K=K)
    #return labelled and unlabelled batches
    return Xprime,Yprime,Uprime,Qprime


# @tf.function
# def mixmatchloss_1d(Y,Yhat,Q,Qhat):
#   """
#   Mixmatch loss function for K=1 labels

#   MSE(Y,Yhat) + reg* MSE(Q,Qhat)

#   Parameters
#   ----------
#   Y : array (n,) of varied size arrays float32
#   Yhat : array (n,) of arrays of size (1,1) float32
#   Q : array (n,) of varied size arrays float32
#   Qhat : array (n,) of arrays of size (1,1) float32
#   Output
#   ---------

#   lossx,

#   """
#   mse = tf.keras.losses.MSE

#   lossesx = mse(Y,Yhat)
#   lossesu = mse(Q,Qhat)

#   lossx = tf.reduce_mean(lossesx)
#   lossu = tf.reduce_mean(lossesu)

#   return lossx,lossu





def mixmatchloss_ot(Y,Yhat,Q,Qhat,
    p=tf.constant(2,dtype=tf.float32)):
    """

    Mixmatch loss function using 1D OT:

    loss = 1/n sum_i W_p(y_i,yhat_i) + reg * 1/n sum_i W_p(q_i,qhat_i)

    Parameters
    ----------
    Y : array/list (n,) of varied size arrays float32
    Yhat : array/list (n,) of varied size arrays float32
    Q : array (m,)/list of varied size arrays float32
    Qhat : array (m,)/list of varied size arrays float32
    p : tf.float32 

    Output
    ---------

    lossx : tf.float32
    lossu : tf.float32

    """

    Wp = lambda X,Y : Wasserstein1d_uniform(X,Y,p=p)

    lossesx = list(map(Wp,Y,Yhat))
    lossesu = list(map(Wp,Q,Qhat))

    lossx = tf.reduce_mean(lossesx)
    lossu = tf.reduce_mean(lossesu)


    return lossx,lossu




def ema(model, ema_model, ema_decay=0.9):
    """
    Updates the weights of an ema_model
    according to that of the exponential moving average
    of the weights of a model 

    Parameters
    ----------
    model : tk.keras.model
    ema_model : tf.keras.model
    ema_decay : float
    """
    for var,ema_var in zip(model.variables, ema_model.variables):
        if var.trainable:
            ema_var.assign((1 - ema_decay) * var + ema_decay * ema_var)
        else:
            ema_var.assign(tf.identity(var))



#example of loss function
if __name__=="__main__":
    


    # optimakl transport mixmatch loss example
    y1 = np.array([[1.0],[1.1],[1.3]]).astype(np.float32)
    y2 = np.array([[3.0],[2.95],[3.1]]).astype(np.float32)
    Y = np.array([y1,y2])
    
    Yhat = tf.constant([[[1.0]],[[3.0]]],dtype=tf.float32)

    q1 = np.array([[2.0],[2.01],[1.987]]).astype(np.float32)
    q2 = np.array([[5.1],[5.13],[5.09]]).astype(np.float32)
    Q = np.array([q1,q2])

    Qhat = tf.constant([ [[2.15]],[[5.76]] ],dtype=tf.float32)



    lx,lu = mixmatchloss_ot(Y,Y,Q,Qhat)

    print("lx = ",lx)
    print("lu = ",lu)













