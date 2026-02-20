import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from logic import calculate_workload, predict_start_date, identify_issues, calculate_utilization_metrics
import textwrap
import utils

def render_analysis_report(df: pd.DataFrame, df_resource: pd.DataFrame = None, df_weights: pd.DataFrame = None):
    # Top Action Bar
    col_action, _ = st.columns([0.2, 0.8])
    with col_action:
        if st.button("🔄 원본 데이터 불러오기", key="analysis_refresh"):
            st.cache_data.clear()
            st.rerun()

    # st.header("📊 데이터 분석 리포트") # Title handled in app.py
    
    # 0. Key Issues & Strategic Tasks (Moved to top)
    st.subheader("⚠️ 주요 이슈 및 전략 과제 (Key Issues & Strategic Tasks)")
    
    st.markdown("""
    <div style="background-color: #FFF3CD; border-left: 5px solid #FFC107; padding: 20px; border-radius: 4px; margin-bottom: 20px;">
        <h4 style="color: #856404; margin-top: 0;">⚠️ Executive Summary</h4>
        <p style="color: #856404;">
            <b>본 테이블은 CEO 검토 및 판단이 필요한 항목만 선별한 요약 리스트입니다.</b>
        </p>
        <ul style="color: #856404;">
            <li><b>이슈</b>: 현재 상황을 공유드리며, 필요 시 진행 여부 또는 우선순위에 대한 판단을 부탁드립니다.</li>
            <li><b>전략과제</b>: 신규로 인입된 전략 과제로, 진행 여부 결정 후 요청 부서에 회신이 필요한 항목입니다.</li>
        </ul>
        <p style="color: #856404; font-size: 0.9em;">
            ※ 각 과제의 배경과 현재 상태는 <b>비고/설명</b> 컬럼을 참고해 주세요.
        </p>
    </div>
    """, unsafe_allow_html=True)
    # identify_issues is imported at the top.
    issues = identify_issues(df)
    
    if not issues.empty:
        # [User Request] Add icons to Status column
        issues['Status'] = issues['Status'].apply(lambda x: f"{utils.get_status_style(x).get('icon', '')} {x}")

        st.error(f"총 {len(issues)}건의 이슈가 발견되었습니다.")
        # Prepare columns for display
        # Ensure Project column exists (it might be missing if source data didn't have it)
        display_cols = ['Squad', 'Task', 'Status', 'Comment']
        if 'Project' in issues.columns:
            display_cols.insert(1, 'Project') # Insert Project after Squad
            
        st.dataframe(
            issues[display_cols], 
            use_container_width=True,
            column_config={
                "Squad": "스쿼드",
                "Project": "Project",
                "Task": "과제명",
                "Status": "상태",
                "Comment": "이슈 설명"
            },
            hide_index=True
        )
    else:
        st.success("발견된 이슈가 없습니다.")

    st.divider()
    
    st.subheader("📈 스쿼드별 업무 로드 및 리소스 분석")
    
    # Calculate Utilization Metrics
    metrics_df = calculate_utilization_metrics(df, df_resource, df_weights)
    
    if not metrics_df.empty:
        # 1. Formula Explanation (Detailed Box)
        st.markdown(f"""
        <div class="explanation-card">
            <div class="explanation-title">📊 스쿼드 리소스 분석 (공급 vs 수요)</div>
            <ul>
                <li><b>공급 (Capacity)</b>: 스쿼드에서 공급가능한 과제 리소스
                    <ul>
                        <li>(보유 인원 ÷ 최소 투입 인원) × 5.0 × 0.8</li>
                        <li>회의, 운영 업무 등 고려하여 80% 를 '적정'으로 잡고 계산</li>
                    </ul>
                </li>
                <li><b>수요 (Total Load)</b>: 오늘 기준 진행 중인 과제(상태='진행 중' OR 시작일 ≤ 오늘 ≤ 종료일)들의 Type별 가중치 총합</li>
            </ul>
             <p><b>[해석 가이드]</b></p>
            <ul>
                <li><b>부족 인원 양수(+)</b>: 현재 리소스 대비 과제 부하가 높아 인력 충원이 필요함 🔴</li>
                <li><b>부족 인원 음수(-)</b>: 현재 리소스 대비 과제 부하가 낮아 여유가 있음 🟢</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. Key Metrics Visualization (Grouped Bar Chart)
        # Sort by Shortage descending
        metrics_df = metrics_df.sort_values(by='Shortage', ascending=False)
        
        fig = go.Figure()
        
        # Bar 1: Capacity (Blueish)
        fig.add_trace(go.Bar(
            x=metrics_df['Squad'],
            y=metrics_df['Capacity_Score'],
            name='Capacity (공급)',
            marker_color='#3b82f6',
            customdata=metrics_df[['Shortage']],
            hovertemplate="<b>%{x}</b><br>Capacity Score: %{y:.1f}<br>부족 인원: %{customdata[0]:.1f}명<extra></extra>",
            text=metrics_df['Capacity_Score'],
            texttemplate='%{text:.1f}',
            textposition='auto'
        ))
        
        # Bar 2: Total Load (Redish)
        fig.add_trace(go.Bar(
            x=metrics_df['Squad'],
            y=metrics_df['Total_Load_Score'],
            name='Total Load (수요)',
            marker_color='#ef4444',
            customdata=metrics_df[['Shortage']],
            hovertemplate="<b>%{x}</b><br>Total Load Score: %{y:.1f}<br>부족 인원: %{customdata[0]:.1f}명<extra></extra>",
            text=metrics_df['Total_Load_Score'],
            texttemplate='%{text:.1f}',
            textposition='auto'
        ))
        
        fig.update_layout(
            barmode='group',
            title="스쿼드별 리소스 분석 (Capacity vs Total Load)",
            xaxis_title="스쿼드",
            yaxis_title="Score",
            height=400,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. Detailed Data Table
        st.subheader("📋 상세 데이터")
        
        # Format Head / Min string
        metrics_df['Head_Min'] = metrics_df['Headcount'].astype(str) + " / " + metrics_df['Min_Personnel'].astype(str)
        
        # Select columns for display
        display_cols = ['Squad', 'Head_Min', 'Capacity_Score', 'Total_Load_Score']
        
        # Create tooltip for Active Tasks Score
        score_help_text = "오늘 날짜 기준 진행 중인 과제들의 Type별 가중치 합산 점수\n\n[Type별 점수 기준]"
        if df_weights is not None and not df_weights.empty:
            type_col = next((c for c in df_weights.columns if str(c).strip().lower() == 'type'), None)
            weight_col = next((c for c in df_weights.columns if str(c).strip().lower() == 'weight'), None)
            if type_col and weight_col:
                for _, row in df_weights.iterrows():
                    t = str(row[type_col]).strip()
                    w = str(row[weight_col]).strip()
                    if t and w and t != 'nan' and w != 'nan':
                        score_help_text += f"\n• {t}: {w}점"
        else:
            score_help_text += "\n(데이터 없음)"
            
        # Create 2 columns for Master-Detail view
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            st.markdown("###### 👈 스쿼드를 선택하여 상세 과제를 확인하세요")
            
            # Interactive Dataframe with st.dataframe using style mapping
            styled_df = metrics_df[display_cols].style
            
            selection = st.dataframe(
                styled_df,
                column_config={
                    "Squad": st.column_config.TextColumn("스쿼드", disabled=True),
                    "Head_Min": st.column_config.TextColumn(
                        "보유/최소(Head/Min)", 
                        help="스쿼드의 보유 인원과 과제 1개를 수행하는 데 필요한 최소 투입 인원"
                    ),
                    "Capacity_Score": st.column_config.NumberColumn(
                        "Capacity", 
                        format="%.1f",
                        help="Capacity Score (공급)"
                    ),
                    "Total_Load_Score": st.column_config.NumberColumn(
                        "Total Load", 
                        format="%.1f",
                        help=score_help_text
                    )
                },
                hide_index=True,
                use_container_width=True,
                on_select="rerun",
                selection_mode="single-row"
            )

        with col2:
            if selection and selection.selection.rows:
                selected_index = selection.selection.rows[0]
                selected_squad = metrics_df.iloc[selected_index]['Squad']
                
                st.markdown(f"###### 📌 {selected_squad} - 진행중 과제 목록")
                
                # Filter Active Tasks for selected squad
                task_mask = (
                    (df['Squad'] == selected_squad) &
                    (df['Status'] == '진행 중')
                )
                
                active_tasks_df = df[task_mask].copy()
                
                if not active_tasks_df.empty:
                    # Sort by End date for relevance
                    active_tasks_df = active_tasks_df.sort_values(by='End', na_position='last')
                    
                    st.dataframe(
                        active_tasks_df[['Task', 'Biz_impact', 'Type', 'Status', 'End']],
                        column_config={
                            "Task": "과제명",
                            "Biz_impact": "비즈니스 임팩트 (Biz Impact)",
                            "Type": "Type",
                            "Status": "상태",
                            "End": st.column_config.DateColumn("종료일", format="YYYY-MM-DD")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("해당 스쿼드에 진행 중인 과제가 없습니다.")
            else:
                st.info("👈 좌측 표에서 스쿼드를 선택하면 진행중인 과제 목록이 여기에 표시됩니다.")
    else:
        st.info("데이터가 없습니다.")

    st.divider()

    # 4. Shortest Start Date Prediction (Moved below Detailed Data)
    st.subheader("📅 스쿼드별 최단 시작 가능일 예측")
    
    squads = df['Squad'].unique()
    # Filter '미정', '공통' again if inconsistent, but df implies full data. logic.py filters metrics_df only.
    # We should respect the filter for this view too.
    filtered_squads = [s for s in squads if s not in ['미정', '공통']]
    
    # We need to ensure logic.predict_start_date is available. It is imported at the top.
    
    prediction_data = []
    for squad in filtered_squads:
        pred_date = predict_start_date(df, squad)
        prediction_data.append({
            "Squad": squad,
            "Possible Start Date": pred_date
        })
    
    if prediction_data:
        pred_df = pd.DataFrame(prediction_data)
        # Sort by date for better visibility
        pred_df = pred_df.sort_values(by="Possible Start Date")
        
        st.dataframe(
            pred_df,
            column_config={
                "Squad": st.column_config.TextColumn("스쿼드"),
                "Possible Start Date": st.column_config.DateColumn(
                    "최단 시작 가능일",
                    format="YYYY-MM-DD"
                )
            },
            hide_index=True,
            use_container_width=True
        )
        st.caption("※ 각 스쿼드의 현재 진행 중인 마지막 과제 종료일 다음 날을 기준으로 계산됩니다.")
    else:
        st.info("예측 가능한 스쿼드 데이터가 없습니다.")



# Mock for logic that wasn't fully defined in previous step or needs import fix
# logic.py didn't include start_swap_scenario, so removing import or fixing usage.
# Fixed usage above by implementing simple list instead of complex swap logic function if not exists.
# Wait, I didn't define start_swap_scenario in logic.py. I'll stick to logic implemented in tab3.
