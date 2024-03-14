import streamlit as st
# import streamlit.components.v1 as components
import pandas as pd
import boto3
import time
import logging
import datetime
import json
import toml
import os
# import extra_streamlit_components as stx
import extra_streamlit_components.TabBar as TabBar

logger = logging.getLogger(__name__)

# def get_data_func(m_st):
#     logger.info(m_st)
#     while('exit' in m_st and m_st['exit'] == False):
#         time.sleep(3)
#         logger.info("sleep")
#     logger.info("exit")
@st.cache_data
def get_mapping():
    if os.path.exists('./.streamlit/mapping.toml'):
        with open('./.streamlit/mapping.toml', 'r', encoding='utf-8') as f:
            config = toml.load(f)
            return config['mapping']
    return {}

def set_style():
    st.set_page_config(
        page_title="YMPC-TEST App",
        page_icon="👹",
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
        
        .stDownloadButton>button {
            background-color:rgb(255 75 75);
            color: rgb(255 255 255);
            width: 100%;
        }
        .stDownloadButton>button:focus {
            background-color:rgb(150 75 75);
            color: rgb(255 255 255);
        }
        .stDownloadButton>button:hover {
            background-color:rgb(150 75 75);
            color: rgb(255 255 255);
        }
        .st-do p {
            font-size:24px;
        }
        .st-bu {
            ackground-color:#fffbf0
        }
        .st-bt {
            border-bottom-color:#F63366
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
        client = session.client('iam')
        client.list_users()
    except:
        logger.error("認証エラー")
        return False
    return True

def get_log_data(log_group_name, start_time, end_time, ccuid = ""):
    session = boto3.session.Session(aws_access_key_id=st.session_state['accessKey'],
                                    aws_secret_access_key=st.session_state['secretKey'],
                                    region_name='ap-northeast-1')
    client = session.client('logs')
    next_token = ''
    response = {}
    filterStr = ''

    if len(ccuid) > 0:
        filterStr = '{($.type = "status") && ($.ccuid = "' + ccuid + '")}'
    else:
        filterStr = '{$.type = "status"}'

    while True:
        if next_token == '':
            response = client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time,
                endTime=end_time,
                filterPattern=filterStr
            )
        else:
            response = client.filter_log_events(
                logGroupName=log_group_name,
                startTime=start_time,
                endTime=end_time,
                filterPattern=filterStr,
                nextToken=next_token
            )

        if 'nextToken' in response:
            next_token = response['nextToken']
            yield response['events']
        else:
            break

def get_jp_dt(utc_dt_str):
    if len(utc_dt_str) > 0:
        try:
            return datetime.datetime.strptime(utc_dt_str, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=9)
        except:
            return ""
    return ""

def get_data1():
    logger.info("get_data1")
    log_group = '/aws/lambda/ympc_iot_data_transfer_lambda'
    utc_now = datetime.datetime.now() + datetime.timedelta(hours=-9)
    start_dt = utc_now + datetime.timedelta(hours=-48)
    start_unix = int(start_dt.timestamp() * 1000)
    end_dt = datetime.datetime.now() + datetime.timedelta(hours=24)
    end_unix = int(end_dt.timestamp() * 1000)

    data1 = []
    if 'data1' in st.session_state:
        data1 = st.session_state['data1']

    data1_max_dic = {}
    if 'data1_max_dic' in st.session_state:
        data1_max_dic = st.session_state['data1_max_dic']

    m_list = []
    mapping = get_mapping()
    for events in get_log_data(log_group, start_unix, end_unix, ""):
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
                if ccuid in mapping.keys():
                    carno = mapping[ccuid]

                # timestamp = get_jp_dt(get_item_value(json_map, 'timestamp').replace(" UTC", "").replace("T", " "))
                if 'vehicleInfo' in json_map.keys():
                    vehicleInfo = json_map['vehicleInfo']
                    # logger.info(vehicleInfo)
                    for itm in vehicleInfo:
                        timestamp2 = get_jp_dt(get_item_value(itm, 'timestamp').replace(" UTC", "").replace("T", " "))
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

                        reocde = (ccuid, carno, timestamp2, mode, odometer_total,
                                 soc, soh, rsrp, rssi, band, cid, latitude, longitude, altitude,
                                 numOfSatellites, pdop, hdop, vdop, acceleration_x, acceleration_y, acceleration_z)
                        # logger.info(reocde)
                        m_list.append(reocde)

                        if ccuid in data1_max_dic.keys():
                            if timestamp2 > data1_max_dic[ccuid]:
                                data1_max_dic[ccuid] = timestamp2
                        else:
                            data1_max_dic[ccuid] = timestamp2
                    # logger.info(data1_max_dic)

    if len(data1) > 0:
        for i in range(len(data1)):
            tmp = data1[i]
            for recode in m_list:
                if recode[0] == tmp[0] and tmp[2] < recode[2]:
                    data1[i] = recode
                    break

    for recode in m_list:
        if recode[0] in data1_max_dic.keys() \
                and recode[2] == data1_max_dic[recode[0]]:
            flag = False
            for tmp in data1:
                if tmp[0] == recode[0] and tmp[2] == recode[2]:
                    flag = True
                    break

            if not flag:
                data1.append(recode)

    data1.sort(key=sort_func)
    st.session_state['data1_max_dic'] = data1_max_dic
    st.session_state['data1'] = data1
    return data1

# @st.cache_data
def get_data2(ccuid, s_d, e_d):
    logger.info("get_data2")
    log_group = '/aws/lambda/ympc_iot_data_transfer_lambda'
    start_dt = datetime.datetime(s_d.year, s_d.month, s_d.day, 0, 0, 0) + datetime.timedelta(hours=-9)
    end_dt = datetime.datetime(e_d.year, e_d.month, e_d.day, 23, 59, 59) + datetime.timedelta(hours=-9)
    start_unix = int(start_dt.timestamp() * 1000)
    end_unix = int(end_dt.timestamp() * 1000)

    ret_list = []
    mapping = get_mapping()
    for events in get_log_data(log_group, start_unix, end_unix, ccuid):
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
                if ccuid in mapping.keys():
                    carno = mapping[ccuid]

                # timestamp = get_jp_dt(get_item_value(json_map, 'timestamp').replace(" UTC", "").replace("T", " "))
                if 'vehicleInfo' in json_map.keys():
                    vehicleInfo = json_map['vehicleInfo']
                    # logger.info(vehicleInfo)
                    for itm in vehicleInfo:
                        timestamp2 = get_jp_dt(get_item_value(itm, 'timestamp').replace(" UTC", "").replace("T", " "))
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

                        reocde = (timestamp2, mode, odometer_total,
                                 soc, soh, rsrp, rssi, band, cid, latitude, longitude, altitude,
                                 numOfSatellites, pdop, hdop, vdop, acceleration_x, acceleration_y, acceleration_z)
                        # logger.info(reocde)
                        ret_list.append(reocde)

    ret_list.sort(key=sort_func2)
    return ret_list

def sort_func(itms):
    return itms[2]

def sort_func2(itms):
    return itms[0]

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

@st.cache_data
def get_carlist():
    carlist = []
    carlist.append("")
    for val in get_mapping().values():
        carlist.append(val)
    return carlist

def get_car_idx(lable):
    carlist = get_carlist()
    for idx in range(len(carlist)):
        if carlist[idx] == lable:
            return idx
    return 0

def get_ccuid_by_carno(val):
    for k, v in get_mapping().items():
        if v == val:
            return k
    return ""

def main():
    if 'state' not in st.session_state:
        st.caption("⚠️AWSをアクセスするためにアカウントIDとシークレットキーを入力してください。")
        accessKey = st.text_input(label="Access key ID")
        secretKey = st.text_input(label="Secret access key", type='password')
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

        # tabs = ["🐶稼働状況　　　　　　　　　", "🐹ログ情報　　　　　　　　　"]
        # tab1, tab2 = st.tabs(tabs)

        # with st.spinner('処理実行中、しばらくお待ちください。'):
        chosen_id = TabBar.tab_bar(data=[
            TabBar.TabBarItemData(id=1, title="🐶稼働状況　　　　　　　　　", description="定周期で稼働状況を検索する"),
            TabBar.TabBarItemData(id=2, title="🐹ログ情報　　　　　　　　　", description="ログ情報を検索する      "),
        ], default=1)
        # logger.info(chosen_id)
        # with st.spinner('検索処理実行中、しばらくお待ちください。'):
        # with tab1:
        if chosen_id == '1':
            st.session_state['tab'] = 1
            st.subheader('◆検索条件')
            with st.form("my_form1"):
                flag = False
                if 'second' in st.session_state and st.session_state['second'] > 0:
                    flag = True

                slider_val = st.slider("データ取得間隔(秒)：", min_value=3, max_value=60, value=10, disabled=flag)
                 # Every form must have a submit button.
                c0, c1 = st.columns([9, 1])

                c0.caption('※定周期で過去48時間から現時点までの最新データを取得する。')
                if 'second' not in st.session_state or st.session_state['second'] == 0:
                    submitted = c1.form_submit_button("検索")
                    if submitted:
                        st.session_state['second'] = slider_val

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
                    columns=(
                        "CCUID", "号車", "データ日時", "走行状態", "走行距離", "SOC", "SOH",
                        "RSRP", "RSSI", "BAND", "CID", "緯度",
                        "経度", "高度", "使用衛星数", "PDOP", "HDOP", "VDOP", "加速度(x)", "加速度(y)", "加速度(z)")
                )
                st.subheader('◆検索結果')
                df.style.set_table_styles([dict(selector="th", props=[('max-width', '1500px')])])
                st.table(df.style.map(subset=['RSRP'], func=color_positive))
                if st.session_state['second'] > 0:
                    time.sleep(0.1)
                    st.experimental_rerun()
            else:
                # pass
                if 'data1' in st.session_state:
                    df = pd.DataFrame(
                        data=st.session_state['data1'],
                        columns=(
                            "CCUID", "号車", "データ日時", "走行状態", "走行距離", "SOC", "SOH",
                            "RSRP", "RSSI", "BAND", "CID", "緯度",
                            "経度", "高度", "使用衛星数", "PDOP", "HDOP", "VDOP", "加速度(x)", "加速度(y)", "加速度(z)")
                    )
                    st.subheader('◆検索結果')
                    df.style.set_table_styles([dict(selector="th", props=[('max-width', '1500px')])])
                    st.table(df.style.map(subset=['RSRP'], func=color_positive))

        # with tab2:
        elif chosen_id == '2':
            # logger.info("---------------------------------")
            if 'second' in st.session_state :
                st.warning("⚠タブの切替に伴って稼働状況の定周期検索処理が停止されました。")
                st.session_state.pop('second')

            st.session_state['tab'] = 2
            st.subheader('◆検索条件')
            # with st.form("my_form2"):
            m_container = st.container()

            today = datetime.datetime.now()
            c1, c2, c3, c4, c5, c6, c7 = m_container.columns([2.3, 0.3, 2.3, 0.4, 2.3, 0.3, 2.3])
            car_idx = 0
            if 'carno' in st.session_state:
                car_idx = get_car_idx(st.session_state['carno'])

            carno = c1.selectbox("車号:", options=get_carlist(), index=car_idx)
            ccuid = ""
            if 'ccuid' in st.session_state:
                ccuid = st.session_state['ccuid']

            if len(carno) > 0:
                ccuid = get_ccuid_by_carno(carno)
                if len(ccuid) > 0:
                    ccuid = c3.text_input("CCUID:", value=ccuid)
                else:
                    ccuid = c3.text_input("CCUID:", value=ccuid)
            else:
                ccuid = c3.text_input("CCUID:", value=ccuid)

            start_date = today
            if 'start_date' in st.session_state:
                start_date = c5.date_input("開始日付:", value=st.session_state['start_date'])
            else:
                start_date = c5.date_input("開始日付:", today)

            end_date = today
            if 'end_date' in st.session_state:
                end_date = c7.date_input("終了日付:", value=st.session_state['end_date'])
            else:
                end_date = c7.date_input("終了日付:", today)

            c0, c1 = m_container.columns([9, 1])
            c0.caption('※CCUID指定の場合、車号が設定不要')

            if c1.button("検索"):
                # if 'ccuid' in st.session_state:
                #     st.session_state.pop('ccuid')
                # if 'start_date' in st.session_state:
                #     st.session_state.pop('start_date')
                # if 'end_date' in st.session_state:
                #     st.session_state.pop('end_date')

                with st.spinner('検索処理実行中、しばらくお待ちください。'):
                    if len(ccuid) == 0:
                        m_container.error("⚠️CCUIDを入力してください。")
                    elif end_date < start_date:
                        m_container.error("⚠️日付入力不正。")
                    else:
                        st.session_state['carno'] = carno
                        st.session_state['ccuid'] = ccuid
                        st.session_state['start_date'] = start_date
                        st.session_state['end_date'] = end_date
                        retlist = get_data2(ccuid, start_date, end_date)
                        st.session_state['retlist'] = retlist
                        st.experimental_rerun()

            if 'retlist' in st.session_state:
                retlist = st.session_state['retlist']
                df = pd.DataFrame(
                    data=retlist,
                    columns=(
                        "データ日時", "走行状態", "走行距離", "SOC", "SOH",
                        "RSRP", "RSSI", "BAND", "CID", "緯度",
                        "経度", "高度", "使用衛星数", "PDOP", "HDOP", "VDOP", "加速度(x)", "加速度(y)", "加速度(z)")
                )
                st.markdown("""<hr style="height:1px;border:none;color:#F63366;background-color:#F63366;" /> """,
                            unsafe_allow_html=True)
                c1, c2 = st.columns([9, 1])
                c1.subheader('◆検索結果')
                if len(retlist) > 0:
                    st.table(df)
                    csv = df.to_csv(index=True).encode('shift-jis')
                    c2.download_button("📥 CSV出力", csv, get_csv_filename(st.session_state['carno'], st.session_state['ccuid']), "text/csv", key='download-csv')
                else:
                    st.error("⚠️条件満足のデータがありません。")

def get_csv_filename(carno, ccuid):
    now = datetime.datetime.now()
    fn = ""
    if len(carno) > 0:
        fn = "log_" + "No" + carno + "_" + now.strftime("%Y-%m-%d_%H%M%S") + ".csv"
    else:
        fn = "log_" + ccuid + "_" + now.strftime("%Y-%m-%d_%H%M%S") + ".csv"
    return fn

if __name__ == '__main__':
    # try:
        set_style()
        # st.balloons()
        st.header('👹YMPCテスト用ツール')
        main()
    # except:
    #     st.error("システムエラーが発生しました。\n")


