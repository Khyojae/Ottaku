import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# --- 페이지 설정 ---
st.set_page_config(
    page_title="👕 천안시 옷가게 지도",
    page_icon="👕",
    layout="wide"
)


# --- 함수 정의 ---
def search_places(api_key, query, lat, lon, radius=20000):
    """카카오 로컬 API를 사용하여 특정 키워드로 장소를 검색하는 함수"""
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {
        "query": query,
        "x": lon,
        "y": lat,
        "radius": radius,  # 반경 20km
        "size": 15
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # 오류가 있으면 예외 발생
        return response.json().get('documents', [])
    except requests.exceptions.RequestException as e:
        st.error(f"API 호출 중 오류 발생: {e}")
        st.error("API 키가 유효한지, 또는 인터넷 연결을 확인해주세요.")
        return None


# --- 사이드바 ---
with st.sidebar:
    st.header("API 키 입력")
    # secrets.toml을 우선적으로 사용하고, 없으면 직접 입력받음
    try:
        default_key = st.secrets.get("kakao_api_key", "")
    except FileNotFoundError:
        default_key = ""

    kakao_api_key = st.text_input(
        "카카오 REST API 키",
        value=default_key,
        type="password",
        help="카카오 개발자 사이트에서 발급받은 REST API 키를 입력하세요."
    )
    st.markdown("---")
    st.info("이 앱은 Streamlit과 카카오맵 API를 활용하여 제작되었습니다.")

# --- 메인 화면 ---
st.title("👕 천안시 옷가게 위치 지도")
st.caption("Streamlit과 카카오맵 API를 활용하여 천안시의 옷가게 위치를 보여줍니다.")

if not kakao_api_key:
    st.warning("사이드바에 카카오 REST API 키를 먼저 입력해주세요.")
    st.stop()  # API 키가 없으면 실행 중지

# 천안시청 좌표를 중심으로 검색
CHEONAN_CITY_HALL_LAT = 36.8151
CHEONAN_CITY_HALL_LON = 127.1139


# 데이터 로딩 및 캐싱
@st.cache_data  # 동일한 키로 함수 재실행 방지
def get_store_data(api_key):
    return search_places(api_key, "천안 옷가게", CHEONAN_CITY_HALL_LAT, CHEONAN_CITY_HALL_LON)


stores = get_store_data(kakao_api_key)

if stores is None:
    st.error("옷가게 정보를 불러오는 데 실패했습니다.")
elif not stores:
    st.info("검색 반경 내에 옷가게 정보가 없습니다.")
else:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader(f"🔍 검색된 옷가게 ({len(stores)}개)")

        # 검색된 가게 리스트 표시
        store_names = [f"{i + 1}. {s['place_name']}" for i, s in enumerate(stores)]
        selected_store_name = st.radio("가게를 선택하면 지도가 이동합니다.", store_names)

        # 선택된 가게 정보 찾기
        selected_index = store_names.index(selected_store_name)
        selected_store = stores[selected_index]

    with col2:
        # Folium을 사용한 지도 생성
        map_center = [float(selected_store['y']), float(selected_store['x'])]
        m = folium.Map(location=map_center, zoom_start=16)

        # 모든 가게에 마커 추가
        for store in stores:
            lat, lon = float(store['y']), float(store['x'])

            # 팝업에 표시될 정보 (HTML 형식)
            popup_html = f"""
            <b>{store['place_name']}</b><br>
            {store['road_address_name']}<br>
            <a href="{store['place_url']}" target="_blank">카카오맵에서 보기</a>
            """
            iframe = folium.IFrame(popup_html, width=200, height=80)
            popup = folium.Popup(iframe, max_width=200)

            # 선택된 가게는 다른 색 아이콘으로 표시
            icon_color = 'blue' if store['id'] == selected_store['id'] else 'gray'

            folium.Marker(
                [lat, lon],
                popup=popup,
                tooltip=store['place_name'],
                icon=folium.Icon(color=icon_color, icon='shopping-bag', prefix='fa')  # Font Awesome 아이콘 사용
            ).add_to(m)

        # 지도 출력
        st_folium(m, width='100%', height=500, returned_objects=[])