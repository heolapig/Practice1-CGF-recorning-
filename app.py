import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import plotly.express as px

# 1. 데이터베이스 초기화 및 설정
def init_db():
    conn = sqlite3.connect('cgf_farm_diary.db')
    cursor = conn.cursor()
    # 농장 평가 데이터 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farm_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_name TEXT,
            eval_date TEXT,
            temperature REAL,
            humidity REAL,
            cleanliness INTEGER,
            quarantine INTEGER,
            init_weight REAL,
            weight_deviation REAL,
            end_weight REAL,
            shipment_days INTEGER,
            carcass_weight REAL,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_data(data):
    conn = sqlite3.connect('cgf_farm_diary.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO farm_evaluations 
        (farm_name, eval_date, temperature, humidity, cleanliness, quarantine, 
         init_weight, weight_deviation, end_weight, shipment_days, carcass_weight, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()

def load_data():
    conn = sqlite3.connect('cgf_farm_diary.db')
    df = pd.read_sql_query("SELECT * FROM farm_evaluations", conn)
    conn.close()
    return df

# DB 초기화
init_db()

# 2. Streamlit UI 레이아웃 설정
st.set_page_config(page_title="CGF 농장진단 앱", layout="wide", page_icon="🐖")

st.title("🐖 CGF(계약비육농장) 농장진단 어플리케이션")
st.caption("새끼돼지 입식 전 환경 평가 및 출하 성적 기반 AI 데이터 분석 플랫폼")

# 사이드바 메뉴 구성
menu = st.sidebar.selectbox("메뉴 선택", ["입식 전 농장 평가", "출하 후 성적 기록", "농장 데이터 분석 & 비교"])

# 데이터 불러오기
df_records = load_data()

# ---------------------------------------------------------
# 메뉴 1: 입식 전 농장 평가
# ---------------------------------------------------------
if menu == "입식 전 농장 평가":
    st.header("📋 1단계: 입식 전 농장 환경 평가")
    st.info("농장 담당자님, 새끼돼지 입식 전 농장의 환경 지표를 0~7점 기준으로 평가해 주세요.")
    
    with st.form("evaluation_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📍 농장 기본 정보")
            farm_name = st.text_input("농장명 (예: 대박농장)", placeholder="농장 이름을 입력하세요.")
            eval_date = st.date_input("평가 일자", datetime.now()).strftime('%Y-%m-%d')
            
            st.subheader("🌡️ 환경 지표")
            temperature = st.number_input("농장 온도 (°C)", min_value=-10.0, max_value=40.0, value=22.0, step=0.1)
            humidity = st.number_input("농장 습도 (%)", min_value=0.0, max_value=100.0, value=60.0, step=1.0)
            
        with col2:
            st.subheader("🛡️ 관리 수준 평가 (0~7점)")
            cleanliness = st.slider("청결도 수준", 0, 7, 4, help="0: 매우 불량, 7: 매우 청결")
            quarantine = st.slider("방역 수준", 0, 7, 4, help="0: 방역 취약, 7: 철저한 방역")
            
            st.subheader("🐖 입식 돼지 상태")
            init_weight = st.number_input("입식 돼지 평균 체중 (kg)", min_value=0.0, max_value=50.0, value=30.0, step=0.1)
            weight_deviation = st.number_input("입식 돼지 체중 편차 (kg)", min_value=0.0, max_value=20.0, value=2.5, step=0.1)

        submit_btn = st.form_submit_button("평가 데이터 저장하기")
        
        if submit_btn:
            if not farm_name.strip():
                st.error("농장명을 입력해야 저장이 가능합니다.")
            else:
                # 입식 시점에는 종료체중, 출하일령, 도체중을 None(Null)으로 저장
                save_data((farm_name, eval_date, temperature, humidity, cleanliness, quarantine, 
                           init_weight, weight_deviation, None, None, None, "입식완료"))
                st.success(f"🎉 {farm_name}의 입식 전 평가 데이터가 성공적으로 중앙 DB에 누적되었습니다!")

# ---------------------------------------------------------
# 메뉴 2: 출하 후 성적 기록
# ---------------------------------------------------------
elif menu == "출하 후 성적 기록":
    st.header("📊 2단계: 출하 후 결과 지표 기록 (약 6개월 뒤)")
    
    # 아직 출하 성적이 입력되지 않은 농장 필터링
    if not df_records.empty:
        pending_farms = df_records[df_records['status'] == "입식완료"]
        
        if pending_farms.empty:
            st.success("현재 출하 성적 입력을 대기 중인 농장이 없습니다. 새로운 입식 평가를 먼저 진행해주세요.")
        else:
            st.info("출하가 완료된 농장을 선택하고 최종 성적을 입력하여 버전을 업데이트하세요.")
            
            # 선택 창
            farm_options = pending_farms['farm_name'] + " (" + pending_farms['eval_date'] + ")"
            selected_option = st.selectbox("성적 입력 대상 농장 선택", farm_options)
            selected_idx = pending_farms.index[farm_options == selected_option][0]
            target_id = int(df_records.loc[selected_idx, 'id'])
            
            with st.form("shipment_form"):
                col1, col2 = st.columns(2)
                with col1:
                    end_weight = st.number_input("종료 체중 평균 (kg)", min_value=50.0, max_value=200.0, value=115.0, step=0.1)
                    shipment_days = st.number_input("출하일령 (일)", min_value=100, max_value=250, value=180, step=1)
                with col2:
                    carcass_weight = st.number_input("도체중 평균 (kg)", min_value=40.0, max_value=150.0, value=88.0, step=0.1)
                
                update_btn = st.form_submit_button("출하 성적 업데이트")
                
                if update_btn:
                    conn = sqlite3.connect('cgf_farm_diary.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE farm_evaluations 
                        SET end_weight = ?, shipment_days = ?, carcass_weight = ?, status = ?
                        WHERE id = ?
                    ''', (end_weight, shipment_days, carcass_weight, "출하완료", target_id))
                    conn.commit()
                    conn.close()
                    st.success("📈 출하 성적이 업데이트되었으며 성장 적합도 분석에 반영됩니다.")
                    st.rerun()
    else:
        st.warning("등록된 농장 데이터가 존재하지 않습니다.")

# ---------------------------------------------------------
# 메뉴 3: 농장 데이터 분석 & 비교
# ---------------------------------------------------------
elif menu == "농장 데이터 분석 & 비교":
    st.header("🤖 AI 기반 농장 데이터 가시화 및 환경 검증")
    
    if df_records.empty:
        st.warning("분석할 데이터가 부족합니다. 먼저 농장 평가 데이터를 입력해주세요.")
    else:
        # 가상의 타사 종합 데이터가 부족할 때를 대비한 모의 데이터 병합(시각화용)
        st.subheader("📋 전체 누적 데이터 테이블")
        st.dataframe(df_records, use_container_width=True)
        
        # 1. 다른 농장들과의 환경 지표 비교 (방역 vs 청결 vs 온도)
        st.subheader("🔍 우리 농장 vs 전체 농장 환경 지표 비교")
        
        fig_scatter = px.scatter(
            df_records, 
            x="cleanliness", 
            y="quarantine", 
            size="init_weight", 
            color="farm_name",
            hover_data=["temperature", "humidity"],
            labels={"cleanliness": "청결도 (0~7점)", "quarantine": "방역 수준 (0~7점)"},
            title="농가별 청결도 및 방역 수준 분포 (원의 크기는 입식 체중)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # 2. 입식 조건에 따른 성장 적합도 분석 (출하 완료된 데이터 대상)
        st.subheader("💡 입식 환경이 출하 성적에 미치는 영향 분석 (AI 인사이트)")
        df_completed = df_records[df_records['status'] == "출하완료"]
        
        if df_completed.empty:
            st.info("💡 아직 출하가 완료된 농장 데이터가 없어 영향도 분석 프로세스를 대기 중입니다. (출하 데이터 필요)")
            
            # 안내용 샘플 데이터 시각화 시연
            st.caption("💡 [예시 화면] 데이터가 쌓이면 아래와 같은 환경 요인 분석 차트가 자동으로 생성됩니다.")
            sample_df = pd.DataFrame({
                '환경 점수(청결+방역)': [6, 10, 12, 8, 14, 9],
                '출하일령 (일)': [190, 182, 175, 185, 170, 180],
                '농장': ['A농장', 'B농장', 'C농장', 'D농장', 'E농장', 'F농장']
            })
            fig_sample = px.line(sample_df, x='환경 점수(청결+방역)', y='출하일령 (일)', text='농장', markers=True, title="[샘플] 환경 관리 수준이 높을수록 출하일령이 단축되는 경향성")
            st.plotly_chart(fig_sample, use_container_width=True)
        else:
            # 실제 데이터 분석 반영
            df_completed['env_score'] = df_completed['cleanliness'] + df_completed['quarantine']
            
            col1, col2 = st.columns(2)
            with col1:
                fig_analysis = px.scatter(
                    df_completed, 
                    x="env_score", 
                    y="shipment_days",
                    trendline="ols",
                    labels={"env_score": "환경 종합 점수 (청결도+방역)", "shipment_days": "출하일령 (일)"},
                    title="환경 종합 점수와 출하일령의 상관관계"
                )
                st.plotly_chart(fig_analysis, use_container_width=True)
                st.write("💡 **AI 진단:** 추세선(Trendline)의 기울기를 통해 입식 환경 요인이 실제 사육 기간 단축에 얼마나 기여했는지 정량적으로 검증합니다.")
                
            with col2:
                fig_weight = px.bar(
                    df_completed,
                    x="farm_name",
                    y="carcass_weight",
                    color="temperature",
                    labels={"carcass_weight": "도체중 (kg)", "farm_name": "농장명"},
                    title="농가별 도체중 비교 (색상: 입식 당시 온도)"
                )
                st.plotly_chart(fig_weight, use_container_width=True)
