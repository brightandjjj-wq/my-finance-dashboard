import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# =====================================================
# 1. 페이지 설정
# =====================================================
st.set_page_config(page_title="주식 분석 대시보드", layout="wide")

# =====================================================
# 2. 데이터 로드 함수 (캐싱 적용)
# =====================================================
@st.cache_data
def load_stock_data(ticker, period):
    # Ticker 객체 자체는 캐싱하지 않고 데이터만 추출하여 반환합니다.
    stock_obj = yf.Ticker(ticker)
    df = stock_obj.history(period=period)
    info = stock_obj.info
    return df, info

# =====================================================
# 3. 사이드바 (설정 영역)
# =====================================================
with st.sidebar:
    st.header("🔍 종목 설정")
    ticker_input = st.text_input("티커 입력 (예: AAPL, TSLA, 005930.KS)", value="AAPL").upper()
    period_input = st.selectbox("분석 기간", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)
    st.divider()
    st.markdown("""
    **💡 Tip**
    - 미국 주식: AAPL, NVDA
    - 한국 코스피: 005930.KS
    - 한국 코스닥: 066910.KQ
    """)

# =====================================================
# 4. 메인 대시보드 로직
# =====================================================
try:
    # 데이터 가져오기
    df, info = load_stock_data(ticker_input, period_input)
    # 캐싱되지 않는 Ticker 객체는 별도로 생성 (재무제표용)
    stock = yf.Ticker(ticker_input)

    # 헤더 섹션
    st.title(f"📊 {info.get('longName', ticker_input)} 분석 대시보드")
    st.caption(f"데이터 기준일: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 분석 기간: {period_input}")
    st.divider()

    # -----------------------------------------------------
    # 상단 지표 (Metric Cards)
    # -----------------------------------------------------
    m1, m2, m3, m4 = st.columns(4)
    curr_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2]
    price_diff = curr_price - prev_price
    pct_diff = (price_diff / prev_price) * 100

    with m1:
        st.metric("현재가", f"${curr_price:,.2f}", f"{price_diff:+.2f} ({pct_diff:+.2f}%)")
    with m2:
        st.metric("52주 최고가", f"${info.get('fiftyTwoWeekHigh', 0):,.2f}")
    with m3:
        # RSI 예시 (데이터가 있다면 계산 로직 추가 가능)
        st.metric("RSI (14)", "10.48", "과매도 구간", delta_color="inverse")
    with m4:
        st.info("💡 종합 의견: 관망 (Hold)")

    st.write("") # 간격

    # -----------------------------------------------------
    # 메인 차트 영역 (Plotly 캔들스틱)
    # -----------------------------------------------------
    col_chart, col_stat = st.columns([2, 1])

    with col_chart:
        with st.container(border=True):
            st.subheader("📈 주가 추세 & 이동평균")
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name="Candlestick"
            )])
            fig.update_layout(
                height=450, 
                margin=dict(l=10, r=10, t=10, b=10),
                template="plotly_white",
                xaxis_rangeslider_visible=False
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_stat:
        with st.container(border=True):
            st.subheader("📊 거래량 추이")
            st.bar_chart(df['Volume'], height=200)
            
            st.subheader("📝 특이사항")
            st.write(f"- 최근 종가: {curr_price:,.2f}")
            st.write(f"- 기간 내 최고가: {df['High'].max():,.2f}")
            st.write(f"- 기간 내 최저가: {df['Low'].min():,.2f}")

    # -----------------------------------------------------
    # 하단 재무 정보 (Tabs)
    # -----------------------------------------------------
    st.divider()
    st.subheader("💰 재무 요약 (핵심 지표)")
    tab1, tab2, tab3 = st.tabs(["손익계산서", "대차대조표", "현금흐름표"])

    with tab1:
        st.dataframe(stock.income_stmt, use_container_width=True)
    with tab2:
        st.dataframe(stock.balance_sheet, use_container_width=True)
    with tab3:
        st.dataframe(stock.cashflow, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ 데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.warning("티커명이 올바른지, 혹은 네트워크 연결 상태를 확인해 주세요.")
