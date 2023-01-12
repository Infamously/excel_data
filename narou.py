import requests
import numpy as np
import pandas as pd
import json
import re
import gzip
import time as tm
import datetime
from bs4 import BeautifulSoup 
from tqdm import tqdm
tqdm.pandas()
import xlsxwriter
interval = 0
#入出力に関する定義(入力元のhtmlや、出力先のファイル名)
filename = 'narou.xlsx'
api_url = "https://api.syosetu.com/novelapi/api/"
scr_url = "https://kasasagi.hinaproject.com/access/monthpv/ncode/" 

#メインのプログラム
def get_novel_info():
  #最終的に入るpandas.Dataframeを作成
  df = pd.DataFrame()

  #作品総数を取得する
  payload = {
    "out" : "json",
    "gzip" : "5",
    "of" : "n",
    "lim" : "1",
  }
  res = requests.get(api_url,params=payload).content
  r = gzip.decompress(res).decode("utf-8")
  allcount = json.loads(r)[0]["allcount"]
  all_queue_cnt = (allcount // 500) + 10

  #現在時間から取得する
  nowtime = datetime.datetime.now().timestamp()
  #lastup = int(nowtime)

  ncode_list = pd.Series

  #メインのAPI操作
  for i in tqdm(range(all_queue_cnt)):
    #取得する条件
    payload = {
      "out" : "json",
      "of" : "t-n-bg-g-k-gf-gl-nt-e-l-gp-f-imp-r-a-ah",
      "gzip" : "5",
      "opt" : "weekly",
      "lim" : "500",
      "lastup" : "1073779200-"+str(lastup)
    }

    #APIで取得、問題時5回までやり直す
    cnt = 0
    while cnt < 5:
      try:
        res = requests.get(api_url , params = payload , timeout = 30).content
        break
      except:
        print("Connection Error")
        cnt += 1
        tm.sleep(120)
    
    #取得したデータのgzipを解凍
    r = gzip.decompress(res).decode("utf-8")
    
    #jsonをpandas.Dataframeに
    df_temp = pd.read_json(r)
    df_temp = df_temp.drop(0)
    df = pd.concat([df,df_temp])
    last_general_lastup = df.iloc[-1]["general_lastup"]
    lastup = datetime.datetime.strptime(last_general_lastup,"%Y-%m-%d %H:%M:%S").timestamp()
    lastup = int(lastup)
    tm.sleep(interval)  
  
    #作品のncodeを分ける
    ncode_list = df_temp["ncode"]
    PVs = []
    e = 0
    #間隔を調整(0.8程度で1秒間隔になる)
    sleep_time = 0.8

    #スクレイピング本体
    for j in tqdm(ncode_list):
      if ncode_list[e + 1]: 
        urls = scr_url + ncode_list[e + 1]
        e = e + 1
        cnt = 0
        while cnt < 5:
      #上で作成したurlでスクレイピング開始、一回ミスったら次へ
          try:
            ncode_res = requests.get(urls,timeout = 30).content
            break
          except:
            print("request error")
            cnt += 1
            tm.sleep(120)
      #受け取ったhtmlをパースする
        soup = BeautifulSoup(ncode_res,"html.parser")
     #受け取るデータが月ごと(且つPCとスマホで別扱い＋総和)なので、それを総合に変換
        sum_pv = 0
        for el in soup.find_all(class_="item"):
       #受け取った数字を一旦文字化
         el_text = str(el.text)
       #PVというのが一番上にあるからそれを0に置換
         el_nomoji = re.sub("PV","0",el_text)
       #桁上がりの","を空白に変換
         el_math = re.sub(",","",el_nomoji)
       #全部文字扱いなので数字に変換し、全部足す
         sum_pv += int(el_math)
       #総和とPC+スマホになって二重に数えているので半分にして配列化
        PVs.append(sum_pv / 2)
      #スクレイピングの待機時間の調整
      tm.sleep(sleep_time)

  #PVの配列をpandas.Seriesに変換(簡単に処理できる？)
  df_Pvs = pd.Series(data = PVs , name = "PV")
  #APIの奴とindexが異なるので、それを正す
  df_Pvs.index = np.arange(1,len(df_Pvs)+1)
  #APIのデータとPVを合体
  df = pd.concat([df,df_Pvs],axis=1)

  #pandas.Dataframeをexcelに出力
  dump_to_excel(df)

def dump_to_excel(df):
  #APIのデータに残ってるallcountを削除
  df = df.drop("allcount", axis=1)
  #重複するncodeを削除
  df.drop_duplicates(subset='ncode', inplace=True)
  #上の関係でindexがずれるのでそれを解決
  df = df.reset_index(drop=True)
  
  #export開始
  print("export_start",datetime.datetime.now())    
  try:
      writer = pd.ExcelWriter(filename,options={'strings_to_urls': False}, engine='xlsxwriter')
      df.to_excel(writer, sheet_name="Sheet1")
      writer.close()
      
      print('取得成功数  ',len(df));
      
  except:
      pass

#プログラムを動かしたらこれから下が動く
#開始時間を通知
print("start",datetime.datetime.now())
#メインのプログラム起動
get_novel_info()
#終了時間を通知
print("end",datetime.datetime.now())