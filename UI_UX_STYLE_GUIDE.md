# StockSageAI 2.0 - Complete UI/UX Style Guide

**Version:** 2.0 Production Ready | **Date:** August 23, 2026 | **Status:** ✅ Finalized

---

## Table of Contents
1. [Design Philosophy](#design-philosophy)
2. [Color Palette](#color-palette)
3. [Typography](#typography)
4. [Layout & Spacing](#layout--spacing)
5. [Component Library](#component-library)
6. [Page Patterns](#page-patterns)
7. [Responsive Design](#responsive-design)
8. [Accessibility](#accessibility)

---

## Design Philosophy

### Core Principles
- **Progressive Disclosure**: Show only what users need immediately
- **Consistent Spacing**: Use 8px or 16px grid system throughout
- **Visual Hierarchy**: Clear distinction between primary, secondary, tertiary content
- **Accessibility First**: WCAG 2.1 AA compliance minimum
- **Performance**: Optimize for mobile-first, then enhance for desktop
- **Real Data Visualization**: Show actual metrics, not dummy data

---

## Color Palette

### Primary Colors
```
Primary Blue:       #38bdf8 (Sky Blue)
Primary Dark:       #0369a1 (Navy Blue)
Primary Light:      #e0f2fe (Light Sky)

Usage:
- Primary buttons
- Active states
- Links
- Key metrics/highlights
- Primary dividers
```

### Semantic Colors
```
Success Green:      #10b981 (Emerald)
Success Light:      #d1fae5 (Light Green)

Warning Yellow:     #f59e0b (Amber)
Warning Light:      #fef3c7 (Light Yellow)

Danger Red:         #ef4444 (Red)
Danger Light:       #fee2e2 (Light Red)

Info Blue:          #3b82f6 (Bright Blue)
Info Light:         #dbeafe (Light Blue)
```

### Neutral Colors
```
Background Dark:    #0f172a (Slate Dark)
Background Darker:  #030712 (Almost Black)
Background Light:   #1e293b (Slate)

Text Primary:       #e2e8f0 (Light Slate)
Text Secondary:     #cbd5e1 (Medium Slate)
Text Muted:         #94a3b8 (Dark Slate)

Border:             rgba(96, 165, 250, 0.18) (Transparent Blue)
```

### Gradients
```
Success Gradient:   linear-gradient(135deg, #10b981, #059669)
Warning Gradient:   linear-gradient(135deg, #f59e0b, #d97706)
Danger Gradient:    linear-gradient(135deg, #ef4444, #dc2626)
Primary Gradient:   linear-gradient(135deg, #38bdf8, #0284c7)

Metric Gradient:    linear-gradient(135deg, rgba(56,189,248,0.1), rgba(168,85,247,0.05))
Card Gradient:      linear-gradient(135deg, rgba(30,41,59,0.8), rgba(15,23,42,0.6))
```

---

## Typography

### Font Stack
```css
Font Family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 
             'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
```

### Heading Styles

**H1 - Page Title**
```
Font Size: clamp(1.5rem, 5vw, 2.8rem) [24-44px desktop]
Line Height: 1.2
Font Weight: 700
Margin: 0.5rem 0
Color: #e2e8f0
Example: "💼 Portfolio Management System"
```

**H2 - Major Section**
```
Font Size: clamp(1.3rem, 4vw, 2.2rem) [20-35px desktop]
Line Height: 1.3
Font Weight: 600
Margin: 1rem 0 0.5rem 0
Color: #e2e8f0
Example: "📊 Current Holdings"
```

**H3 - Subsection**
```
Font Size: clamp(1.1rem, 3vw, 1.8rem) [18-28px desktop]
Line Height: 1.4
Font Weight: 600
Margin: 0.75rem 0 0.25rem 0
Color: #cbd5e1
Example: "Performance Metrics"
```

### Body Text
```
Standard Text:
- Font Size: clamp(0.9rem, 2vw, 1rem) [14-16px]
- Line Height: 1.6
- Color: #e2e8f0
- Margin: 0.5rem 0

Small Text:
- Font Size: clamp(0.75rem, 1.5vw, 0.875rem) [12-14px]
- Color: #cbd5e1
- Use for: Helper text, labels, timestamps
```

### Labels & Inputs
```
Label Text:
- Font Size: 0.9rem
- Font Weight: 500
- Color: #e2e8f0
- Margin Bottom: 0.5rem

Input Placeholder:
- Color: #64748b (Darker slate)
- Italic: No
```

---

## Layout & Spacing

### Grid System (8px base)
```
Spacing Scale:
0.25rem (2px)   - Minimal
0.5rem (4px)    - Extra tight
1rem (8px)      - Tight
1.5rem (12px)   - Standard
2rem (16px)     - Medium
2.5rem (20px)   - Large
3rem (24px)     - Extra large
4rem (32px)     - Huge

Usage:
- 1rem: Default between elements
- 2rem: Between major sections
- 1.5rem: Between form groups
```

### Padding
```
Container Padding:
- Mobile (< 640px):     1rem (16px)
- Tablet (640-1024px):  1.5rem (24px)
- Desktop (> 1024px):   2rem (32px)

Card Padding:
- Mobile:     1rem
- Desktop:    1.5rem

Button Padding:
- Vertical:   0.75rem
- Horizontal: 1.5rem
- Min Height: 44px (touch-friendly)
```

### Gaps
```
Column Gaps:
- Default:  gap="medium" (1rem)
- Compact:  gap="small" (0.5rem)
- Spacious: gap="large" (2rem)

Common Layouts:
- col1, col2 = st.columns(2, gap="medium")
- col1, col2, col3 = st.columns(3, gap="medium")
```

### Vertical Spacing
```
Between Sections:
- Use: st.markdown("")     (adds 1rem)
- Use: st.divider()      (full-width line)
- Better: st.markdown("---") (custom styling)

Header Spacing:
- Title to content: 2rem
- Between titles: 1rem
- Title to divider: 1rem

Post-divider spacing: 1rem
```

---

## Component Library

### Buttons

**Primary Button**
```python
st.button(
    "🚀 START TRAINING",
    key='unique_key',
    use_container_width=True,
    help="Descriptive tooltip"
)

Styling:
- Background: #38bdf8
- Color: #0f172a
- Border Radius: 8px
- Padding: 0.75rem 1.5rem
- Min Height: 44px
- Hover: Box shadow + slight transform
```

**Success Button**
```python
st.button(
    "✅ Add to Portfolio",
    key='unique_key',
    use_container_width=True
)

Styling:
- Background: #10b981
- Color: White
```

**Danger Button**
```python
st.button(
    "❌ Delete",
    key='unique_key'
)

Styling:
- Background: #ef4444
- Color: White
```

### Forms

**Text Input**
```python
symbol = st.text_input(
    "Stock Symbol",
    placeholder="e.g., AAPL",
    max_chars=10,
    help="Enter stock ticker symbol"
)

Styling:
- Background: rgba(15, 23, 42, 0.6)
- Border: 1px solid var(--border-color)
- Border Radius: 8px
- Padding: 0.75rem 1rem
- Focus Border: #38bdf8
- Font: 0.9rem (preventing iOS zoom)
```

**Number Input**
```python
quantity = st.number_input(
    "Number of Shares",
    value=10.0,
    min_value=0.1,
    step=0.1
)

Styling: (Same as text input)
```

**Selectbox**
```python
model = st.selectbox(
    "Select Model Architecture",
    AVAILABLE_MODELS,
    help="Choose the ML architecture"
)

Styling:
- Same as text input
- Dropdown arrow: #38bdf8
```

**Checkbox**
```python
tune = st.checkbox(
    "🔄 Enable Hyperparameter Tuning",
    value=False,
    help="Adds 20-30 min..."
)

Styling:
- Checkbox: #38bdf8 when checked
- Label: #e2e8f0
- Hover: Background highlight
```

### Cards/Boxes

**Standard Card**
```python
st.markdown("""
<div style='background: rgba(30, 41, 59, 0.8); 
    border: 1px solid rgba(96, 165, 250, 0.18);
    border-radius: 12px;
    padding: 1.5rem;
    backdrop-filter: blur(10px);'>
    <!-- Content -->
</div>
""", unsafe_allow_html=True)

Properties:
- Background: Slightly transparent
- Border: Thin blue line
- Border Radius: 12px
- Padding: 1.5rem
- Backdrop Filter: Blur effect
- Hover: Border color changes to #38bdf8
```

**Metric Card**
```python
st.markdown("""
<div class="metric-card">
    <div class="metric-label">Total Value</div>
    <div class="metric-value">₹15,234.50</div>
</div>
""", unsafe_allow_html=True)

Properties:
- Background: Gradient linear
- Border: 1px solid rgba(56, 189, 248, 0.2)
- Border Radius: 12px
- Padding: 1.5rem
- Text Align: Center
```

### Tables

**Standard Table**
```python
st.dataframe(
    pd.DataFrame(holdings_data),
    use_container_width=True,
    hide_index=True
)

Styling:
- Header: rgba(56, 189, 248, 0.1) background
- Row Alternate: Optional striped
- Borders: 1px solid var(--border-color)
- Text Size: 0.9rem
- Padding: 0.75rem
```

### Dividers

**Default Divider**
```python
st.divider()      # Streamlit default

Properties:
- Full width
- Color: var(--border-color)
- Margin: 1rem top/bottom
```

**Custom Divider**
```python
st.markdown("---")  # Markdown divider

Properties:
- Full width
- Color: var(--border-color)
- Styling: Can be customized with CSS
```

**Divider with Label (Section Header)**
```python
st.subheader("📊 Current Holdings", divider="blue")

Properties:
- Text and divider combined
- Divider color: blue
- Padding: Auto-spaced
```

### Status Indicators

**Success Alert**
```python
st.success("✅ Dataset loaded: filename.csv")
```

**Warning Alert**
```python
st.warning("⚠️ Please log in to access features")
```

**Error Alert**
```python
st.error("❌ Access Denied - Admin privileges required")
```

**Info Alert**
```python
st.info("ℹ️ No custom dataset - will use default data")
```

---

## Page Patterns

### Page Header Pattern
```python
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <h1 style='margin: 0.5rem 0;'>💼 Portfolio Management System</h1>
    <p style='color: #cbd5e1; margin: 0.5rem 0; font-size: 0.95rem;'>
        Track and manage your stock portfolio with real-time P&L
    </p>
</div>
""", unsafe_allow_html=True)
```

### Section Header Pattern
```python
st.subheader("📊 Current Holdings", divider="blue")

Or:

st.markdown("### 📊 Current Holdings", divider="blue")
```

### Metric Display Pattern
```python
metric_cols = st.columns(4, gap="medium")

with metric_cols[0]:
    st.metric(
        "Total Value",
        "₹15,234.50",
        help="Current market value"
    )
```

### Form Pattern
```python
with st.form("form_key"):
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        field1 = st.text_input("Field 1")
    with col2:
        field2 = st.number_input("Field 2")
    
    st.markdown("")  # Spacing
    
    if st.form_submit_button("✅ Submit", use_container_width=True):
        # Process
```

### Two-Column Main Layout Pattern
```python
col_main, col_sidebar = st.columns([3, 2], gap="large")

with col_main:
    st.subheader("Main Content", divider="blue")
    # Main content here

with col_sidebar:
    st.subheader("Sidebar Info", divider="green")
    # Info/status here
```

---

## Responsive Design

### Breakpoints
```
Mobile:   < 640px  (1 column)
Tablet:   640-1024px (2 columns, select 3-column)
Desktop:  > 1024px (3-4 columns, full width)
Extra:    > 1440px (4+ columns)
```

### Responsive Column Patterns
```python
# Adaptive 2-column
col1, col2 = st.columns([3, 2], gap="large")  # 60/40 split

# Adaptive 3-column
col1, col2, col3 = st.columns(3, gap="medium")  # Equal

# Adaptive 4-column (metrics)
metric_cols = st.columns(4, gap="medium")

# Each adapts automatically to screen size
```

### Mobile-First Text Sizing
```css
H1: clamp(1.5rem, 5vw, 2.8rem)
    /* Min 24px, preferred 5% viewport, max 44px */

H2: clamp(1.3rem, 4vw, 2.2rem)
    /* Min 20px, preferred 4% viewport, max 35px */

Body: clamp(0.9rem, 2vw, 1rem)
    /* Min 14px, preferred 2% viewport, max 16px */
```

### Touch-Friendly Sizing
```
Minimum Touch Target: 44px × 44px
Button Min Height: 44px
Input Min Height: 44px
Button Padding: 0.75rem vertical

Spacing between interactive elements: ≥ 8px
Avoid: Hover-only interactions on mobile
```

---

## Accessibility

### Color Contrast
```
AAA Standard (target):
- Normal text: 7:1 ratio minimum
- Large text: 4.5:1 ratio minimum
- Graphical elements: 3:1 ratio

Current palette:
- #e2e8f0 on #0f172a: 15.1:1 ✅
- #38bdf8 on #0f172a: 5.2:1 ✅
- #10b981 on #0f172a: 7.4:1 ✅
```

### Keyboard Navigation
```
Tab Order: Natural reading order
Focus Visible: Clear blue border
Skip Links: Available (internal)
Form Navigation: Logical flow
```

### ARIA Labels
```python
st.button(
    "Start",
    help="Start training new model"  # Adds aria-label equivalent
)

st.text_input(
    "Stock Symbol",
    help="Enter stock ticker (e.g., AAPL)"  # Helper text
)
```

### Icons & Emojis
```
✅  Success
❌  Error
⚠️   Warning
ℹ️   Information
📊  Stats/Charts
💼  Portfolio
🚀  Launch/Action
⚙️  Settings
🔐  Security
📈  Growth
📉  Decline
```

---

## Implementation Checklist

- [ ] All page headers follow header pattern
- [ ] All sections use `subheader(..., divider="blue")`
- [ ] All forms wrapped in `st.form()`
- [ ] All buttons use emojis and clear labels
- [ ] All columns use `gap="medium"` or `gap="large"`
- [ ] All inputs have help text
- [ ] All metrics in columns with `gap="medium"`
- [ ] No text boxes without padding
- [ ] No mismatched link/button widths (use `use_container_width=True`)
- [ ] Color palette used consistently
- [ ] Touch targets minimum 44×44px
- [ ] Text contrast meets WCAG AA
- [ ] Mobile responsiveness tested

---

**Last Updated:** August 23, 2026 | **Version:** 2.0 | **Status:** ✅ Production Ready
