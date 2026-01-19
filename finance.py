import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="주식 분석 대시보드", layout="wide")

# 세션 상태 초기화
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "TSLA", "005930.KS"]
if "current_ticker" not in st.session_state:
    st.session_state.current_ticker = "AAPL"

# 2. 데이터 로드 함수 (캐싱 강화: 1시간 동안 유지)
@st.cache_data(ttl=3600)
def get_all_stock_data(ticker, period):
    try:
        stock_obj = yf.Ticker(ticker)
        df = stock_obj.history(period=period)
        if df.empty:
            return None
        # 필요한 모든 정보를 하나의 딕셔너리로 묶어서 반환 (요청 횟수 감소)
        data = {
            "df": df,
            "info": stock_obj.info,
            "income": stock_obj.income_stmt,
            "balance": stock_obj.balance_sheet,
            "cash": stock_obj.cashflow
        }
        return data
    except:
        return None

# 3. 사이드바 (조회 버튼 추가로 서버 부하 감소)
with st.sidebar:
    st.header("⭐ 즐겨찾기")
    for stock_id in st.session_state.watchlist:
        if st.button(f"📌 {stock_id}", key=f"btn_{stock_id}", use_container_width=True):
            st.session_state.current_ticker = stock_id
            st.rerun()
            
    st.divider()
    
    # ⚠️ 중요: Form을 사용하여 입력할 때마다 서버에 요청이 가는 것을 방지
    with st.form("search_form"):
        st.header("🔍 종목 검색")
        ticker_input = st.text_input("티커 입력", value=st.session_state.current_ticker).upper()
        period_input = st.selectbox("기간", ["1mo", "3mo", "6mo", "1y", "2y"], index=3)
        submit_button = st.form_submit_button("데이터 불러오기")
        
        if submit_button:
            st.session_state.current_ticker = ticker_input

    if st.button("현재 종목 즐겨찾기 추가"):
        if st.session_state.current_ticker not in st.session_state.watchlist:
            st.session_state.watchlist.append(st.session_state.current_ticker)
            st.rerun()

# 4. 메인 로직
try:
    # 캐싱된 함수 호출
    data_pack = get_all_stock_data(st.session_state.current_ticker, period_input)
    
    if data_pack:
        df = data_pack["df"]
        info = data_pack["info"]

        st.title(f"📊 {info.get('longName', st.session_state.current_ticker)}")
        
        # 상단 지표
        m1, m2, m3 = st.columns(3)
        curr = df['Close'].iloc[-1]
        diff = curr - df['Close'].iloc[-2]
        m1.metric("현재가", f"${curr:,.2f}", f"{diff:+.2f}")
        m2.metric("52주 최고", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")
        m3.info(f"섹터: {info.get('sector', 'N/A')}")

        # 차트
        with st.container(border=True):
            fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
            fig.update_layout(height=450, template="plotly_white", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        # 재무제표 탭
        st.subheader("💰 재무제표")
        tab1, tab2, tab3 = st.tabs(["손익계산서", "대차대조표", "현금흐름표"])
        with tab1: st.dataframe(data_pack["income"], use_container_width=True)
        with tab2: st.dataframe(data_pack["balance"], use_container_width=True)
        with tab3: st.dataframe(data_pack["cash"], use_container_width=True)
   else:
        st.error("데이터를 가져오지 못했습니다. 티커를 다시 확인하거나 잠시 후 시도하세요.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
