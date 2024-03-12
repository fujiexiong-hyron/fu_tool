import streamlit as st
import numpy as np
import pandas as pd
import boto3
import threading
import time
import logging
import datetime
import json

logger = logging.getLogger(__name__)

# def get_data_func(m_st):
#     logger.info(m_st)
#     while('exit' in m_st and m_st['exit'] == False):
#         time.sleep(3)
#         logger.info("sleep")
#     logger.info("exit")

def set_style():

    st.set_page_config(
        page_title="YMPC-TEST App",
        page_icon="🧊",
        layout="wide",  # 'wide' or 'centered'
        initial_sidebar_state="expanded",
        # menu_items={        }
    )

    hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
    st.markdown(hide_st_style, unsafe_allow_html=True)

    st.markdown("""
        <style>
        .stButton>button {
            background-color:rgb(255 75 75);
            color: rgb(255 255 255);
            width: 100%;
        }
        .stButton>button:focus {
            background-color:rgb(150 75 75);
            color: rgb(255 255 255);
        }
        .stButton>button:hover {
            background-color:rgb(150 75 75);
            color: rgb(255 255 255);
        }
        .st-dw {
            font-size:24px;
        }
        .st-do {
            font-size:24px;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown("""
        <style>
            .block-container {
                padding-top: 0px;
            }
            .element-container {
                opacity: 1;
            }
        </style>
        """, unsafe_allow_html=True)

def accesskey_check(accessKey, secretKey):
    if len(str(accessKey)) == 0 or len(str(secretKey)) == 0:
        return False
    try:
        session = boto3.session.Session(aws_access_key_id=accessKey,
                                aws_secret_access_key=secretKey,
                                region_name='ap-northeast-1')
    except:
        logger.error("認証エラー")
        return False
    return True

def get_log_data(log_group_name, start_time, end_time):
    session = boto3.session.Session(aws_access_key_id=st.session_state['accessKey'],
                                    aws_secret_access_key=st.session_state['secretKey'],
                                    region_name='ap-northeast-1')
    client = session.client('logs')
    next_token = ''
    response = {}
    while True:
        if next_token == '':
            response = client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time,
                endTime=end_time,
                filterPattern='{$.type = "status"}'
            )
        else:
            response = client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time,
                endTime=end_time,
                filterPattern='{$.type = "status"}',
                nextToken=next_token
            )

        if 'nextToken' in response:
            next_token = response['nextToken']
            yield response['events']
        else:
            break

# ["ccuid"]
# ["carno"]
# ["timestamp"]
# ["vehicleInfo.timestamp"]
# ["vehicleInfo.mode"]
# ["vehicleInfo.odometer-total"]
# ["vehicleInfo.soc"]
# ["vehicleInfo.soh"]
# ["vehicleInfo.rsrp"]
# ["vehicleInfo.rssi"]
# ["vehicleInfo.band"]
# ["vehicleInfo.cid"]
# ["vehicleInfo.latitude"]
# ["vehicleInfo.longitude"]
# ["vehicleInfo.altitude"]
# ["vehicleInfo.numOfSatellites"]
# ["vehicleInfo.pdop"]
# ["vehicleInfo.hdop"]
# ["vehicleInfo.vdop"]
# ["vehicleInfo.acceleration-x"]
# ["vehicleInfo.acceleration-y"]
# ["vehicleInfo.acceleration-z"]
def get_data1():

    log_group = '/aws/lambda/ympc_iot_data_transfer_lambda'
    now = datetime.datetime.now()
    end_unix = int(now.timestamp() * 1000)

    start_dt = now + datetime.timedelta(hours=-20)
    start_unix = int(start_dt.timestamp() * 1000)

    data1 = []
    if 'data1' in st.session_state:
        data1 = st.session_state['data1']

    data1_max_dic = {}
    if 'data1_max_dic' in st.session_state:
        data1_max_dic = st.session_state['data1_max_dic']

    list = []
    for events in get_log_data(log_group, start_unix, end_unix):
        for item in events:
            msg = str(item['message']).strip()
            if msg.find('Processing KinesisData:') > 0 and msg.find('{', msg.find('Processing KinesisData:')) > 0:
                msg = msg[msg.find('{', msg.find('Processing KinesisData:')):]
                json_map = json.loads(msg)
                # logger.info(json_map)
                typestr = get_item_value(json_map, 'type')
                if typestr != 'status':
                    continue

                ccuid = get_item_value(json_map, 'ccuid')
                carno = "-"
                timestamp = get_item_value(json_map, 'timestamp').replace(" UTC", "").replace("T", " ")
                if 'vehicleInfo' in json_map.keys():
                    vehicleInfo = json_map['vehicleInfo']
                    # logger.info(vehicleInfo)
                    for itm in vehicleInfo:
                        timestamp2 = str(get_item_value(itm, 'timestamp').replace(" UTC", "").replace("T", " "))
                        mode = str(get_item_value(itm, 'mode'))
                        odometer_total = str(get_item_value(itm, 'odometer-total'))
                        soc = str(get_item_value(itm, 'soc'))
                        soh = str(get_item_value(itm, 'soh'))
                        rsrp = str(get_item_value(itm, 'rsrp'))
                        rssi = str(get_item_value(itm, 'rssi'))
                        band = str(get_item_value(itm, 'band'))
                        cid = str(get_item_value(itm, 'cid'))
                        latitude = str(get_item_value(itm, 'latitude'))
                        longitude = str(get_item_value(itm, 'longitude'))
                        altitude = str(get_item_value(itm, 'altitude'))
                        numOfSatellites = str(get_item_value(itm, 'numOfSatellites'))
                        pdop = str(get_item_value(itm, 'pdop'))
                        hdop = str(get_item_value(itm, 'hdop'))
                        vdop = str(get_item_value(itm, 'vdop'))
                        acceleration_x = str(get_item_value(itm, 'acceleration-x'))
                        acceleration_y = str(get_item_value(itm, 'acceleration-y'))
                        acceleration_z = str(get_item_value(itm, 'acceleration-z'))

                        reocde = (ccuid, carno, timestamp, timestamp2, mode, odometer_total,
                                 soc, soh, rsrp, rssi, band, cid, latitude, longitude, altitude,
                                 numOfSatellites, pdop, hdop, vdop, acceleration_x, acceleration_y, acceleration_z)
                        # logger.info(reocde)
                        list.append(reocde)

                        if ccuid in data1_max_dic.keys():
                            if datetime.datetime.strptime(timestamp2, "%Y-%m-%d %H:%M:%S") > data1_max_dic[ccuid]:
                                data1_max_dic[ccuid] = datetime.datetime.strptime(timestamp2, "%Y-%m-%d %H:%M:%S")
                        else:
                            data1_max_dic[ccuid] = datetime.datetime.strptime(timestamp2, "%Y-%m-%d %H:%M:%S")
                    # logger.info(data1_max_dic)

    for recode in list:
        if recode[0] in data1_max_dic.keys() \
                and datetime.datetime.strptime(recode[3], "%Y-%m-%d %H:%M:%S") == data1_max_dic[recode[0]]:
            flag = False
            for tmp in data1:
                if tmp[0] == recode[0] and tmp[3] == recode[3]:
                    flag = True
                    break

            if not flag:
                data1.append(recode)

    data1.sort(key=sort_func)
    st.session_state['data1_max_dic'] = data1_max_dic
    st.session_state['data1'] = data1
    return data1

def sort_func(itms):
    return itms[3]

def get_item_value(dic, key):
    if key in dic.keys():
        return dic[key]
    return ''

def color_positive(org_val):
    try:
        val = int(org_val)
        if val <= -140:
            color = 'gray'
        elif val >= -139 and val <= -120:
            color = 'red'
        elif val >= -119 and val <= -100:
            color = 'orange'
        elif val >= -99 and val <= -90:
            color = 'green'
        elif val >= -89 and val <= -44:
            color = 'lightgreen'
        else:
            color = 'white'
    except:
        color = 'white'
    return 'background: %s' % color

if __name__ == '__main__':
    set_style()
    # st.balloons()
    st.header('👹YMPCテスト用ツール')

    if 'state' not in st.session_state:
        st.caption("⚠️AWSをアクセスするためにアカウントIDとシークレットキーを入力してください。")
        accessKey = st.text_input(label="Access key ID", value="")
        secretKey = st.text_input(label="Secret access key", type='password', value="")
        _, c1 = st.columns([9, 1])
        if c1.button(label='認証'):
            if accesskey_check(accessKey, secretKey):
                st.session_state['state'] = 1
                st.session_state['accessKey'] = accessKey
                st.session_state['secretKey'] = secretKey
                st.experimental_rerun()
            else:
                st.error("アクセスキー認証失敗になりました。")
    else:
        st.caption("⚠️AWSへアクセスするためにアカウントIDとシークレットキーを入力してください。")
        AccessKey = st.text_input(label="Access key ID", disabled=True, value=st.session_state['accessKey'])
        SecretKey = st.text_input(label="Secret access key", type='password', disabled=True, value="***********")
        _, c1 = st.columns([9, 1])
        if c1.button(label='ログアウト'):
            st.session_state.clear()
            st.experimental_rerun()

        tab1, tab2 = st.tabs(["|👁️‍🗨️稼働状況　　　　　　　　　", "|🤖ログ情報　　　　　　　　　"])
        with tab1:
            st.subheader('◆検索条件')
            with st.form("my_form1"):
                flag = False
                if 'second' in st.session_state and st.session_state['second'] > 0:
                    flag = True

                slider_val = st.slider("データ取得間隔(秒)：", min_value=1, max_value=60, value=10, disabled=flag)
                 # Every form must have a submit button.
                _, c1 = st.columns([9, 1])

                if 'second' not in st.session_state or st.session_state['second'] == 0:
                    submitted = c1.form_submit_button("設定&検索")
                    if submitted:
                        st.session_state['second'] = slider_val
                        st.session_state['tab'] = 1
                        st.session_state['first'] = 1
                        # logger.info(st.session_state)
                        st.experimental_rerun()
                else:
                    if c1.form_submit_button(label='停止'):
                        st.session_state['second'] = 0
                        # st.stop()
                        # st.session_state.pop('second')
                        st.experimental_rerun()

            if 'second' in st.session_state:

                if st.session_state['second'] > 0 and 'first' not in st.session_state:
                    st.warning("⚠️定周期でデータ取得が実行中、しばらくお待ちください。")
                    my_bar = st.progress(0)

                    for percent_complete in range(100):
                        time.sleep(slider_val / 100)
                        my_bar.progress(percent_complete + 1)
                    # time.sleep(1)
                    time.sleep(0.1)
                    my_bar.progress(100)
                    my_bar.empty()

                if 'first' in st.session_state:
                    my_bar = st.progress(100)
                    time.sleep(0.1)
                    my_bar.empty()
                    st.session_state.pop('first')

                df = pd.DataFrame(
                    data=get_data1(),
                    columns=("CCUID",
                             "号車",
                             "データ送信日時",
                             "データ取得日時",
                             "走行モード",
                             "総走行距離",
                             "SOC（バッテリー充電状態）",
                             "SOH（バッテリー劣化状態）",
                             "RSRP（LTEの電波強度）",
                             "RSSI（LTEの電波強度（ノイズ含む））",
                             "BAND（現在のLTEのバンド）",
                             "CID（基地局のID）",
                             "緯度(十進法度単位）",
                             "経度(十進法度単位）",
                             "高度",
                             "使用衛星数",
                             "PDOP",
                             "HDOP",
                             "VDOP",
                             "加速度（x)",
                             "加速度（y)",
                             "加速度（z)"))

                st.subheader('◆検索結果')
                # pd.set_option('display.max_rows', 500)
                # df.set_option('display.min_rows', 10)
                df.style.set_table_styles([dict(selector="th", props=[('max-width', '1500px')])])
                # df = df.set_index('CCUID', drop=True)
                # df = df.reset_index(drop=True)
                # st.dataframe(df, 0, 500)
                st.table(df.style.applymap(subset=['RSRP（LTEの電波強度）'], func=color_positive))
                # time.sleep(st.session_state['second'])
                if st.session_state['second'] > 0:
                    time.sleep(1)
                    st.experimental_rerun()
        with tab2:
            st.subheader('◆検索条件')
            with st.form("my_form2"):
                today = datetime.datetime.now()
                # start_date = st.date_input(label="開始日付:", value=today.date())
                # end_date = st.date_input(label="開始日付:", value=today.date())
                c1, c2, c3, c4 = st.columns([2, 1, 2, 5])
                c1.text_input("CCUID:")
                c2.write("号車")
                c1, c2, c3, c4 = st.columns([2, 1, 2, 5])
                start_date = c1.date_input("開始日付:", today + datetime.timedelta(hours=-24))
                end_date = c3.date_input("終了日付:", today)

                _, c1 = st.columns([9, 1])
                submitted = c1.form_submit_button("検索")
                st.session_state['tab'] = 2
                if submitted:
                    st.write("slider")

            st.subheader('◆検索結果')