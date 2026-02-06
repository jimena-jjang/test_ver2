import streamlit as st
import plotly.express as px
import pandas as pd
from logic import STATUS_CONFIG, DEFAULT_STATUS_COLOR

def render_roadmap(df: pd.DataFrame):
    if df.empty:
        st.info("표시할 데이터가 없습니다.")
        return

    # Prepare data for plotting
    plot_df = df.copy()
    
    # Ensure Start and End are datetime
    plot_df['Start'] = pd.to_datetime(plot_df['Start'])
    plot_df['End'] = pd.to_datetime(plot_df['End'])
    
    # Handle missing dates for visualization (skip or default?)
    # Timeline needs valid dates.
    plot_df = plot_df.dropna(subset=['Start', 'End'])
    
    if plot_df.empty:
        st.warning("날짜 정보가 있는 과제가 없습니다.")
        return

    # Color Mapping based on Status logic
    color_discrete_map = {k: v['color'] for k, v in STATUS_CONFIG.items()}
    
    # Create Gantt Chart
    fig = px.timeline(
        plot_df, 
        x_start="Start", 
        x_end="End", 
        y="Squad", # Group by Squad on Y-axis
        color="Status",
        hover_data=["Task", "Goal", "Status", "Start", "End"],
        color_discrete_map=color_discrete_map,
        category_orders={"Squad": list(plot_df['Squad'].unique())} # Respect sort order
    )
    
    # Update Layout
    fig.update_yaxes(autorange="reversed") # Common Gantt convention
    fig.update_layout(
        xaxis_title="기간",
        yaxis_title="스쿼드",
        legend_title="상태",
        height=600 + (len(plot_df['Squad'].unique()) * 20), # Dynamic height
        margin=dict(l=10, r=10, t=30, b=30),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Data Table View (Optional)
    with st.expander("모든 데이터 보기"):
        st.dataframe(df)
