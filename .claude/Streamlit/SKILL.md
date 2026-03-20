# Streamlit Development Skill

## Overview
This skill provides guidance for building interactive data applications and dashboards using Streamlit. Use this skill when creating web apps for data visualization, machine learning demos, interactive reports, or rapid prototyping of Python-based tools.

## When to Use This Skill

**Trigger this skill when:**
- Building data dashboards or interactive visualizations
- Creating ML model demos or exploratory data analysis tools
- Developing rapid prototypes for Python applications
- Making data science work shareable and interactive
- Building internal tools or admin panels
- Creating interactive reports or presentations

**Do NOT use for:**
- Production-grade web applications requiring complex authentication
- High-performance applications with millions of users
- Applications requiring fine-grained control over frontend behavior
- Static websites or blogs
- Applications requiring custom CSS/JavaScript heavy lifting

## Core Principles

### 1. Script-Based Execution Model
Streamlit reruns the entire script top-to-bottom on every user interaction. Design your code with this in mind:
- Cache expensive operations
- Minimize redundant computations
- Use session state for persistence
- Structure code for efficient reruns

### 2. Widget-First Design
Every widget that captures input automatically triggers a rerun when changed. Design flows that leverage this:
- Place widgets logically in the user flow
- Use widget return values directly
- Avoid unnecessary form complexity

### 3. Progressive Disclosure
Show information progressively as users interact:
- Start with high-level views
- Reveal details on demand
- Use expanders and tabs for organization

## Best Practices

### Session State Management

Use `st.session_state` to persist data across reruns:

```python
# Initialize state
if 'counter' not in st.session_state:
    st.session_state.counter = 0

# Use state
st.session_state.counter += 1
st.write(f"Count: {st.session_state.counter}")

# Callbacks for complex logic
def increment():
    st.session_state.counter += 1

st.button("Increment", on_click=increment)
```

**Key patterns:**
- Initialize state variables at the top
- Use callbacks for updates that need to happen before rerun
- Store dataframes, models, and computed results in session state
- Avoid storing non-serializable objects (use `@st.cache_resource` instead)

### Caching Strategy

#### Data Loading: `@st.cache_data`
Use for data loading, transformations, and computations:

```python
@st.cache_data
def load_data(file_path):
    return pd.read_csv(file_path)

@st.cache_data
def expensive_computation(data):
    # This only runs when data changes
    return data.groupby('category').agg({'value': 'sum'})
```

**When to use:**
- Loading CSV, JSON, or database queries
- Data preprocessing and transformations
- API calls that return data
- Serializable computation results

#### Resource Management: `@st.cache_resource`
Use for global resources that shouldn't be duplicated:

```python
@st.cache_resource
def load_model():
    return torch.load('model.pth')

@st.cache_resource
def get_database_connection():
    return psycopg2.connect(...)
```

**When to use:**
- ML models
- Database connections
- Expensive initialization
- Non-serializable objects

### Layout and Organization

#### Columns for Side-by-Side Content
```python
col1, col2, col3 = st.columns([2, 1, 1])  # Proportional widths

with col1:
    st.header("Main Content")
    st.line_chart(data)

with col2:
    st.metric("Total", 1234, delta=56)

with col3:
    st.metric("Average", 45.6, delta=-2.3)
```

#### Tabs for Multiple Views
```python
tab1, tab2, tab3 = st.tabs(["Overview", "Details", "Settings"])

with tab1:
    st.write("Overview content")

with tab2:
    st.write("Detailed analysis")

with tab3:
    st.write("Configuration options")
```

#### Expanders for Optional Details
```python
with st.expander("Advanced Options"):
    threshold = st.slider("Threshold", 0.0, 1.0, 0.5)
    method = st.selectbox("Method", ["A", "B", "C"])
```

#### Sidebar for Controls
```python
with st.sidebar:
    st.header("Controls")
    date_range = st.date_input("Date Range", [])
    categories = st.multiselect("Categories", options)
    
    st.divider()
    
    if st.button("Reset"):
        st.session_state.clear()
```

### File Uploads and Downloads

#### File Upload
```python
uploaded_file = st.file_uploader("Choose a CSV file", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write(df)
    
    # Can also handle multiple files
    uploaded_files = st.file_uploader("Upload multiple files", 
                                      accept_multiple_files=True)
```

#### File Download
```python
# Download button for text/data
csv = df.to_csv(index=False)
st.download_button(
    label="Download CSV",
    data=csv,
    file_name='data.csv',
    mime='text/csv'
)

# For binary data (e.g., images, models)
with open('model.pkl', 'rb') as f:
    st.download_button(
        label="Download Model",
        data=f,
        file_name='model.pkl',
        mime='application/octet-stream'
    )
```

### Forms for Grouped Input

Use forms when you want to batch multiple inputs before triggering a rerun:

```python
with st.form("my_form"):
    name = st.text_input("Name")
    age = st.number_input("Age", min_value=0, max_value=120)
    submitted = st.form_submit_button("Submit")
    
    if submitted:
        st.write(f"Hello {name}, you are {age} years old")
```

**When to use forms:**
- Multiple related inputs that should be processed together
- Preventing premature computation while user is still entering data
- Submit actions like database inserts or API calls

### Data Display

#### DataFrames
```python
# Interactive dataframe with sorting/filtering
st.dataframe(df, use_container_width=True)

# Static table
st.table(df.head())

# Styled dataframe
st.dataframe(
    df.style.highlight_max(axis=0),
    use_container_width=True
)
```

#### Metrics
```python
col1, col2, col3 = st.columns(3)
col1.metric("Revenue", "$1.2M", "+15%")
col2.metric("Users", "45.2K", "+8%")
col3.metric("Churn", "2.3%", "-0.5%", delta_color="inverse")
```

### Visualizations

#### Native Charts (Simple and Fast)
```python
# Line chart
st.line_chart(df[['column1', 'column2']])

# Bar chart
st.bar_chart(df['category'].value_counts())

# Area chart
st.area_chart(df)

# Scatter plot
st.scatter_chart(df, x='age', y='income', color='category')
```

#### Matplotlib/Seaborn
```python
fig, ax = plt.subplots()
ax.hist(data, bins=30)
st.pyplot(fig)
```

#### Plotly (Interactive)
```python
fig = px.scatter(df, x='x', y='y', color='category', 
                 hover_data=['name'])
st.plotly_chart(fig, use_container_width=True)
```

#### Altair
```python
chart = alt.Chart(df).mark_bar().encode(
    x='category',
    y='count',
    color='segment'
)
st.altair_chart(chart, use_container_width=True)
```

### Status and Progress

#### Progress Bars
```python
progress_bar = st.progress(0)
for i in range(100):
    # Do work
    progress_bar.progress(i + 1)
```

#### Spinners
```python
with st.spinner('Loading data...'):
    time.sleep(2)
    data = load_data()
st.success('Data loaded!')
```

#### Status Messages
```python
st.success("Operation completed successfully!")
st.info("This is an informational message")
st.warning("This is a warning")
st.error("An error occurred")
```

### Navigation and Multi-Page Apps

Create a multi-page app with this structure:
```
your_app/
├── streamlit_app.py  # Home page
└── pages/
    ├── 1_📊_Dashboard.py
    ├── 2_⚙️_Settings.py
    └── 3_📈_Analysis.py
```

Navigation is automatic. Control with:
```python
# In streamlit_app.py
st.set_page_config(
    page_title="My App",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

Use `st.navigation` for custom navigation (newer approach):
```python
pages = {
    "Home": [
        st.Page("home.py", title="Home", icon="🏠"),
    ],
    "Tools": [
        st.Page("tool1.py", title="Dashboard", icon="📊"),
        st.Page("tool2.py", title="Analysis", icon="📈"),
    ]
}

pg = st.navigation(pages)
pg.run()
```

## Common Patterns

### Filter-Then-Display
```python
# Filters in sidebar
with st.sidebar:
    st.header("Filters")
    selected_category = st.selectbox("Category", df['category'].unique())
    date_range = st.date_input("Date Range", [])

# Filter data
filtered_df = df[df['category'] == selected_category]
if len(date_range) == 2:
    filtered_df = filtered_df[
        (filtered_df['date'] >= date_range[0]) &
        (filtered_df['date'] <= date_range[1])
    ]

# Display results
st.write(f"Showing {len(filtered_df)} records")
st.dataframe(filtered_df)
```

### Interactive ML Demo
```python
# Model loading (cached)
@st.cache_resource
def load_model():
    return joblib.load('model.pkl')

model = load_model()

# Input widgets
st.header("Make Prediction")
col1, col2 = st.columns(2)
with col1:
    feature1 = st.slider("Feature 1", 0.0, 10.0, 5.0)
    feature2 = st.slider("Feature 2", 0.0, 10.0, 5.0)

with col2:
    feature3 = st.selectbox("Feature 3", ['A', 'B', 'C'])
    feature4 = st.number_input("Feature 4", value=100)

# Predict
if st.button("Predict"):
    # Prepare input
    input_data = prepare_input(feature1, feature2, feature3, feature4)
    prediction = model.predict(input_data)
    
    # Display result
    st.success(f"Prediction: {prediction[0]:.2f}")
    
    # Visualize
    st.plotly_chart(create_feature_importance_chart(model))
```

### Data Upload and Analysis Pipeline
```python
st.title("Data Analysis Tool")

# Upload
uploaded_file = st.file_uploader("Upload your data", type=['csv', 'xlsx'])

if uploaded_file:
    # Load
    @st.cache_data
    def load_uploaded_data(file):
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    
    df = load_uploaded_data(uploaded_file)
    
    # Overview
    st.subheader("Data Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", len(df))
    col2.metric("Columns", len(df.columns))
    col3.metric("Memory", f"{df.memory_usage().sum() / 1024**2:.2f} MB")
    
    # Show data
    with st.expander("View Data"):
        st.dataframe(df)
    
    # Analysis options
    st.subheader("Analysis")
    analysis_type = st.selectbox("Choose analysis", 
                                  ["Summary Statistics", "Correlations", "Distribution"])
    
    if analysis_type == "Summary Statistics":
        st.write(df.describe())
    elif analysis_type == "Correlations":
        fig = px.imshow(df.corr(), text_auto=True)
        st.plotly_chart(fig)
    elif analysis_type == "Distribution":
        column = st.selectbox("Select column", df.columns)
        fig = px.histogram(df, x=column)
        st.plotly_chart(fig)
```

## Performance Optimization

### 1. Minimize Reruns
- Use callbacks for state updates that don't need immediate UI changes
- Group related widgets in forms
- Use fragments for isolated updates (Streamlit 1.33+)

### 2. Cache Aggressively
- Cache data loading and preprocessing
- Cache model initialization
- Cache expensive computations
- Use TTL for time-sensitive data: `@st.cache_data(ttl=3600)`

### 3. Lazy Loading
```python
# Don't compute everything upfront
if st.button("Show Analysis"):
    with st.spinner("Analyzing..."):
        result = expensive_analysis()
        st.write(result)
```

### 4. Optimize Data Display
- Use `st.dataframe()` instead of `st.table()` for large datasets
- Limit rows displayed by default
- Use pagination for very large datasets
- Consider data aggregation before display

### 5. Async Operations (Advanced)
```python
import asyncio

async def fetch_data_async(url):
    # Async data fetching
    pass

if st.button("Fetch Data"):
    data = asyncio.run(fetch_data_async(url))
    st.write(data)
```

## Configuration

### Page Config (Must be first Streamlit command)
```python
st.set_page_config(
    page_title="My App",
    page_icon="🚀",
    layout="wide",  # or "centered"
    initial_sidebar_state="expanded",  # or "collapsed"
    menu_items={
        'Get Help': 'https://docs.streamlit.io',
        'Report a bug': 'https://github.com/user/repo/issues',
        'About': 'This is my awesome app!'
    }
)
```

### Config File (.streamlit/config.toml)
```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
```

## Deployment Considerations

### Secrets Management
Create `.streamlit/secrets.toml`:
```toml
[database]
host = "localhost"
port = 5432
username = "admin"
password = "secure_password"

api_key = "your-api-key-here"
```

Access in code:
```python
import streamlit as st

db_host = st.secrets["database"]["host"]
api_key = st.secrets["api_key"]
```

### Requirements File
```txt
streamlit>=1.30.0
pandas>=2.0.0
plotly>=5.18.0
scikit-learn>=1.3.0
# Add all your dependencies
```

### Deployment Platforms
- **Streamlit Community Cloud**: Free, easy, GitHub-integrated
- **Docker**: Full control, any cloud provider
- **Hugging Face Spaces**: Good for ML demos
- **AWS/GCP/Azure**: Production deployments

## Common Pitfalls

### 1. Not Using Session State
**Problem:** Widgets reset on every interaction
**Solution:** Use `st.session_state` to persist values

### 2. Forgetting to Cache
**Problem:** App is slow, recomputes everything
**Solution:** Use `@st.cache_data` and `@st.cache_resource`

### 3. Mixing st.write with Returns
**Problem:** Confusion about when to use `st.write()` vs returning values
**Solution:** `st.write()` displays immediately; widget functions return values to use

### 4. Not Handling Empty States
**Problem:** Errors when no data is uploaded or selected
**Solution:** Always check if data exists before processing

### 5. Overusing st.experimental_rerun()
**Problem:** Infinite loops or janky UX
**Solution:** Usually unnecessary; rely on natural rerun behavior

### 6. Putting Expensive Code Outside Functions
**Problem:** Runs on every interaction even when not needed
**Solution:** Wrap in functions and cache or conditionally execute

## Testing Locally

Run your app:
```bash
streamlit run your_app.py
```

Options:
```bash
streamlit run app.py --server.port 8502
streamlit run app.py --server.headless true
streamlit run app.py --theme.base dark
```

## Resources

- **Documentation**: https://docs.streamlit.io
- **API Reference**: https://docs.streamlit.io/library/api-reference
- **Gallery**: https://streamlit.io/gallery
- **Forum**: https://discuss.streamlit.io
- **GitHub**: https://github.com/streamlit/streamlit

## Quick Reference

### Most Common Widgets
```python
# Text input
text = st.text_input("Label", value="default")
text_area = st.text_area("Label", height=200)

# Numbers
number = st.number_input("Label", min_value=0, max_value=100, value=50)
slider = st.slider("Label", 0, 100, 50)

# Selection
option = st.selectbox("Label", ["A", "B", "C"])
options = st.multiselect("Label", ["A", "B", "C"])
radio = st.radio("Label", ["A", "B", "C"])
checkbox = st.checkbox("Label", value=True)

# Dates
date = st.date_input("Label")
time = st.time_input("Label")

# Buttons
if st.button("Click me"):
    st.write("Button clicked!")

# File operations
file = st.file_uploader("Upload", type=['csv'])
st.download_button("Download", data, "file.csv")

# Layout
col1, col2 = st.columns(2)
with st.sidebar:
    st.write("Sidebar content")
with st.expander("More"):
    st.write("Hidden content")
tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])
```

## Summary

Streamlit excels at rapid development of data-focused applications. Remember:
- Cache expensive operations
- Use session state for persistence  
- Design for the rerun model
- Start simple, add complexity as needed
- Leverage built-in components before custom solutions
- Test with realistic data volumes early

The key to great Streamlit apps is understanding the rerun model and designing your data flow accordingly.
