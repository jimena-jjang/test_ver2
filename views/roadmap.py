import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import textwrap
import sys
import os
import unicodedata

# Add parent directory to path to allow importing utils if needed (though usually streamlit handles root)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils

def create_professional_gantt(df, group_col='Squad'):
    """Gantt 차트 생성 로직"""
    df_plot = df.copy()
    # -------------------------------------------------------------
    # [Layout Fix] Pixel-based Logic for Panels
    # We convert pixels to "days" so we can draw panels on the x-axis (time domain)
    # This ensures panel width is constant regardless of total duration.
    # -------------------------------------------------------------
    
    # Determine Layout Logic based on Panel usage
    primary_col = group_col
    secondary_col = 'Squad' # Default
    
    # Resolve Secondary Column Logic
    if primary_col == 'Squad':
        if 'project_name' in df_plot.columns: secondary_col = 'project_name'
        elif 'Group' in df_plot.columns: secondary_col = 'Group' 
        elif 'Goal' in df_plot.columns: secondary_col = 'Goal'
        else: secondary_col = None
    elif primary_col == 'Group':
        secondary_col = 'Squad'
    else:
        secondary_col = 'Squad'

    # [Dynamic Panel Width Calculation]
    # Calculate max length to adjust panel width
    max_len_primary = 0
    if not df_plot.empty and primary_col in df_plot.columns:
        # Use visual width (Korean=2, English=1)
        max_len_primary = df_plot[primary_col].astype(str).apply(utils.get_visual_width).max()
        if pd.isna(max_len_primary): max_len_primary = 5
        
    # Heuristic: Base 80px + 11px per visual unit + 40px Padding. 
    # (Visual unit 1 = approx 11px, Visual unit 2 (Korean) = approx 22px) -> More conservative
    PADDING_PX = 40
    calc_primary_px = 80 + (max_len_primary * 11) + PADDING_PX
    SQUAD_PANEL_PX = max(140, min(600, int(calc_primary_px)))
    
    # Calculate max pixel width for wrapping
    # We pass this to utils.wrap_text_by_pixels
    primary_max_px = SQUAD_PANEL_PX - PADDING_PX

    GROUP_PANEL_PX = 200 # Default
    secondary_max_px = 160 # Default
    
    if secondary_col and secondary_col in df_plot.columns:
        max_len_sec = df_plot[secondary_col].astype(str).apply(utils.get_visual_width).max()
        if pd.isna(max_len_sec): max_len_sec = 5
        
        calc_sec_px = 80 + (max_len_sec * 11) + PADDING_PX
        GROUP_PANEL_PX = max(140, min(600, int(calc_sec_px)))
        secondary_max_px = GROUP_PANEL_PX - PADDING_PX

    PX_PER_DAY = 5  # Fixed scale: 5 pixels per 1 day
    # SQUAD_PANEL_PX & GROUP_PANEL_PX set dynamically above
    
    # Calculate Data Range
    data_min_date = df_plot['Start'].min()
    if pd.isna(data_min_date): data_min_date = datetime.now()
    
    data_max_date = df_plot['End'].max()
    if pd.isna(data_max_date): data_max_date = datetime.now() + timedelta(days=30)
    
    # Extend max date for visual breathing room
    vis_max_date = data_max_date + timedelta(days=90)
    
    # Calculate Panel Widths in Days (deltas)
    squad_days = SQUAD_PANEL_PX / PX_PER_DAY
    group_days = GROUP_PANEL_PX / PX_PER_DAY
    
    # (Removed previous static column logic block from here as it's moved up)

    # Calculate Start Date for the Axis (Left edge of panels)
    # Axis Start = Data Start - (Panel Days)
    # We add a small buffer (10 days) between panels and data
    BUFFER_DAYS = 5
    
    total_panel_days = squad_days + BUFFER_DAYS
    if secondary_col:
        total_panel_days += group_days

    axis_min_date = data_min_date - timedelta(days=total_panel_days)
    
    # Calculate Total Width required
    total_plot_days = (vis_max_date - axis_min_date).days
    chart_width = max(1200, total_plot_days * PX_PER_DAY)
    
    # Shapes (Panels) Calculation
    # Primary Panel (Leftmost)
    primary_x0 = axis_min_date
    primary_x1 = axis_min_date + timedelta(days=squad_days)
    
    # Secondary Panel (Next to Primary)
    if secondary_col:
        sec_x0 = primary_x1
        sec_x1 = sec_x0 + timedelta(days=group_days)
    
    # Update Fig Layout early to enforce width
    fig = go.Figure()
    
    # 1. Zebra Background (Full Width)
    for idx in range(len(df_plot)):
        stripe_color = 'rgba(248, 248, 248, 1)' if idx % 2 == 0 else 'rgba(255, 255, 255, 1)'
        # Cover entire visible range
        fig.add_shape(type="rect", x0=axis_min_date, x1=vis_max_date, y0=idx - 0.4, y1=idx + 0.4,
                      fillcolor=stripe_color, line=dict(width=0), layer="below")
    
    
    # 1. Custom Order (from Google Sheet or File)
    custom_order = utils.get_custom_squad_order()
    
    if custom_order:
        # Normalize keys for robust matching
        # Use a high number for undefined squads to put them at the end
        rank_map = {unicodedata.normalize('NFC', str(s)).strip(): i for i, s in enumerate(custom_order)}
        
        def get_squad_rank(squad_name):
            norm_name = unicodedata.normalize('NFC', str(squad_name)).strip()
            # If found in map, return rank. Else return 999.
            return rank_map.get(norm_name, 999)
            
        df_plot['squad_rank'] = df_plot['Squad'].apply(get_squad_rank)
    else:
        # Fallback: '공통' first, others 999 (effective alphabetical if sort includes name)
        df_plot['squad_rank'] = df_plot['Squad'].astype(str).apply(
            lambda x: 0 if '공통' in unicodedata.normalize('NFC', x) else 999
        )
    
    if primary_col == 'Squad':
        sort_cols = ['squad_rank', primary_col, secondary_col, 'Start']
    elif secondary_col == 'Squad':
        sort_cols = [primary_col, 'squad_rank', secondary_col, 'Start']
    else:
        sort_cols = [primary_col, secondary_col, 'Start']
        
    existing_sort_cols = [c for c in sort_cols if c and c in df_plot.columns]
    
    if existing_sort_cols:
         df_plot = df_plot.sort_values(by=existing_sort_cols, ascending=[True] * len(existing_sort_cols))
         
    df_plot = df_plot.reset_index(drop=True)
    df_plot['row_idx'] = range(len(df_plot))
    
    primary_groups = df_plot.groupby(primary_col, sort=False)
    
    # 2-1. Primary Panel Draw using Date Coordinates (xref='x')
    for p_name, p_group in primary_groups:
        min_idx = p_group['row_idx'].min()
        max_idx = p_group['row_idx'].max()
        
        if primary_col == 'Squad':
            if p_name in utils.SQUAD_COLORS:
                panel_color = utils.SQUAD_COLORS[p_name]
            else:
                panel_color = utils.FALLBACK_COLORS[hash(p_name) % len(utils.FALLBACK_COLORS)]
        elif primary_col == 'Status' or unicodedata.normalize('NFC', str(p_name)).strip() in utils.STATUS_CONFIG:
             clean_p_name = unicodedata.normalize('NFC', str(p_name)).strip()
             style = utils.get_status_style(clean_p_name)
             panel_color = style.get('fill', '#888888')
        else:
            panel_color = utils.FALLBACK_COLORS[hash(p_name) % len(utils.FALLBACK_COLORS)]
        
        # Background Box (xref='x')
        GAP = 0.05
        fig.add_shape(type="rect", xref="x", yref="y",
                      x0=primary_x0, x1=primary_x1, 
                      y0=min_idx - 0.5 + GAP, y1=max_idx + 0.5 - GAP,
                      fillcolor=panel_color, line=dict(width=0), layer="above")
        
        # Text (Calculate center in time domain)
        center_date = primary_x0 + (primary_x1 - primary_x0) / 2
        
        # Dynamic Wrapping based on max pixel width
        wrapped_text = utils.wrap_text_by_pixels(p_name, max_px=primary_max_px)
        
        font_size = 13
        p_len = len(str(p_name))
        
        # Adaptive font size (Simplified because wrapping handles resizing)
        # if p_len > 40: font_size = 11
        
        fig.add_annotation(
            xref="x", yref="y",
            x=center_date, y=(min_idx + max_idx) / 2,
            text=f"<b>{wrapped_text}</b>", 
            showarrow=False,
            font=dict(size=font_size, color='white', family='Arial Black'),
            align="center",
            xanchor="center"
        )
        
        # Separator
        if min_idx > 0:
            # Existing panel separator (white gap for panel)
            fig.add_shape(type="line", xref="x", yref="y",
                          x0=primary_x0, x1=primary_x1, y0=min_idx - 0.5, y1=min_idx - 0.5,
                          line=dict(color="white", width=4), layer="above")
            
            # [Visual Improvement] Global Separator Line between Groups
            # Changed layer to 'above' to ensure it's not hidden by background
            # Made color darker for better visibility
            # Use xref='paper' to guarantee it spans the entire view width
            fig.add_shape(type="line", xref="paper", yref="y",
                          x0=0, x1=1, 
                          y0=min_idx - 0.5, y1=min_idx - 0.5,
                          line=dict(color="#333333", width=2, dash="solid"), 
                          layer="above")
    
    # 2-2. Secondary Panel Draw
    if secondary_col:
        secondary_groups = df_plot.groupby([primary_col, secondary_col], sort=False)
        
        for (p_val, s_val), group_data in secondary_groups:
            min_idx = group_data['row_idx'].min()
            max_idx = group_data['row_idx'].max()
            
            sec_color = '#E8E8E8'
            
            fig.add_shape(type="rect", xref="x", yref="y",
                          x0=sec_x0, x1=sec_x1, 
                          y0=min_idx - 0.49, y1=max_idx + 0.49,
                          fillcolor=sec_color, 
                          line=dict(width=1, color='#CCCCCC'), 
                          layer="above")
            
            center_sec_date = sec_x0 + (sec_x1 - sec_x0) / 2
            
            wrapped_sec_text = utils.wrap_text_by_pixels(s_val, max_px=secondary_max_px)
            sec_font_size = 11
            
            fig.add_annotation(
                xref="x", yref="y",
                x=center_sec_date, 
                y=(min_idx + max_idx) / 2,
                text=f"<b>{wrapped_sec_text}</b>", 
                showarrow=False,
                font=dict(size=sec_font_size, color='#333333', family='Arial'),
                align="center",
                xanchor="center"
            )
            
            if min_idx > 0:
                fig.add_shape(type="line", xref="x", yref="y",
                              x0=sec_x0, x1=sec_x1, 
                              y0=min_idx - 0.5, y1=min_idx - 0.5,
                              line=dict(color="#CCCCCC", width=1), layer="above")

    # [New Feature] Sub-Group Separator (Squad Separator when grouped by Status/etc)
    # If the primary column is NOT Squad, we still want to see separators between Squads.
    if primary_col != 'Squad':
        # Iterate through rows to find where Squad changes
        for i in range(1, len(df_plot)):
            # Check if Squad changed from previous row
            curr_squad = df_plot.iloc[i]['Squad']
            prev_squad = df_plot.iloc[i-1]['Squad']
            
            # Check if Primary Group also changed (we already have a line there from the main loop)
            # We only want to add *extra* lines if the primary group didn't change but the squad did.
            curr_primary = df_plot.iloc[i][primary_col]
            prev_primary = df_plot.iloc[i-1][primary_col]
            
            if curr_squad != prev_squad and curr_primary == prev_primary:
                 # Draw a separator
                 # We use a slightly different style (e.g. thinner/lighter) or same?
                 # User requested "separator", let's use a clear grey line.
                 fig.add_shape(type="line", xref="paper", yref="y",
                          x0=0, x1=1, 
                          y0=i - 0.5, y1=i - 0.5,
                          line=dict(color="#999999", width=1, dash="longdash"), # Distinct from main block
                          layer="below") # Below to not obscure text, but visible on background

    # [Important] Update Layout with explicit width and range


    # 3. Bar Chart Drawing Logic
    # Modified to support solid bars with internal text as requested

    # Separate traces for bars (with text) and simple markers
    
    annotations = []
    
    for idx, row in df_plot.iterrows():
        status = row['Status']
        style = utils.get_status_style(status)
        border_color = style['border']
        fill_color = style['fill']
        text_color = style.get('text_color', 'black') # Default to black if not set
        icon_display = style['icon']
        
        start_date = row['Start']
        end_date = row['End']
        task_text = row['Task']
        if icon_display:
            task_text = f"{icon_display} {task_text}"
            
        today_val = datetime.now()
        
        # Determine bar properties
        bar_base = None
        bar_x = None
        show_bar = False
        bar_opacity = 1.0
        
        # Case 1: Start X, End O (Start=Today)
        if pd.isna(start_date) and pd.notna(end_date):
            start_date = today_val
            if start_date > end_date: start_date = end_date
            bar_base = start_date
            bar_x = (max(0.5, (end_date - start_date).days) * 24 * 60 * 60 * 1000)
            show_bar = True
            
        # Case 2: Start X, End X (Only Marker)
        elif pd.isna(start_date) and pd.isna(end_date):
            fig.add_trace(go.Scatter(
                x=[today_val], y=[idx], mode='markers+text',
                marker=dict(symbol='line-ns-open', size=10, color=border_color, line=dict(width=2)),
                text=[f"<b>{task_text}</b>"],
                textposition="middle right",
                textfont=dict(size=12, color="black"),
                showlegend=False,
                hoverinfo='skip'
            ))
            continue # Done for this row
            
        # Case 3: Start O, End O (Normal)
        elif pd.notna(start_date) and pd.notna(end_date):
            bar_base = start_date
            bar_x = (max(0.5, (end_date - start_date).days) * 24 * 60 * 60 * 1000)
            show_bar = True
            
        # Case 4: Start O, End X (Ongoing infinite?)
        elif pd.notna(start_date) and pd.isnull(end_date):
            end_date = datetime.now()
            if start_date > end_date: 
                duration_days = 0 
            else:
                duration_days = (end_date - start_date).days
            
            bar_base = start_date
            bar_x = (duration_days * 24 * 60 * 60 * 1000)
            show_bar = True
            bar_opacity = 1.0 # Keep opaque text
            # task_text += " (진행중)" # Removed as per user request
        
        if show_bar:
            # 1. Main White Bar (Box)
            fig.add_trace(go.Bar(
                y=[idx],
                x=[bar_x],
                base=[bar_base],
                orientation='h',
                marker=dict(
                    color='white', 
                    line=dict(width=2, color='black') # Thick black border
                ),
                width=0.8, # Thicker bar for card look
                opacity=bar_opacity,
                showlegend=False,
                text=f"<b>{task_text}</b>",
                textposition='inside', 
                insidetextanchor='start', # Left align task name
                insidetextfont=dict(size=12, color='black', family="Arial"), # Black text
                textangle=0, # Force horizontal
                constraintext='none', # Allow overflow, don't rotate/shrink weirdly
                hovertemplate=(
                    f"<span style='font-size:14px; font-weight:bold;'>{row['Task']}</span><br><br>"
                    f"<b>Squad:</b> {row['Squad']}<br>"
                    f"<b>Status:</b> {status}<br>"
                    f"<b>Period:</b> {start_date.strftime('%Y-%m-%d') if pd.notna(start_date) else 'Unknown'} ~ "
                    f"{end_date.strftime('%Y-%m-%d') if pd.notna(end_date) else 'Ongoing'}<br>"
                    f"<b>Comment:</b> {utils.wrap_text_html(row['Comment'], 50)}<extra></extra>"
                ),
                hoverlabel=dict(bgcolor="white", font_size=13, font_family="Arial", align="left")
            ))
            
            # 2. Status Badge (Annotation)
            # Badge overlapping top-left border
            # y=idx is center. Bar width=0.8 means top edge is idx - 0.4
            
            annotations.append(dict(
                x=bar_base,
                y=idx - 0.4, # Top edge
                text=f"<b>{status}</b>",
                showarrow=False,
                xanchor='left',
                yanchor='middle', # Straddle the line
                xshift=0, 
                yshift=0,
                font=dict(color='white', size=10, family="Arial"),
                bgcolor=fill_color,
                bordercolor=fill_color,
                borderwidth=1,
                borderpad=2,
                opacity=1.0
            ))

    # 5. Today Line
    today = datetime.now()
    fig.add_shape(type="line", x0=today, x1=today, y0=-1, y1=len(df_plot),
                  line=dict(color="red", width=1.5, dash="dot"), layer="above")
    
    # Move Today label inside the plot (below the timeline axis) to avoid overlap with Date Labels
    fig.add_annotation(
        x=today, 
        y=1.0, 
        yref="paper", 
        text="<b>Today</b>", 
        showarrow=False,
        font=dict(size=11, color="red", family="Arial Black"),
        xanchor='center',
        yanchor='top', # Anchor to top
        yshift=-10 # Shift DOWN into the chart area
    )

    # Combine existing annotations with badge annotations
    existing_annotations = list(fig.layout.annotations) if fig.layout.annotations else []
    fig.layout.annotations = existing_annotations + annotations

    fig.update_layout(
        width=chart_width,  # Explicitly Set Width
        height=max(600, len(df_plot) * 40 + 100), 
        xaxis=dict(
            type='date', 
            tickformat='%Y-%m', 
            dtick="M3", 
            gridcolor='lightgray',
            side='top',
            # Fixed Range covering Panels + Data
            range=[axis_min_date, vis_max_date],
            tickfont=dict(size=12, family="Arial")
        ),
        yaxis=dict(
            showticklabels=False, 
            title="",
            range=[len(df_plot), -1], 
            autorange=False
        ),
        # Margin: Zero left margin because panels are inside the plot area now
        margin=dict(t=120, l=10, r=50, b=30), 
        hovermode='closest',
        plot_bgcolor='white',
        showlegend=True,
        uniformtext_minsize=12, 
        uniformtext_mode='show', 
    )

    # Legend Logic
    legend_status = ['진행 완료', '진행 중', '진행 예정', '보류/이슈', 'DROP', '단순 인입']
    for status in legend_status:
        style = utils.get_status_style(status)
        fill_color = style.get('fill', 'white')
        border_color = style.get('border', 'black')
        
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode='markers',
            marker=dict(symbol='square', size=15, color=fill_color, line=dict(width=1, color=border_color)),
            name=status
        ))
    
    # Use 'container' coordinates for stable positioning regardless of chart height
    fig.update_layout(legend=dict(
        orientation="h", 
        yanchor="top", y=1.0, 
        xanchor="left", x=0,
        yref="container"  # Fix to container top
    ))
    
    return fig

def render_roadmap(df_original):
    # Sidebar Filters
    with st.sidebar:
        st.header("📂 정렬 기준")
        
        # 1. Group By (Dynamic based on Excel columns)
        # Exclude system columns that shouldn't be grouped by
        system_cols = ['Task', 'Start', 'End', 'Comment', 'Display_Date', 'Duration_Text', 'Tick_Label', 'Duration', 'row_idx']
        
        # [User Request] Keep original column order from data
        group_options = [c for c in df_original.columns if c not in system_cols]
        
        # Ensure 'Squad' is present if implied (though it should be in df columns)
        if 'Squad' not in group_options and 'Squad' in df_original.columns:
            group_options.insert(0, 'Squad')
            
        # Default logic (Status or Squad)
        default_index = 0
        if 'Status' in group_options:
            default_index = group_options.index('Status')
        elif 'Squad' in group_options:
            default_index = group_options.index('Squad')
        
        selected_group_col = st.selectbox("정렬 기준 선택", group_options, index=default_index, label_visibility="collapsed")
        
        st.divider()
        
        st.header("🔍 검색 및 필터")

        # Search
        search_query = st.text_input("과제명 검색", "")
        
        # Squad Filter
        all_squads = list(df_original['Squad'].unique())
        if 'Squad' in df_original.columns:
            # Custom sorting for Squad list if needed, or rely on df order
            pass
            
        selected_squads = st.multiselect("Squad 선택", all_squads, default=all_squads)
        
        # Goal Filter
        all_goals = []
        if 'Goal' in df_original.columns:
            all_goals = sorted(df_original['Goal'].dropna().unique().tolist())
            
        selected_goals = st.multiselect("Goal 선택", all_goals, default=all_goals)
        

        
        # Filter Logic
        df_filtered = df_original.copy()
        
        if search_query:
            df_filtered = df_filtered[df_filtered['Task'].str.contains(search_query, case=False, na=False)]
            
        if selected_squads:
            df_filtered = df_filtered[df_filtered['Squad'].isin(selected_squads)]
            
        if selected_goals:
            df_filtered = df_filtered[df_filtered['Goal'].isin(selected_goals)]
            

        # Additional Filters from original code (Manager, Show Completed)
        # Assuming they are less critical or added if needed. Let's add Show Completed as it's common.
        show_completed = st.checkbox("진행 완료 포함", value=True)
        if not show_completed:
            df_filtered = df_filtered[df_filtered['Status'] != '진행 완료']
            
        st.divider()
        st.subheader("⚙️ 보기 설정")
        
        # 1. Group By (Moved to Top) -> Removed from here

        # 2. Status Filter (Moved to Sidebar)
        all_statuses = sorted(df_filtered['Status'].dropna().unique())
        selected_statuses = st.multiselect("상태 필터 (Status)", all_statuses, default=all_statuses)
        
        # Apply Status Filter
        if selected_statuses:
            df_chart = df_filtered[df_filtered['Status'].isin(selected_statuses)]
        else:
            df_chart = df_filtered
        
    # Main Area
    # Title handled in app.py
    # st.markdown("<h3 style='text-align: center; margin-bottom: 20px;'>📊 Project Roadmap</h3>", unsafe_allow_html=True)

    # Date Period Filter (Main Area)
    today = datetime.now().date()
    this_year_start = datetime(today.year, 1, 1).date()
    this_year_end = datetime(today.year, 12, 31).date()

    # Initialize Session State for Period Filter if not present
    # Initialize Session State for Period Filter if not present
    if 'roadmap_period_filter' not in st.session_state:
        st.session_state['roadmap_period_filter'] = () # Default to All (Empty)

    def reset_period_filter():
        st.session_state['roadmap_period_filter'] = ()

    # Layout: Input + Reset Button
    c_period_1, c_period_2 = st.columns([0.4, 0.6])
    
    with c_period_1:
         c_p_input, c_p_btn = st.columns([0.8, 0.2])
         with c_p_input:
             period_input = st.date_input(
                 "📅 기간 설정 (Start Date 기준)", 
                 key='roadmap_period_filter'
             )
         with c_p_btn:
             # Add spacer to align button with input
             st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
             st.button("🔄", help="기간 설정 초기화 (전체 보기)", on_click=reset_period_filter)
    
    # Apply Period Filter to df_chart if range is selected
    if isinstance(period_input, tuple) and len(period_input) == 2:
         start_p, end_p = period_input
         if start_p and end_p:
             df_chart = df_chart.dropna(subset=['Start'])
             mask_period = (df_chart['Start'].dt.date >= start_p) & (df_chart['Start'].dt.date <= end_p)
             df_chart = df_chart[mask_period]

    if df_chart.empty:
        st.warning("표시할 과제가 없습니다.")
        return

    # 2. Metrics Area (Dynamic based on df_chart)
    total_chart_count = len(df_chart)
    total_original_count = len(df_original)
    
    st.info(f"📋 현재 **{total_chart_count}개**의 과제가 표시 중입니다. (전체 {total_original_count}개 중)")
    
    status_counts = df_chart['Status'].value_counts()
    
    today_date = datetime.now()
    active_mask = (df_chart['Start'] <= today_date) & (
        (df_chart['End'] >= today_date) | pd.isna(df_chart['End'])
    )
    active_today_count = len(df_chart[active_mask])
    
    metrics_order = [
        ("표시 중인 과제", total_chart_count, "#333333"),
        ("🔥 오늘 진행중", active_today_count, "#FF4B4B"),
        ("진행 완료", status_counts.get('진행 완료', 0), utils.STATUS_CONFIG['진행 완료']['border']),
        ("진행 중", status_counts.get('진행 중', 0), utils.STATUS_CONFIG['진행 중']['border']),
        ("진행 예정", status_counts.get('진행 예정', 0), utils.STATUS_CONFIG['진행 예정']['border']),
        ("보류/이슈", status_counts.get('보류/이슈', 0), utils.STATUS_CONFIG['보류/이슈']['border']),
        ("단순 인입", status_counts.get('단순 인입', 0), utils.STATUS_CONFIG['단순 인입']['border']),
        ("DROP", status_counts.get('DROP', 0), utils.STATUS_CONFIG['DROP']['border']),
    ]
    
    st.markdown('''
    <style>
    .metric-box {
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    .metric-label {
        font-size: 12px;
        color: #666;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
    }
    </style>
    ''', unsafe_allow_html=True)
    
    m_cols = st.columns(len(metrics_order))
    for i, (label, value, color) in enumerate(metrics_order):
        with m_cols[i]:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="color: {color};">{value}</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.divider()

    # 3. Chart Area
    with st.spinner('차트를 생성 중입니다...'):
        fig = create_professional_gantt(df_chart, group_col=selected_group_col)
        
        plotly_config = {
            'scrollZoom': False, 
            'displayModeBar': True,
            'toImageButtonOptions': {
                'format': 'png', 
                'filename': 'project_roadmap',
                'height': None,
                'width': None,
                'scale': 3
            }
        }
        
        st.plotly_chart(fig, use_container_width=False, theme=None, config=plotly_config)
