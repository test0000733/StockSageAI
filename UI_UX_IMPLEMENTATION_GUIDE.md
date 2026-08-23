# StockSageAI 2.0 - UI/UX Implementation Guide for Developers

**Version:** 2.0 | **Date:** August 23, 2026 | **Status:** ✅ Ready for Implementation

---

## Quick Start: Apply to Any Page

### Template: Enhanced Page Structure
```python
"""
Page Description - Enhanced UI/UX Version
"""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Page Title", layout="wide")

# 1. PAGE HEADER (Required)
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <h1 style='margin: 0.5rem 0;'>🎯 Page Title</h1>
    <p style='color: #cbd5e1; margin: 0.5rem 0; font-size: 0.95rem;'>
        Brief description of page purpose
    </p>
</div>
""", unsafe_allow_html=True)

# 2. AUTHENTICATION CHECK (if needed)
if "user" not in st.session_state or not st.session_state.user:
    st.warning("⚠️ Please log in to access this feature")
    st.stop()

# 3. SIDEBAR NAVIGATION (Optional)
with st.sidebar:
    st.markdown("### 🎯 Actions")
    action = st.radio(
        "Select",
        ["Option 1", "Option 2"],
        label_visibility="collapsed"
    )

# 4. MAIN CONTENT SECTIONS
# Use consistent divider pattern
st.markdown("### 📊 Section Title", divider="blue")
st.markdown("")  # Spacing

# Your content here with proper spacing

```

---

## Common Page Improvements

### ❌ BEFORE: Spacing Issues
```python
st.subheader("Holdings")
holdings = portfolio_mgr.get_holdings(portfolio_id)

if holdings.empty:
    st.info("No holdings")
    with st.form("add_holding"):
        col1, col2, col3 = st.columns(3)
        # Tight columns, unclear labels
```

### ✅ AFTER: Improved Spacing
```python
st.markdown("### 📊 Current Holdings", divider="blue")
st.markdown("")  # Add breathing room

holdings = portfolio_mgr.get_holdings(portfolio_id)

if holdings.empty:
    st.info("📊 No holdings yet. Add your first stock!")
    st.markdown("")  # Spacing between sections
    
    with st.form("add_holding"):
        col1, col2, col3 = st.columns(3, gap="medium")  # Define gap
        with col1:
            symbol = st.text_input("Stock Symbol", placeholder="e.g., AAPL")
        with col2:
            quantity = st.number_input("Quantity", value=10.0, min_value=0.1)
        with col3:
            price = st.number_input("Purchase Price", value=100.0, min_value=0.01)
        
        st.markdown("")  # Pre-button spacing
        
        if st.form_submit_button("✅ Add to Portfolio", use_container_width=True):
            # Process
```

---

## Widget-by-Widget Improvements

### Text Input
```python
# ❌ Before (No help, unclear)
symbol = st.text_input("Symbol")

# ✅ After (Clear, helpful)
symbol = st.text_input(
    "Stock Symbol",
    placeholder="e.g., AAPL",
    max_chars=10,
    help="Enter 1-10 character stock ticker symbol"
)
```

### Number Input
```python
# ❌ Before
quantity = st.number_input("Qty")

# ✅ After (Clear units, helpful)
quantity = st.number_input(
    "Number of Shares",
    value=10.0,
    min_value=0.1,
    step=0.1,
    help="Minimum 0.1 shares allowed"
)
```

### Button
```python
# ❌ Before (Generic, no visual)
st.button("Submit")

# ✅ After (Emoji, clear action, full width)
if st.button("✅ Add to Portfolio", use_container_width=True):
    # Process
```

### Selectbox
```python
# ❌ Before
model = st.selectbox("Model", models)

# ✅ After (Help text, clear options)
model = st.selectbox(
    "Select Model Architecture",
    AVAILABLE_MODELS,
    help="Choose the ML architecture to train"
)
```

### Metric Display
```python
# ❌ Before (No context)
st.metric("Value", "$1000")

# ✅ After (With help, in columns)
metric_cols = st.columns(4, gap="medium")
with metric_cols[0]:
    st.metric(
        "Total Value",
        "₹15,234.50",
        help="Current market value of all holdings"
    )
```

### Radio Selection
```python
# ❌ Before (With label)
action = st.radio("Action", ["View", "Add", "Analytics"])

# ✅ After (Sidebar with no label)
with st.sidebar:
    st.markdown("### 🎯 Actions")
    action = st.radio(
        "Select",
        ["View Portfolio", "Add Holding", "Analytics"],
        label_visibility="collapsed"
    )
```

---

## Spacing Rules (Golden Standards)

### Zero Spacing
```python
# Between: Closely related elements (form fields in same row)
col1, col2 = st.columns(2)
# No markdown("") between
```

### One Unit (1rem = 8px)
```python
# Between: Default elements, form groups
st.markdown("")  # Creates ~1rem space

# Usage:
field = st.text_input("Field")
st.markdown("")  # Space
button = st.button("Submit")
```

### Two Units (2rem = 16px)
```python
# Between: Major sections, dividers

st.markdown("### Section 1")
st.divider()
st.markdown("")
st.markdown("")  # Extra space after divider

# Or use:
st.markdown("---")  # Custom divider with spacing
```

### Three Units (3rem = 24px)
```python
# Between: Completely different sections, new pages

st.markdown("---")  # Section divider
st.markdown("")
st.markdown("")

st.markdown("### Next Major Section")
```

---

## Column Layout Guide

### 2-Column: Unequal (60/40)
```python
col_main, col_sidebar = st.columns([3, 2], gap="large")

with col_main:
    st.subheader("Main Content", divider="blue")
    # Most content here

with col_sidebar:
    st.subheader("Status", divider="green")
    # Summary/status info
```

### 2-Column: Equal (50/50)
```python
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown("### Left Section")
    # Form or content

with col2:
    st.markdown("### Right Section")
    # Form or content
```

### 3-Column: Equal
```python
col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    # Field 1
    symbol = st.text_input("Symbol")

with col2:
    # Field 2
    quantity = st.number_input("Qty")

with col3:
    # Field 3
    price = st.number_input("Price")
```

### 4-Column: Metrics
```python
metric_cols = st.columns(4, gap="medium")

for idx, (label, value) in enumerate([
    ("Total Value", "₹15,234"),
    ("Gain/Loss", "₹2,345"),
    ("Return %", "18.2%"),
    ("VaR 95%", "₹1,234")
]):
    with metric_cols[idx]:
        st.metric(label, value)
```

---

## Form Pattern (Standard)

```python
st.markdown("### ➕ Add New Item", divider="green")
st.markdown("")  # Spacing

with st.form("add_item_form"):
    # Main form fields
    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        field1 = st.text_input(
            "Field 1",
            placeholder="e.g., Value",
            help="Helper text"
        )
    
    with col2:
        field2 = st.number_input(
            "Field 2",
            value=10.0,
            help="Helper text"
        )
    
    st.markdown("")  # Pre-button spacing
    
    # Button row
    col_btn, col_info = st.columns([2, 3], gap="medium")
    
    with col_btn:
        if st.form_submit_button("✅ Submit", use_container_width=True):
            # Validate and process
            if field1:
                st.success(f"✅ Added successfully!")
                st.rerun()
            else:
                st.error("❌ Please fill all fields")
    
    with col_info:
        st.info("ℹ️ Helper text about the form")
```

---

## Status/Alert Pattern

```python
# Success - Action completed
st.success("✅ Dataset loaded: filename.csv")

# Warning - Requires attention
st.warning("⚠️ Please log in to access features")

# Error - Action failed
st.error("❌ Access Denied - Admin privileges required")

# Info - Helpful information
st.info("ℹ️ No custom dataset - using default data")

# Note: Each added ~1rem margin automatically
```

---

## Data Display Patterns

### Metrics Row
```python
st.markdown("**📈 Performance Metrics**")

metric_cols = st.columns(4, gap="medium")

metrics = [
    ("Total Value", "₹15,234.50"),
    ("Total Gain", "₹2,345.20"),
    ("Return %", "18.2%"),
    ("VaR (95%)", "₹1,200.00")
]

for idx, (label, value) in enumerate(metrics):
    with metric_cols[idx % 4]:
        st.metric(label, value)
```

### Table Display
```python
st.markdown("**📋 Holdings Table**")

# Prepare data
table_data = []
for item in items:
    table_data.append({
        'Column 1': item.field1,
        'Column 2': f"₹{item.field2:,.2f}",
        'Column 3': f"{item.field3:.2f}%"
    })

# Display
st.dataframe(
    pd.DataFrame(table_data),
    use_container_width=True,
    hide_index=True
)
```

### Chart Display
```python
st.markdown("**📈 Chart Title**")

col_info, col_chart = st.columns([1, 3], gap="large")

with col_info:
    st.markdown("**Summary Stats**")
    st.write(f"Total: 1,234")
    st.write(f"Average: 123")

with col_chart:
    fig = create_chart()
    st.plotly_chart(fig, use_container_width=True)
```

---

## Color Usage Guide

### Text Colors
```python
st.markdown("Primary text (default): No styling needed")

st.markdown("<small style='color: #cbd5e1;'>Secondary text (dimmed)</small>", 
            unsafe_allow_html=True)

st.markdown("<small style='color: #38bdf8;'>Highlighted/Link text</small>", 
            unsafe_allow_html=True)
```

### Background Boxes
```python
# Info box (blue background)
st.markdown("""
<div style='background: rgba(56, 189, 248, 0.05); 
    padding: 1rem; border-radius: 8px; 
    border-left: 4px solid #38bdf8;'>
    <strong>ℹ️ Information</strong>
    <p>Your message here</p>
</div>
""", unsafe_allow_html=True)

# Warning box (amber background)
st.markdown("""
<div style='background: rgba(245, 158, 11, 0.05); 
    padding: 1rem; border-radius: 8px; 
    border-left: 4px solid #f59e0b;'>
    <strong>⚠️ Warning</strong>
    <p>Your message here</p>
</div>
""", unsafe_allow_html=True)

# Success box (green background)
st.markdown("""
<div style='background: rgba(16, 185, 129, 0.05); 
    padding: 1rem; border-radius: 8px; 
    border-left: 4px solid #10b981;'>
    <strong>✅ Success</strong>
    <p>Your message here</p>
</div>
""", unsafe_allow_html=True)
```

---

## Accessibility Checklist

For each page, verify:
- [ ] All headings use proper hierarchy (H1, H2, H3)
- [ ] All inputs have labels and help text
- [ ] All buttons have descriptive text (not just "Click here")
- [ ] All images have alt text
- [ ] Color not the only way to convey information
- [ ] Text contrast meets WCAG AA standard
- [ ] Keyboard navigation works (no mouse-only features)
- [ ] Touch targets are 44×44px minimum
- [ ] Page headings match browser title

---

## Performance Tips

```python
# ✅ Good: Minimal reloads
if "data" not in st.session_state:
    st.session_state.data = load_expensive_data()

# ❌ Bad: Reloads every page render
data = load_expensive_data()

# ✅ Good: Cache expensive operations
@st.cache_data
def load_data():
    return read_csv("large_file.csv")

# ✅ Good: Use columns for layout (no nested containers)
col1, col2 = st.columns(2)

# ❌ Avoid: Deep nesting of containers
with st.container():
    with st.container():
        st.write("Too nested")
```

---

## Common Mistakes to Avoid

| ❌ Don't | ✅ Do | Why |
|---------|------|-----|
| `st.subheader("Text")` without divider | `st.markdown("### Text", divider="blue")` | Consistency |
| No spacing between elements | `st.markdown("")` between sections | Visual clarity |
| `st.columns(3)` without gap | `st.columns(3, gap="medium")` | Better spacing |
| Buttons without emojis | `st.button("✅ Action")` | Visual feedback |
| Links/buttons different widths | `use_container_width=True` on all | Alignment |
| No help text on inputs | Help text explaining purpose | Usability |
| Form fields with no spacing | `st.markdown("")` between groups | Organization |
| Generic labels | Specific, descriptive labels | Clarity |

---

## Testing Checklist Before Launch

```
Visual Testing:
☐ Page renders correctly on mobile (< 640px)
☐ Page renders correctly on tablet (640-1024px)
☐ Page renders correctly on desktop (> 1024px)
☐ No overlapping text or elements
☐ All buttons and inputs visible and clickable
☐ Proper spacing between elements

Functionality Testing:
☐ All forms submit correctly
☐ All buttons perform intended action
☐ All links work
☐ Error messages display properly
☐ Success messages display properly

Accessibility Testing:
☐ Page readable without colors (grayscale)
☐ Tab navigation works in order
☐ Screen reader compatible (basic test)
☐ Touch targets are 44×44px minimum
☐ Text contrast meets WCAG AA

Performance Testing:
☐ Page loads in < 2 seconds
☐ No unnecessary reruns
☐ Cache used for expensive operations
☐ No console errors or warnings
```

---

## Quick Reference: Common Patterns

### Pattern 1: Dashboard Header
```python
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <h1 style='margin: 0.5rem 0;'>📊 Dashboard Title</h1>
    <p style='color: #cbd5e1;'>Subtitle or description</p>
</div>
""", unsafe_allow_html=True)
```

### Pattern 2: Section with Status
```python
st.markdown("### 📊 Section Title", divider="blue")
st.markdown("")

col_main, col_status = st.columns([3, 1], gap="large")

with col_main:
    # Main content

with col_status:
    st.metric("Status", "Value")
```

### Pattern 3: Config + Results
```python
col_config, col_results = st.columns([1, 2], gap="large")

with col_config:
    st.markdown("#### ⚙️ Configuration")
    field1 = st.text_input("Field")
    if st.button("✅ Process"):
        st.session_state.results = process(field1)

with col_results:
    if st.session_state.get("results"):
        st.markdown("#### 📊 Results")
        st.write(st.session_state.results)
    else:
        st.info("Configure and process to see results")
```

---

**Version:** 2.0 | **Updated:** August 23, 2026 | **Status:** ✅ Ready to Use
