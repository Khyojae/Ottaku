import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta


# --- 1. 기능 함수들 ---

# [신규] 기온별 옷차림 추천 함수
def recommend_clothing(temp):
    """
    기온(temp) 문자열을 입력받아 숫자료 변환하고,
    온도 구간에 따라 적절한 옷차림 추천 문구를 반환하는 함수.
    """
    try:
        # 온도를 숫자로 변환
        temp = float(temp)
    except (ValueError, TypeError):
        return "온도 정보가 없어 추천할 수 없어요."

    if temp >= 28:
        return "민소매, 반팔, 반바지, 원피스 등 매우 가벼운 옷차림을 추천해요. 🥵"
    elif temp >= 23:
        return "반팔, 얇은 셔츠, 반바지, 면바지로 시원하게 입으세요. 😄"
    elif temp >= 17:
        return "얇은 니트, 가디건, 맨투맨, 청바지가 활동하기 좋은 날씨예요. 👍"
    elif temp >= 10:
        return "자켓, 트렌치코트, 니트, 청바지로 멋과 보온을 둘 다 챙기세요.🧥"
    elif temp >= 5:
        return "두꺼운 코트, 가죽 자켓, 플리스, 기모 옷차림이 필요해요. 🥶"
    else:
        return "패딩, 두꺼운 코트, 목도리, 장갑 등 방한용품으로 따뜻하게 입으세요. 🧤"


# API 데이터 요청 함수 (기존과 동일)
def get_weather_data(api_key, base_date, base_time, nx, ny):
    endpoint = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst"
    params = {
        'serviceKey': api_key, 'pageNo': '1', 'numOfRows': '1000', 'dataType': 'JSON',
        'base_date': base_date, 'base_time': base_time, 'nx': nx, 'ny': ny
    }
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 중 오류가 발생했습니다: {e}")
        return None


# API 응답 데이터를 Pivot을 사용해 처리하는 함수 (기존과 동일)
def process_weather_data(data):
    if not data or data['response']['header']['resultCode'] != '00':
        result_msg = data.get('response', {}).get('header', {}).get('resultMsg', '알 수 없는 오류')
        st.error(f"잘못된 응답을 받았습니다: {result_msg}")
        return pd.DataFrame()

    items = data['response']['body']['items']['item']
    df = pd.DataFrame(items)

    df_pivot = df.pivot_table(
        index=['fcstDate', 'fcstTime'], columns='category', values='fcstValue', aggfunc='first'
    ).reset_index()

    sky_codes = {'1': '맑음 ☀️', '3': '구름많음 ☁️', '4': '흐림 🌥️'}
    pty_codes = {'0': '강수 없음', '1': '비 🌧️', '2': '비/눈 🌨️', '3': '눈 ❄️', '4': '소나기 🌦️'}

    if 'SKY' in df_pivot.columns:
        df_pivot['SKY_STATUS'] = df_pivot['SKY'].map(sky_codes)
    if 'PTY' in df_pivot.columns:
        df_pivot['PTY_STATUS'] = df_pivot['PTY'].map(pty_codes).fillna('강수 없음')

    return df_pivot


# base_date, base_time 계산 함수 (기존과 동일)
def get_base_datetime():
    now = datetime.now()
    if now.hour < 2 or (now.hour == 2 and now.minute <= 10):
        base_dt = now - timedelta(days=1)
        base_hour = 23
    else:
        base_dt = now
        available_times = [2, 5, 8, 11, 14, 17, 20, 23]
        base_hour = max(t for t in available_times if t <= now.hour)

    base_date = base_dt.strftime('%Y%m%d')
    base_time = f"{base_hour:02d}00"

    return base_date, base_time


# --- 2. Streamlit UI 구성 ---
st.set_page_config(page_title="오늘의 날씨", page_icon="🌤️")
st.title("🏞️ 기상청 단기예보 조회 서비스")
st.write(f"오늘 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}")

try:
    api_key = st.secrets["KMA_API_KEY"]
except KeyError:
    st.error("설정 오류: .streamlit/secrets.toml 파일에 KMA_API_KEY를 추가해주세요.")
    st.stop()

locations = {
    "서울": (60, 127), "부산": (98, 76), "대구": (89, 90), "인천": (55, 124),
    "광주": (58, 74), "대전": (67, 100), "울산": (102, 84), "세종": (66, 103),
    "경기": (60, 120), "강원": (73, 134), "충북": (69, 107), "충남": (68, 100),
    "전북": (63, 89), "전남": (51, 67), "경북": (89, 91), "경남": (91, 77),
    "제주": (52, 38),
}

selected_location = st.selectbox("조회할 지역을 선택하세요", list(locations.keys()))

if st.button("날씨 조회하기 🚀"):
    with st.spinner('날씨 데이터를 가져오는 중입니다...'):
        nx, ny = locations[selected_location]
        base_date, base_time = get_base_datetime()
        weather_json = get_weather_data(api_key, base_date, base_time, nx, ny)

        if weather_json:
            df = process_weather_data(weather_json)
            if not df.empty:
                st.success(f"**{selected_location}** 지역의 날씨 예보입니다. (데이터 기준: {base_date} {base_time})")

                latest_data = df.iloc[0]
                temp = latest_data.get('TMP', 'N/A')
                sky = latest_data.get('SKY_STATUS', 'N/A')
                pty = latest_data.get('PTY_STATUS', 'N/A')
                pop = latest_data.get('POP', 'N/A')
                wsd = latest_data.get('WSD', 'N/A')
                reh = latest_data.get('REH', 'N/A')

                # --- [변경] UI에 옷차림 추천 기능 호출 및 표시 ---
                clothing_recommendation = recommend_clothing(temp)
                st.info(f"👕 **옷차림 추천:** {clothing_recommendation}")

                # 날씨 정보 메트릭 표시
                st.metric(label="현재 기온", value=f"{temp}°C")
                col1, col2, col3 = st.columns(3)
                col1.metric("하늘 상태", sky)
                col2.metric("강수 형태", pty)
                col3.metric("강수 확률", f"{pop}%")

                col4, col5 = st.columns(2)
                col4.metric("풍속", f"{wsd} m/s")
                col5.metric("습도", f"{reh}%")

                with st.expander("시간대별 상세 예보 보기"):
                    st.dataframe(df)