import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List
import json

def create_confidence_chart(scores: Dict[str, float]) -> str:
    """Create a bar chart of confidence scores"""
    fig = go.Figure(data=[
        go.Bar(
            x=list(scores.keys()),
            y=list(scores.values()),
            marker_color='rgb(158, 71, 255)',
            text=[f"{v:.1f}%" for v in scores.values()],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Agent Confidence Scores",
        xaxis_title="Metric",
        yaxis_title="Confidence (%)",
        yaxis_range=[0, 100],
        template="plotly_dark"
    )
    
    return fig.to_html(include_plotlyjs='cdn')

def create_timeline_chart(events: List[Dict[str, Any]]) -> str:
    """Create a timeline of research events"""
    df = pd.DataFrame(events)
    
    fig = px.timeline(
        df,
        x_start="start",
        x_end="end",
        y="agent",
        color="agent",
        title="Research Timeline"
    )
    
    fig.update_layout(template="plotly_dark")
    
    return fig.to_html(include_plotlyjs='cdn')

def create_data_distribution(data: Dict[str, List[float]]) -> str:
    """Create distribution plots for data"""
    fig = go.Figure()
    
    for name, values in data.items():
        fig.add_trace(go.Box(
            y=values,
            name=name,
            boxmean='sd'
        ))
    
    fig.update_layout(
        title="Data Distributions",
        yaxis_title="Values",
        template="plotly_dark"
    )
    
    return fig.to_html(include_plotlyjs='cdn')