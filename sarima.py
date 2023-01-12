# ライブラリーの読み込み
import numpy as np
import pandas as pd
import pmdarima as pm
from pmdarima import utils
from pmdarima import arima
from pmdarima import model_selection
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_percentage_error
from matplotlib import pyplot as plt
from sklearn.metrics import r2_score
p = print
# グラフのスタイルとサイズ
plt.style.use('ggplot')
plt.rcParams['figure.figsize'] = [12, 9]

df = pd.read_csv("month_posts.csv",index_col=0,parse_dates=True)
"""
df.plot()
plt.title('Posts')                            #グラフタイトル
plt.ylabel('Monthly Number of Posts') #タテ軸のラベル
plt.xlabel('Month')                                #ヨコ軸のラベル
plt.show()
"""
df_train, df_test = model_selection.train_test_split(df, test_size=12)
data = df_train.posts.values
utils.decomposed_plot(arima.decompose(data,'additive',m=12),
                      figure_kwargs = {'figsize': (12, 12)} )
print('d =', arima.ndiffs(df))      #d
print('D =',arima.nsdiffs(df,m=12)) #D
data = df.diff(1).diff(12).dropna()
utils.plot_acf(data, alpha=.05, lags=24)
utils.plot_pacf(data, alpha=.05, lags=24)
train = df_train
arima_model = pm.auto_arima(train, 
                            seasonal=True,
                            m=12,
                            trace=True,
                            n_jobs=-1,
                            maxiter=10)
# 予測
##学習データの期間の予測値
train_pred = arima_model.predict_in_sample()
##テストデータの期間の予測値
test_pred, test_pred_ci = arima_model.predict(
    n_periods=df_test.shape[0], 
    return_conf_int=True
)
# テストデータで精度検証
print('RMSE:')
print(np.sqrt(mean_squared_error(df_test, test_pred)))
print('MAE:')
print(mean_absolute_error(df_test, test_pred)) 
print('MAPE:')
print(mean_absolute_percentage_error(df_test, test_pred))
fig, ax = plt.subplots()
ax.plot(df_train[24:].index, df_train[24:].values, label="actual(train dataset)")
ax.plot(df_test.index, df_test.values, label="actual(test dataset)", color="gray")
ax.plot(df_train[24:].index, train_pred[24:], color="c")
ax.plot(df_test.index, test_pred, label="auto ARIMA", color="c") 
ax.fill_between(
    df_test.index,
    test_pred_ci[:, 0],
    test_pred_ci[:, 1],
    color='c',
    alpha=.2)
ax.legend()
plt.show()