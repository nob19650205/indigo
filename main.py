VERSION = "0.1"

# r''' 
# 最終更新: 2024/01/07
# 実行方法: streamlit run cloudantOp.py
# 修正遍歴:
#   Ver.0.1  2024/01/07 

# 修正予定：
#   2023/12/xx  
# '''

import os, logging, datetime, time, requests, unicodedata
import streamlit as st
import pandas as pd
from PIL import Image

# 初期設定
CLOUD_HOST  = "https://6e2b5d9d-bcc9-45b1-b738-e2f8d76b9558-bluemix.cloudantnosqldb.appdomain.cloud"    # cloudant-003434
IAMHOST     = "https://iam.cloud.ibm.com/identity/token"

FAVICON     = Image.open("Dell_128_red.ico")

# testdb 用の設定
CLOUD_DB    = "/testdb"
testdb_WApi = "ZCJopJJ4X5qV7QuCfJmzNwC90soVjDaloh5UVOOsKGJJ"  # testdb Write権限
testdb_RApi = "EVNp9etjeAEARtUPeh4-KILRbgKKN0Egk4rJ-SQlBX3g"  # testdb Read権限

# streamlit 関連オプション
try:
    from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
except ModuleNotFoundError as ex:
    print("""
          session idを取得するためのモジュールが移動された可能性があります。streamlit 1.13では次のモジュールでした。
          streamlit.runtime.scriptrunner.script_run_context.get_script_run_ctx 
          https://discuss.streamlit.io/t/streamlit-script-run-context-gone-with-1-8/23526
          """)

# ロギングの設定
if not os.path.isdir("log"): os.mkdir("log")
logFile = os.path.join(os.getcwd(), "log", datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log")
# from streamlit.logger import get_logger
# logger = get_logger(__name__)
logger = logging.getLogger(__name__)
logger.setLevel(10)     # NOTSET: 0, DEBUG: 10, INFO: 20, WARNING: 30, ERROR: 40, CRITICAL: 50
formatter = logging.Formatter('%(asctime)s:%(lineno)d:%(levelname)s:%(message)s')
sh = logging.StreamHandler()
sh.setLevel(logging.DEBUG)
sh.setFormatter(formatter)
logger.addHandler(sh)
# fh = logging.FileHandler(logFile, encoding='utf-8')     # 'cp932' codec can't encode character を回避
# fh.setLevel(logging.DEBUG)
# fh.setFormatter(formatter)
# logger.addHandler(fh)
# logger.debug(f'VERSION: {VERSION}, logging: {logger.handlers}')

# メイン
def main():
    st.set_page_config(
        page_title="DPPの状態", 
        page_icon=FAVICON,
        initial_sidebar_state="auto", 
        layout="wide") 
    searchStatus = st.empty()
    searchStatusMsg = "##### 確認したいDPPの項目を入力してください"
    searchStatus.markdown(searchStatusMsg)
    sidebar()

    if 'results' not in st.session_state:   st.session_state['results'] = ""

    tab_1, tab_2 = st.tabs(['''**DPP情報**''', '''**使い方**'''])
    with tab_1:
        st.info("#### 検索結果")
        # cloudantCheck()
        if st.session_state['results'] != "":
            RESULT = st.session_state['results']
            st.write("該当件数: " + str(len(RESULT)))
            df_all = pd.DataFrame(RESULT)
            # logger.debug(df_all)
            df_all = df_all.loc[:, ["_id", "ServiceTAG", "CustomerName", "City"]]\
                    .rename(columns={"_id":"DPS #", "ServiceTAG":"タグ #", "CustomerName":"お客様", "City":"市町村"})
            st.write(df_all)
            selected_id = st.selectbox("詳細を表示したい項番を選択", tuple(range(len(RESULT))))
            datailTable = pd.DataFrame({"item": ["DPS #", "タグ #", "SLC", "ComboCode", "お客様", "連絡", "電話", "市町村", "住所"], 
                "登録内容": [
                    RESULT[selected_id]["_id"], 
                    RESULT[selected_id]["ServiceTAG"],
                    RESULT[selected_id]["ServiceLevel"],
                    RESULT[selected_id]["ComboCode"],
                    RESULT[selected_id]["CustomerName"], 
                    RESULT[selected_id]["ContactName"],
                    RESULT[selected_id]["ContactPhone"],
                    RESULT[selected_id]["City"],
                    RESULT[selected_id]["AddressLine1"]
                ]
            })
            datailTable = datailTable.set_index("item")
            st.write(datailTable)

    with tab_2:
        st.info("#### 使い方")
        with st.expander('''**その1**''', expanded=True):
            st.write("こんなことや、")
            st.write("あんなことを、")
            st.write("こういうふうに。")
        with st.expander('''**その2**''', expanded=True):
            st.write("そして、こんなことや、")
            st.write("それで、あんなことを、")
            st.write("それでもこういうふうに。")
    
    # cloudantCheck()

def clearEntry():
    st.session_state['results'] = ""
    for item in ["dpsno", "tagno", "cstnam", "calnam", "caltel", "prefct", "city"]:
        st.session_state[item] = ""

# DPP検索条件のサイドバー
# searchData ={}
def sidebar():
    # logger.info("Start....sidebar")
    slcList = ("全て", "NBD", "SBD")
    st.sidebar.selectbox("SLC",       slcList, key="slc")

    teamList = ("全て", "Araun", "RSB", "Selecty")
    st.sidebar.selectbox("担当チーム", teamList, key="team")

    st.sidebar.button("消去", on_click=clearEntry)
    st.sidebar.button("検索", on_click=readCloudant)

    st.sidebar.success("###### 検索項目")
    st.sidebar.text_input("DPSNo",    placeholder="DPS番号",  label_visibility="collapsed",   key="dpsno")            # .id
    st.sidebar.text_input("TAGNo",    placeholder="TAG番号",    label_visibility="collapsed",   key="tagno")
    st.sidebar.text_input("custName", placeholder="お客様名", label_visibility="collapsed",   key="cstnam")           # CustomerName
    st.sidebar.text_input("callerName",placeholder="ご担当者名",label_visibility="collapsed", key="calnam")           # ContactName
    st.sidebar.text_input("callerTel", placeholder="電話番号", label_visibility="collapsed",  key="caltel")           # ContactPhone
    # st.write("")
    # st.sidebar.warning("###### 追加検索項目")
    st.sidebar.text_input("prefecture",placeholder="都道府県", label_visibility="collapsed",  key="prefct")
    st.sidebar.text_input("City",     placeholder="市町村",   label_visibility="collapsed",   key="city")

    # # streamlitのボタンのカスタマイズ https://qiita.com/teruroom/items/e71f46c8ebc220e1ebf2
    # button_css = f"""
    # <style>
    # div.stButton > button:first-child  {{
    #     font-weight  : bold                ;/* 文字：太字                   */
    #     border       :  5px solid #f36     ;/* 枠線：ピンク色で5ピクセルの実線 */
    #     border-radius: 10px 10px 10px 10px ;/* 枠線：半径10ピクセルの角丸     */
    #     background   : #ddd                ;/* 背景色：薄いグレー            */
    # }}
    # </style>
    # """
    # st.markdown(button_css, unsafe_allow_html=True)
    # searchButton = st.sidebar.button("検索")


# Cloudant のチェック(後々、サーバープログラムに移植)
# def cloudantCheck():
#     token = get_IAMtoken()
#         # writeCloudant(token, jsonData)    
#     readJson = readCloudant(token, "19446804653")
#     print(f'readJson:{readJson}')


# IAM tokenの取得
def get_IAMtoken(auth="READ"):
    if(auth == "WRITE"):    APIKEY = testdb_WApi
    else:                   APIKEY = testdb_RApi

    # logger.debug(f'TOKEN({expires_in: {EXPIRE}, Now:{EPOCHNOW}, len:{len(TOKEN)}, {TOKEN[:4]}....{TOKEN[-4:]}')
    if "TOKEN"  in st.session_state and "EXPIRE" in st.session_state and st.session_state["EXPIRE"] > int(time.time()):
        return st.session_state["TOKEN"]
    
    IAMHEADER = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    IAMDATA = {
        "apikey": APIKEY,
        "response_type": "cloud_iam",
        "grant_type": "urn:ibm:params:oauth:grant-type:apikey"
    }
    response = requests.post(IAMHOST, headers=IAMHEADER, data=IAMDATA)
    TOKEN  = response.json()["access_token"]
    st.session_state["TOKEN"] = TOKEN

    EXPIRE = response.json()["expiration"]
    st.session_state["EXPIRE"] = EXPIRE

    EPOCHNOW = int(time.time())
    # logger.debug(f'TOKEN({auth}): {response.status_code}, expires_in: {EXPIRE}, Now:{EPOCHNOW}, len:{len(TOKEN)}, {TOKEN[:4]}....{TOKEN[-4:]}')
    if response.status_code == 200: 
        return TOKEN
    else:                           
        return "IAMトークンの取得に失敗しました"

# Cloudantから読み出し
# @st.cache_data(ttl=600)
def readCloudant():
    token = get_IAMtoken()    
    CLOUDHEAD = {"Accept-Charset": "utf-8",
                 "Content-Type": "application/json",
                 "Accept": "application/json",
                 "Authorization": "Bearer {}".format(token)
                }

    SELECT_PARM = {"selector": {}}

    # DPSNo = "19446804653"
    DPSNo  = unicodedata.normalize("NFKC", st.session_state.dpsno)              # DPS番号, 英数字は半角、カタカナは全角に変換
    if len(DPSNo):  SELECT_PARM["selector"]["_id"]          = {"$regex": DPSNo}
    tagno  = unicodedata.normalize("NFKC", st.session_state.tagno)              # TAG番号
    if len(tagno):  SELECT_PARM["selector"]["ServiceTAG"]   = {"$regex": tagno}
    cstnam = unicodedata.normalize("NFKC", st.session_state.cstnam)             # お客様名
    if len(cstnam): SELECT_PARM["selector"]["CustomerName"] = {"$regex": cstnam}
    calnam = unicodedata.normalize("NFKC", st.session_state.calnam)             # ご担当者名
    if len(calnam): SELECT_PARM["selector"]["ContactName"]  = {"$regex": calnam}
    caltel = unicodedata.normalize("NFKC", st.session_state.caltel)     # 電話番号
    if len(caltel): SELECT_PARM["selector"]["ContactPhone"] = {"$regex": caltel}
    prefct = unicodedata.normalize("NFKC", st.session_state.prefct)     # 都道府県
    if len(prefct): SELECT_PARM["selector"]["prefecture"]   = {"$regex": prefct}
    city   = unicodedata.normalize("NFKC", st.session_state.city)       # 市町村
    if len(city):   SELECT_PARM["selector"]["City"]         = {"$regex": city}
    # print(f"DPSNo :{DPSNo}\ntagno :{tagno}\ncstnam:{cstnam}\ncalnam:{calnam}\ncaltel:{caltel}\nprefct:{prefct}\ncity  :{city}")
    logger.debug(f"SELECT_PARM:{SELECT_PARM}")
    
    # Cloudantからの読み出し
    # if len(status):
    #     SELECT_PARM["selector"]["$or"] =[]
    #     for item in status:
    #         SELECT_PARM["selector"]["$or"].append({"status": {"$eq": item}})
    if SELECT_PARM != {"selector": {}}:
        cloudresp = requests.post(CLOUD_HOST + CLOUD_DB + "/_find" , headers=CLOUDHEAD, json=SELECT_PARM)
        if cloudresp.status_code == 200:
            st.session_state['results'] = cloudresp.json()["docs"]
    return {} #"データの取得に失敗しました"


if __name__ == "__main__":
    # st.set_page_config(page_title="DPPの状態", layout="wide") 
    main()