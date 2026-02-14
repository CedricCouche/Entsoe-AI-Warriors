# Graphic Chart Skill — 1970s Retro Theme

## Overview
This skill defines a 1970-1980 retro visual theme for Plotly charts and Streamlit dashboards. It provides a warm, earthy color palette inspired by the design aesthetics of the 1970s era: earth tones, bold lines, serif typography, and warm backgrounds.

## When to Use This Skill
- Applying a consistent retro/vintage visual identity to Plotly charts
- Styling Streamlit dashboards with a warm, earthy 1970s look
- Creating presentation-ready charts with a distinctive retro personality
- Any project where the visual theme should evoke the 1970s era

## When NOT to Use This Skill
- Charts requiring high-contrast accessibility-first palettes
- Dashboards targeting a modern/corporate/minimal aesthetic
- Scientific publications requiring standard color conventions

## Color Palette

| Name | Hex | Usage |
|------|-----|-------|
| Burnt Orange | `#CC5500` | Primary trace color |
| Avocado Green | `#568203` | Secondary trace color |
| Mustard Yellow | `#E1AD01` | Tertiary trace color |
| Harvest Gold | `#DA9100` | Quaternary trace color |
| Saddle Brown | `#8B4513` | Fifth trace color |
| Sienna | `#A0522D` | Sixth trace color |
| Dark Olive | `#556B2F` | Seventh trace color |
| Peru | `#CD853F` | Eighth trace color |
| Cream | `#FFF8DC` | Page background, paper background |
| Warm Parchment | `#F5E8C8` | Plot area background |
| Orange | `#CC7A2E` | Sidebar background |
| Navy Blue | `#1B2A4A` | Text, axis lines, legend border |

## Typography
- **Headings font:** Abril Fatface (Google Font) — inspired by Cooper Black, the quintessential 1970s display typeface
- **Body font:** EB Garamond (Google Font) — warm classic serif
- **Fallback stack:** `Georgia, 'Times New Roman', Times, serif`
- Title size: 18px
- Font loading: via `<link>` tag from Google Fonts (not `@import`)

## Plotly Template Definition

Register a custom Plotly template to apply the retro theme globally:

```python
import plotly.graph_objects as go
import plotly.io as pio

RETRO_COLORS = [
    "#CC5500",  # Burnt Orange
    "#568203",  # Avocado Green
    "#E1AD01",  # Mustard Yellow
    "#DA9100",  # Harvest Gold
    "#8B4513",  # Saddle Brown
    "#A0522D",  # Sienna
    "#556B2F",  # Dark Olive
    "#CD853F",  # Peru
]

RETRO_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        font=dict(family="'EB Garamond', Georgia, 'Times New Roman', serif", color="#1B2A4A"),
        title=dict(font=dict(size=18)),
        paper_bgcolor="#FFF8DC",
        plot_bgcolor="#F5E8C8",
        colorway=RETRO_COLORS,
        xaxis=dict(
            gridcolor="rgba(59,37,7,0.15)",
            linecolor="#1B2A4A",
            zerolinecolor="rgba(27,42,74,0.3)",
        ),
        yaxis=dict(
            gridcolor="rgba(59,37,7,0.15)",
            linecolor="#1B2A4A",
            zerolinecolor="rgba(27,42,74,0.3)",
        ),
        legend=dict(bgcolor="rgba(255,248,220,0.8)", bordercolor="#1B2A4A", borderwidth=1),
    ),
    data=dict(
        scatter=[go.Scatter(line=dict(width=2.5))],
        bar=[go.Bar(marker=dict(line=dict(width=0.5, color="#1B2A4A")))],
        pie=[go.Pie(marker=dict(line=dict(width=1, color="#FFF8DC")))],
    ),
)

# Register and activate
pio.templates["retro_70s"] = RETRO_TEMPLATE
pio.templates.default = "retro_70s"
```

**Important:** Pass `theme=None` to all `st.plotly_chart()` calls to prevent Streamlit's built-in theme from overriding backgrounds:

```python
st.plotly_chart(fig, width="stretch", theme=None)
```

## Streamlit Page Styling

Load Google Fonts via a `<link>` tag (more reliable than `@import` in Streamlit):

```python
import streamlit as st

st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Abril+Fatface&family=EB+Garamond:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">',
    unsafe_allow_html=True,
)
```

Apply matching CSS for background, sidebar, fonts, and chart containers:

```python
st.markdown("""
<style>
    .stApp {
        background-color: #FFF8DC;
        font-family: 'EB Garamond', Georgia, 'Times New Roman', serif;
    }
    [data-testid="stSidebar"] {
        background-color: #CC7A2E;
    }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp [data-testid="stHeading"] h1,
    .stApp [data-testid="stHeading"] h2,
    .stApp [data-testid="stHeading"] h3,
    .stApp [data-testid="stHeading"] h4,
    .stApp .stMarkdown h1, .stApp .stMarkdown h2,
    .stApp .stMarkdown h3, .stApp .stMarkdown h4 {
        font-family: 'Abril Fatface', Georgia, 'Times New Roman', serif !important;
        color: #1B2A4A;
    }
    .stApp p, .stApp span, .stApp label, .stApp .stCaption {
        font-family: 'EB Garamond', Georgia, 'Times New Roman', serif;
        color: #1B2A4A;
    }
    [data-testid="stMetricValue"] {
        color: #CC5500;
    }
    [data-testid="stMetricLabel"] {
        color: #1B2A4A;
    }
    /* Remove white frame around Plotly charts */
    .stPlotlyChart, [data-testid="stPlotlyChart"],
    .stPlotlyChart > div, [data-testid="stPlotlyChart"] > div,
    .stPlotlyChart iframe, [data-testid="stPlotlyChart"] iframe {
        background-color: transparent !important;
    }
    .js-plotly-plot .plotly .main-svg {
        background: transparent !important;
    }
</style>
""", unsafe_allow_html=True)
```

Use `st.markdown()` with inline style for the main title to guarantee Abril Fatface:

```python
st.markdown(
    '<h1 style="font-family: \'Abril Fatface\', Georgia, serif; color: #1B2A4A;">⚡ Title Here</h1>',
    unsafe_allow_html=True,
)
```

## Styling Rules
- **Line width:** 2.5px for all line traces (bold, retro feel)
- **Backgrounds:** Cream (`#FFF8DC`) for page and paper; warm parchment (`#F5E8C8`) for plot area
- **Grid:** Subtle dark brown at 15% opacity
- **Legend:** Semi-transparent cream with navy border
- **Bar outlines:** Thin navy stroke for definition
- **Pie slices:** Separated by cream-colored lines
- **Sidebar:** Rich orange (`#CC7A2E`)

## Integration
- The retro template is registered globally via `pio.templates.default`, so all Plotly Express and Graph Objects figures automatically inherit the theme
- Use `theme=None` on `st.plotly_chart()` to prevent Streamlit overriding Plotly colors
- Load fonts via `<link>` tag, not `@import`, for reliable rendering in Streamlit
