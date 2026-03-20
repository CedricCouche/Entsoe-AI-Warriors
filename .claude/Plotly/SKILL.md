# Plotly Python Visualization Skill

## Overview
This skill provides best practices for creating interactive visualizations using Plotly in Python. Plotly excels at creating publication-quality, interactive charts that work in Jupyter notebooks, web applications, and can be exported to static formats.

## When to Use This Skill
- Creating interactive data visualizations (scatter plots, line charts, bar charts, heatmaps, 3D plots)
- Building dashboards or web-based visualizations
- Generating plots that require user interaction (zooming, panning, hovering for details)
- Creating complex multi-panel figures or subplots
- Visualizing geographical data with maps
- Producing publication-ready charts with fine-grained control over appearance

## Core Principles

### 1. Choose the Right API
Plotly offers multiple APIs with different abstraction levels:

**Plotly Express (Recommended for most cases)**
- High-level, concise syntax
- Automatic styling and layout optimization
- Best for standard chart types
```python
import plotly.express as px
fig = px.scatter(df, x='column_x', y='column_y', color='category')
```

**Graph Objects (For advanced customization)**
- Low-level API with full control
- Required for complex layouts or custom chart types
```python
import plotly.graph_objects as go
fig = go.Figure(data=go.Scatter(x=x_data, y=y_data))
```

**Rule of thumb**: Start with Plotly Express, switch to Graph Objects only when you need features PE doesn't support.

### 2. Data Preparation
Plotly works best with clean, structured data:

```python
import pandas as pd
import plotly.express as px

# Prefer pandas DataFrames
df = pd.DataFrame({
    'date': dates,
    'value': values,
    'category': categories
})

# Plotly Express handles DataFrames naturally
fig = px.line(df, x='date', y='value', color='category')
```

### 3. Interactive Features
Leverage Plotly's interactivity:

```python
fig = px.scatter(df, x='x', y='y', 
                 hover_data=['additional_info'],  # Show on hover
                 title='Interactive Scatter Plot')

# Add range slider for time series
fig.update_xaxes(rangeslider_visible=True)

# Enable click events (for dash apps)
fig.update_traces(marker=dict(size=10), selector=dict(mode='markers'))
```

## Common Patterns

### Basic Chart Types

**Line Chart**
```python
import plotly.express as px

fig = px.line(df, x='date', y='value', 
              color='category',
              title='Time Series Analysis',
              labels={'value': 'Measurement (units)', 'date': 'Date'})
fig.show()
```

**Scatter Plot with Trendline**
```python
fig = px.scatter(df, x='x', y='y', 
                 trendline='ols',  # Ordinary least squares
                 trendline_color_override='red')
```

**Bar Chart**
```python
fig = px.bar(df, x='category', y='value',
             color='subcategory',
             barmode='group',  # or 'stack'
             text_auto=True)  # Show values on bars
```

**Histogram**
```python
fig = px.histogram(df, x='value', 
                   nbins=30,
                   marginal='box',  # Add box plot on margin
                   color='category')
```

### Subplots and Multiple Axes

```python
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Create 2x2 subplot grid
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Plot 1', 'Plot 2', 'Plot 3', 'Plot 4'),
    specs=[[{'type': 'scatter'}, {'type': 'bar'}],
           [{'type': 'scatter'}, {'type': 'scatter'}]]
)

# Add traces to specific subplots
fig.add_trace(go.Scatter(x=x1, y=y1, name='Series 1'), row=1, col=1)
fig.add_trace(go.Bar(x=x2, y=y2, name='Series 2'), row=1, col=2)

# Update layout
fig.update_layout(height=600, showlegend=True)
fig.show()
```

### Heatmaps and 2D Visualizations

```python
# Correlation heatmap
corr_matrix = df.corr()
fig = px.imshow(corr_matrix,
                text_auto=True,
                aspect='auto',
                color_continuous_scale='RdBu_r',
                title='Correlation Matrix')
```

### 3D Plots

```python
fig = px.scatter_3d(df, x='x', y='y', z='z',
                    color='category',
                    size='size_column',
                    hover_data=['info'])
fig.show()
```

## Customization Best Practices

### Layout Configuration
```python
fig.update_layout(
    title={
        'text': 'Main Title',
        'x': 0.5,  # Center title
        'xanchor': 'center'
    },
    xaxis_title='X Axis Label',
    yaxis_title='Y Axis Label',
    font=dict(family='Arial, sans-serif', size=12),
    plot_bgcolor='white',  # Background color
    hovermode='x unified',  # Unified hover for all traces
    legend=dict(
        orientation='h',  # Horizontal legend
        yanchor='bottom',
        y=1.02,
        xanchor='right',
        x=1
    )
)
```

### Axis Formatting
```python
fig.update_xaxes(
    showgrid=True,
    gridwidth=1,
    gridcolor='LightGray',
    tickformat='%Y-%m-%d',  # For dates
    dtick='M1'  # Monthly ticks
)

fig.update_yaxes(
    showgrid=True,
    tickprefix='$',  # Currency
    ticksuffix='K',  # Thousands
    type='log'  # Logarithmic scale
)
```

### Trace Styling
```python
fig.update_traces(
    line=dict(width=2, dash='dash'),
    marker=dict(size=8, opacity=0.7),
    textposition='top center'
)
```

## Advanced Techniques

### Custom Hover Templates
```python
fig = px.scatter(df, x='x', y='y')
fig.update_traces(
    hovertemplate='<b>%{fullData.name}</b><br>' +
                  'X: %{x:.2f}<br>' +
                  'Y: %{y:.2f}<br>' +
                  '<extra></extra>'  # Remove trace name from hover
)
```

### Animations
```python
fig = px.scatter(df, x='gdp', y='life_expectancy',
                 animation_frame='year',
                 animation_group='country',
                 size='population',
                 color='continent',
                 hover_name='country',
                 range_x=[0, 100000],
                 range_y=[25, 90])
```

### Geographic Maps
```python
# Choropleth map
fig = px.choropleth(df, 
                    locations='country_code',
                    color='value',
                    hover_name='country',
                    color_continuous_scale='Viridis')

# Scatter map
fig = px.scatter_geo(df,
                     lat='latitude',
                     lon='longitude',
                     size='magnitude',
                     projection='natural earth')
```

## Performance Optimization

### For Large Datasets
```python
# 1. Use WebGL for scatter plots with many points
fig = px.scatter(large_df, x='x', y='y', render_mode='webgl')

# 2. Sample data if interaction isn't critical
sampled_df = large_df.sample(n=10000)

# 3. Use aggregation for line charts
df_agg = df.groupby('date').agg({'value': 'mean'}).reset_index()

# 4. Disable hover for very dense plots
fig.update_traces(hoverinfo='skip')
```

## Export and Sharing

### Save to File
```python
# Static image (requires kaleido)
fig.write_image('figure.png', width=1200, height=800)
fig.write_image('figure.pdf')

# Interactive HTML
fig.write_html('figure.html')

# JSON for later use
fig.write_json('figure.json')
```

### Integration with Jupyter
```python
# Display inline (default)
fig.show()

# Use different renderers
import plotly.io as pio
pio.renderers.default = 'browser'  # Open in browser
pio.renderers.default = 'iframe'   # Jupyter iframe
```

## Common Pitfalls and Solutions

### Issue: Plot Not Displaying
```python
# Solution 1: Explicitly call show()
fig.show()

# Solution 2: Check renderer
import plotly.io as pio
print(pio.renderers)
pio.renderers.default = 'notebook'  # For Jupyter
```

### Issue: Memory Problems with Large Data
```python
# Solution: Use Datashader or aggregate data
# Or switch to plotly.graph_objects with scattergl
import plotly.graph_objects as go

fig = go.Figure(data=go.Scattergl(
    x=large_x_array,
    y=large_y_array,
    mode='markers'
))
```

### Issue: Slow Rendering
```python
# Solution: Reduce data points or use WebGL
fig = px.scatter(df, x='x', y='y', render_mode='webgl')

# Simplify hover templates
fig.update_traces(hovertemplate='%{y}')
```

## Color and Theme Management

### Using Built-in Themes
```python
import plotly.io as pio

# Available themes: plotly, plotly_white, plotly_dark, ggplot2, seaborn, etc.
pio.templates.default = 'plotly_white'

# Or per-figure
fig = px.scatter(df, x='x', y='y', template='plotly_dark')
```

### Custom Color Scales
```python
# Discrete colors
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
fig = px.bar(df, x='category', y='value', color='group',
             color_discrete_sequence=colors)

# Continuous scales
fig = px.scatter(df, x='x', y='y', color='value',
                 color_continuous_scale='Viridis')
```

## Integration with Other Libraries

### From Matplotlib
```python
import plotly.tools as tls
import matplotlib.pyplot as plt

# Create matplotlib figure
mpl_fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])

# Convert to plotly
plotly_fig = tls.mpl_to_plotly(mpl_fig)
plotly_fig.show()
```

### With Pandas
```python
# Pandas has built-in plotly backend
import pandas as pd
pd.options.plotting.backend = 'plotly'

# Now pandas plot methods use plotly
df.plot(x='date', y='value', kind='line')
```

## Checklist for High-Quality Plots

- [ ] Clear, descriptive title
- [ ] Axis labels with units
- [ ] Legend positioned appropriately
- [ ] Color scheme appropriate for data type (sequential/diverging/categorical)
- [ ] Hover information provides context
- [ ] Font sizes readable at target display size
- [ ] Data:ink ratio optimized (minimal chartjunk)
- [ ] Tested interactivity (zoom, pan, hover)
- [ ] Accessibility: color-blind friendly palette if appropriate

## Resources
- Official documentation: https://plotly.com/python/
- Plotly Express API: https://plotly.com/python/plotly-express/
- Graph Objects reference: https://plotly.com/python/reference/
- Community examples: https://plotly.com/python/

## Version Notes
This skill is written for Plotly 5.x. Major changes from 4.x include improved performance with WebGL and better Plotly Express integration.
