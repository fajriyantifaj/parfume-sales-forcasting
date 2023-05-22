# -*- coding: utf-8 -*-
"""Prediksi_penjualan_parfume_time series.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1qqQ2rAP-k7juLaOXSXFzQhV1hDC00NtA
"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
# %matplotlib inline
import seaborn as sns
import re
from pylab import rcParams
import warnings

warnings.filterwarnings('ignore')

data_november = pd.read_excel('/content/sales_november.xlsx')
data_desember = pd.read_excel('/content/sales_desember_2022.xlsx')
data_januari = pd.read_excel('/content/sales_januari.xlsx')
data_februari = pd.read_excel('/content/sales_februari.xlsx')
data_maret = pd.read_excel('/content/sales_maret.xlsx')
data_april = pd.read_excel('/content/sales_april.xlsx')


df = [data_november, data_desember, data_januari, data_februari, data_maret, data_april]
df = pd.concat(df)

df = df[['HARI DAN TANGGAL', 'Product Name', 'Variation', 'Quantity', 'SKU Unit Original Price', 'Order Amount']]
df.rename(columns=lambda x: x.replace(" ", "_").lower() if x != 'HARI DAN TANGGAL' else 'Date', inplace=True)

df = df.dropna()
df.isnull().sum()

def clean_numeric_column(df, column):
    
    df[column] = df[column].str.replace(r'IDR|\.', '', regex=True)
    df[column] = pd.to_numeric(df[column])
    return df

df = clean_numeric_column(df, 'sku_unit_original_price')
df = clean_numeric_column(df, 'order_amount')

total_unit = []
for product in df['product_name']:
        if product == 'OWELA Eve Rosse Eau De Parfume - 3 PCS':
            total_unit.append(3.0)
        elif product == 'OWELA Eve Rosse Eau De Parfume - 5 PCS':  
            total_unit.append(5.0)
        else:           
            total_unit.append(1.0)
df['total_unit'] = total_unit

df['variation'].unique()

def clean_variation(df, column):
    df[column] = df[column].str.replace('BELI 1 GRATIS 1', '2').str.replace(r'BELI|PCS|\s', '', regex=True).astype(float)
    return df

df = clean_variation(df, 'variation')
df.variation.unique()

df['sold_items'] = df['variation'] * df['quantity'] * df['total_unit']

df = df.groupby(df.Date.dt.date)["sold_items"].sum().reset_index()
df = df.set_index('Date')
df.shape

#Plotting the time-series
df.plot(figsize=(20,8))
plt.grid();
plt.xlabel('Date',fontsize=15)
plt.ylabel('sold_item',fontsize=15)
plt.rc('xtick',labelsize=15)
plt.rc('ytick',labelsize=15)
plt.legend(fontsize="x-large")
plt.show()

df.head(2)

df.shape

train, test = df[:77], df[77:]

plt.figure(figsize=(20,4))
pd.plotting.autocorrelation_plot(df);

first_diff=df.diff()[1:]
# first_diff

import statsmodels.tsa.api as smt
fig,axes=plt.subplots(1,2,sharex=False,sharey=False)
fig.set_figwidth(10)
fig.set_figheight(4)
smt.graphics.plot_acf(first_diff, lags=20, ax=axes[0], alpha=0.2) # Autocorelation
smt.graphics.plot_pacf(first_diff, lags=20, ax=axes[1], alpha=0.5) # Partial-Autocorelation
plt.tight_layout()

train.shape

train_len=len(train)
train_len

naive=test.copy()
naive['naive_forecast']=train['sold_items'][train_len-1]
# naive

plt.figure(figsize=(12,4))
plt.plot(train['sold_items'], label='Train')
plt.plot(test['sold_items'], label='Test')
plt.plot(naive['naive_forecast'], label='Naive forecast')
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 12
plt.legend()
plt.title('Naive Method');

from sklearn.metrics import mean_squared_error
rmse = np.sqrt(mean_squared_error(test['sold_items'], naive['naive_forecast'])).round(2)
mape = np.round(np.mean(np.abs(test['sold_items']-naive['naive_forecast'])/test['sold_items'])*100,2)

results = pd.DataFrame({'Method':['Naive method'], 'MAPE': [mape], 'RMSE': [rmse]})
results = results[['Method', 'RMSE', 'MAPE']]
results

"""SES-error ga ada prediksi """

warnings.filterwarnings('ignore')
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
model = SimpleExpSmoothing(train['sold_items'])
model_fit = model.fit(optimized=True)
model_fit.params
simp_expo= test.copy()
simp_expo['simp_expo_forecast'] = model_fit.forecast(len(test))

model_fit.params

plt.figure(figsize=(12,4))
plt.plot(train['sold_items'], label='Train')
plt.plot(test['sold_items'], label='Test')
plt.plot(simp_expo['simp_expo_forecast'], label='Simple exponential smoothing forecast')
plt.legend()
plt.title('Simple Exponential Smoothing Method');

"""holt's method"""

from statsmodels.tsa.holtwinters import ExponentialSmoothing
model = ExponentialSmoothing(np.asarray(train['sold_items']) ,seasonal_periods=12 ,trend='additive', seasonal=None)
model_fit = model.fit(optimized=True)
print(model_fit.params)
holt_trend = test.copy()
holt_trend['holt_trend_forecast'] = model_fit.forecast(len(test))

plt.figure(figsize=(12,4))
plt.plot( train['sold_items'], label='Train')
plt.plot(test['sold_items'], label='Test')
plt.plot(holt_trend['holt_trend_forecast'], label='Holt\'s exponential smoothing forecast')
plt.legend()
plt.title('Holt\'s Exponential Smoothing Method');

rmse = np.sqrt(mean_squared_error(test['sold_items'], holt_trend['holt_trend_forecast'])).round(2)
mape = np.round(np.mean(np.abs(test['sold_items']-holt_trend['holt_trend_forecast'])/test['sold_items'])*100,2)

tempResults = pd.DataFrame({'Method':['Holt\'s exponential smoothing method'], 'RMSE': [rmse],'MAPE': [mape] })
results = pd.concat([results, tempResults])
results = results[['Method', 'RMSE', 'MAPE']]
results

!pip install pmdarima

import pmdarima as pm

def arimamodel(timeseries):
    automodel = pm.auto_arima(timeseries,
                             start_p=1,
                             start_q=1,
                             test='adf',
                             seasonal=True,
                             trace=True,
                             stepwise=False)
    return automodel

from statsmodels.tsa.arima.model import ARIMA
automodel=ARIMA(test,order=(0,1,1))
automodel=automodel.fit()
automodel.summary()

prediction_arima = automodel.predict(n_periodes=test.shape[0])
# prediction_arima

prediction_arima['prediction_arima'] = automodel.predict(n_periodes=test.shape[0])
# prediction_arima['prediction_arima']

plt.figure(figsize=(20,7))
plt.plot(test.index, test, label='Actual')
plt.plot(test.index, prediction_arima['prediction_arima'], label='Forecast')
plt.title('Forcasting - ARIMA')
plt.xlabel('Date')
plt.ylabel('Sold_Items')
plt.legend()
plt.show()

plt.figure(figsize=(12,4))
plt.plot( train['sold_items'], label='Train')
plt.plot(test['sold_items'], label='Test')
plt.plot(prediction_arima['prediction_arima'], label='arima forecast')
plt.legend()
plt.title('ARIMA Method');

rmse = np.sqrt(mean_squared_error(test['sold_items'], prediction_arima['prediction_arima'])).round(2)
mape = np.round(np.mean(np.abs(test['sold_items']-prediction_arima['prediction_arima'])/test['sold_items'])*100,2)

tempResults = pd.DataFrame({'Method':['ARIMA Method'], 'RMSE': [rmse],'MAPE': [mape] })
results = pd.concat([results, tempResults])
results = results[['Method', 'RMSE', 'MAPE']]
results