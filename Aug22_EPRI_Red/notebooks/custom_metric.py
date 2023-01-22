import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix

#define our binary custom metrics

def cedric_metric_nonbinary(y_true, y_pred):
    tn, fp1, fp2, fp3, fn1, tp1, m12, m13, fn2, m21, tp2, m23, fn3, m31, m32, tp3 = confusion_matrix(y_true, y_pred).ravel()
    
    n = tn + fp1 + fp2 + fp3
    p1 = fn1 + tp1 + m12 + m13
    p2 = fn2 + m21 + tp2 + m23
    p3 = fn3 + m31 + m32 + tp3
    
    a = 500
    
    metric = (tn / n) * (tp1 / p1) * (tp2 / p2) * (tp3 / p3) * (1 - fn1 / p1) ** a * (1 - fn2 / p2) ** a * (1 - fn3 / p3) ** a 
    return metric

def cedric_metric_binary(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    a = 500
    metric = (tn / (tn + fp)) * (tp / (tp + fn)) ** a
    
    return metric
	
