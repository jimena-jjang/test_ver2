import streamlit as st
import pandas as pd
import plotly.express as px
from logic import calculate_workload, predict_start_date, identify_issues, calculate_utilization_metrics
import textwrap

def render_analysis_report(df: pd.DataFrame, df_resource: pd.DataFrame = None):
    # st.header("📊 데이터 분석 리포트") # Title handled in app.py
    
    st.subheader("스쿼드별 업무 로드 및 리소스 분석")
    
    # Calculate Utilization Metrics
    metrics_df = calculate_utilization_metrics(df, df_resource)
    
    if not metrics_df.empty:
        # 1. Formula Explanation (Detailed Box)
        explanation = """
        **부하율 (%) = (진행중 과제수 ÷ 수행 능력) × 100**
        
        각 항목의 상세 의미는 아래와 같습니다:
        
        - **진행중 과제수 (Active Tasks)**
            오늘 날짜를 기준으로 진행 중인 과제의 수입니다. 
            *(시작일 ≤ 오늘 ≤ 종료일)* 또는 *상태가 '진행 중'*인 과제를 카운트합니다.
        
        - **수행 능력 (Capacity)**
            스쿼드가 동시에 처리할 수 있는 적정 과제 수입니다.
            계산식: `보유 인원 (Headcount)` ÷ `과제당 필요 인원 (Min Personnel)`
            예: 9명의 인원이 있고, 과제당 5명이 필요하다면 → 수행 능력은 **1.8개**가 됩니다.
            
        **[요약]**
        즉, **"스쿼드가 현재 처리 가능한 능력(Capacity) 대비 실제로 얼마나 많은 과제(Active Tasks)를 맡고 있는지"**를 백분율로 나타낸 값입니다.
        - **100% 초과**: 수행 능력보다 많은 일이 몰려있음 (과부하)
        - **100% 미만**: 수행 능력 대비 여유가 있음
        """
        st.info(explanation)
        
        # 2. Key Metrics Visualization (Bar Chart with Load Rate color)
        def get_color(rate):
            if rate >= 1.5: return '#FF4B4B' # Red (Severe)
            if rate >= 1.0: return '#FFA500' # Orange (Warning)
            return '#28a745' # Green (Good)

        metrics_df['Color'] = metrics_df['Load_Rate'].apply(get_color)
        
        # [User Request] Sort by Load Rate descending
        metrics_df = metrics_df.sort_values(by='Load_Rate', ascending=False)
        
        # Enhanced Bar Chart
        fig = px.bar(
            metrics_df, 
            x='Squad', 
            y='Load_Rate',
            title="스쿼드별 부하율 (Load Rate)", 
            text_auto='.0%'
        )
        fig.update_traces(
            marker_color=metrics_df['Color'],
            hovertemplate=(
                "<b>%{x}</b><br>" +
                "Load Rate: %{y:.0%}<br>" +
                "Active Tasks: %{customdata[0]}<br>" +
                "Capacity: %{customdata[1]:.1f}<br>" +
                "Headcount: %{customdata[2]}<br>" +
                "Min Personnel: %{customdata[3]}<extra></extra>"
            ),
            customdata=metrics_df[['Active_Tasks', 'Capacity', 'Headcount', 'Min_Personnel']]
        )
        fig.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="100% Capacity")
        fig.update_layout(yaxis_tickformat=".0%", height=400)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. Detailed Data Table
        st.subheader("📋 상세 데이터")
        
        # Select columns for display
        display_cols = ['Squad', 'Total_Tasks', 'Active_Tasks', 'Headcount', 'Min_Personnel', 'Capacity']
        
        # Create 2 columns for Master-Detail view
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            st.markdown("###### 👈 스쿼드를 선택하여 상세 과제를 확인하세요")
            
            # Interactive Dataframe
            selection = st.dataframe(
                metrics_df[display_cols],
                column_config={
                    "Squad": st.column_config.TextColumn("스쿼드", disabled=True),
                    "Total_Tasks": st.column_config.NumberColumn(
                        "총 과제수", 
                        help="로드된 Roadmap 데이터 기준 전체 과제 개수"
                    ),
                    "Active_Tasks": st.column_config.NumberColumn(
                        "진행중 과제수", 
                        help="오늘 날짜 기준 진행 중인 과제 수 (기간 내 또는 상태='진행 중')"
                    ),
                    "Headcount": st.column_config.NumberColumn(
                        "보유 인원", 
                        help="리소스 데이터(파일/시트)에 등록된 스쿼드별 총 인원"
                    ),
                    "Min_Personnel": st.column_config.NumberColumn(
                        "필요 인원/Task", 
                        help="리소스 데이터(파일/시트)의 'Min_Personnel' 기준. 과제 1개를 수행하는 데 필요한 최소 투입 인원 (기본값: 1명)"
                    ),
                    "Capacity": st.column_config.NumberColumn(
                        "수행 능력", 
                        format="%.1f개", 
                        help="동시에 처리 가능한 적정 과제 수 (보유 인원 ÷ 필요 인원)"
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
                today_date = pd.Timestamp.now()
                # Active Logic: (Date in range) OR (Status == '진행 중')
                # AND Squad == selected_squad
                
                task_mask = (
                    (df['Squad'] == selected_squad) &
                    (
                        ((df['Start'] <= today_date) & ((df['End'] >= today_date) | pd.isna(df['End']))) |
                        (df['Status'] == '진행 중')
                    )
                )
                
                active_tasks_df = df[task_mask].copy()
                
                if not active_tasks_df.empty:
                    # Sort by End date for relevance
                    active_tasks_df = active_tasks_df.sort_values(by='End', na_position='last')
                    
                    st.dataframe(
                        active_tasks_df[['Task', 'Main_Goal', 'Status', 'End']],
                        column_config={
                            "Task": "과제명",
                            "Main_Goal": "목표 (Main Goal)",
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

    st.divider()

    # 5. Issue Tracking (Moved to bottom)
    st.subheader("⚠️ 이슈 및 지연 과제 (Issue Tracking)")
    # identify_issues is imported at the top.
    issues = identify_issues(df)
    
    if not issues.empty:
        st.error(f"총 {len(issues)}건의 이슈가 발견되었습니다.")
        st.dataframe(
            issues[['Squad', 'Task', 'Status', 'End', 'Issue_Type', 'Comment']], 
            use_container_width=True,
            column_config={
                "Squad": "스쿼드",
                "Task": "과제명",
                "Status": "상태",
                "End": st.column_config.DateColumn("종료일", format="YYYY-MM-DD"),
                "Issue_Type": "이슈 유형",
                "Comment": "비고/설명"
            }
        )
    else:
        st.success("발견된 이슈가 없습니다.")

# Mock for logic that wasn't fully defined in previous step or needs import fix
# logic.py didn't include start_swap_scenario, so removing import or fixing usage.
# Fixed usage above by implementing simple list instead of complex swap logic function if not exists.
# Wait, I didn't define start_swap_scenario in logic.py. I'll stick to logic implemented in tab3.
