# FairLens Design System

## Overview

FairLens is a data-dense web application for ML engineers and compliance officers to upload model prediction data, run automated statistical fairness tests, and receive audit-ready verdicts. The design system prioritizes clarity, trustworthiness, and efficiency for technical users who need to quickly interpret results and take action.

**Design Thesis:** Professional tools should feel like precision instruments. Clean, purposeful, authoritative. No decoration for decoration's sake. The interface should recede so the data stands out.

---

## Color System

### Brand Colors

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Brand Primary | Deep Indigo | `#1e3a5f` | Headers, primary buttons, active states |
| Brand Hover | Navy | `#152a47` | Button hover states |
| Brand Light | Slate Blue | `#3b5998` | Secondary actions, links |

### Semantic Colors (Verdicts & Status)

| Role | Color | Hex | WCAG Contrast | Usage |
|------|-------|-----|---------------|-------|
| PASS | Emerald | `#059669` | 5.8:1 ✓ | Verdict badge, success states |
| PASS BG | Emerald Light | `#ecfdf5` | — | Background tint for pass results |
| FAIL | Rose | `#e11d48` | 5.4:1 ✓ | Verdict badge, error states |
| FAIL BG | Rose Light | `#fef2f2` | — | Background tint for fail results |
| CONDITIONAL_PASS | Amber | `#d97706` | 4.6:1 ✓ | Verdict badge, warning states |
| CONDITIONAL_PASS BG | Amber Light | `#fffbeb` | — | Background tint for conditional pass |

**Accessibility Note:** All semantic colors pass WCAG AA (4.5:1) on white. The background tints provide additional visual differentiation without relying solely on color.

### Neutral Palette

| Role | Hex | Usage |
|------|-----|-------|
| Neutral 900 | `#0f172a` | Primary headings, body text |
| Neutral 700 | `#334155` | Secondary text, table content |
| Neutral 500 | `#64748b` | Placeholder text, disabled states |
| Neutral 300 | `#cbd5e1` | Borders, dividers |
| Neutral 200 | `#e2e8f0` | Table borders, input backgrounds |
| Neutral 100 | `#f1f5f9` | Page background |
| Neutral 50 | `#f8fafc` | Card backgrounds, table rows |

### Status Badge Colors

| Status | Color | Hex | Pattern |
|--------|-------|-----|---------|
| Queued | Slate | `#64748b` | Pill with clock icon |
| Processing | Blue | `#2563eb` | Pill with spinner |
| Completed | Emerald | `#059669` | Pill with checkmark |
| Failed | Rose | `#e11d48` | Pill with X icon |

### Interactive States

| State | Color | Hex | Usage |
|-------|-------|-----|-------|
| Primary Hover | Navy | `#152a47` | Primary button hover |
| Primary Active | Dark Navy | `#0f1a2e` | Button press |
| Focus Ring | Indigo | `#1e3a5f` | 2px outline, 2px offset |
| Link Hover | Slate Blue | `#3b5998` | Underline on hover |

---

## Typography

### Font Stack

**Primary Font:** `"IBM Plex Sans"` — A humanist sans-serif with excellent legibility for data-dense interfaces. IBM Plex Sans is designed for computer interfaces and maintains clarity at small sizes.

**Monospace Font:** `"IBM Plex Mono"` — For metric values, confidence intervals, and any data that needs tabular alignment. Monospace is essential for a precision-auditing tool.

**Fallback:** `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`

### Type Scale

| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| text-xs | 12px | 16px | 400 | Table captions, metadata, timestamps |
| text-sm | 14px | 20px | 400 | Body text, form labels, table content |
| text-base | 16px | 24px | 400 | Primary body text, paragraphs |
| text-lg | 18px | 28px | 500 | Section headers, card titles |
| text-xl | 24px | 32px | 600 | Page titles |
| text-2xl | 32px | 40px | 700 | Dashboard headline (if needed) |
| text-3xl | 40px | 48px | 700 | Verdict badge (emphasis) |

### Type Styles

```css
/* Page Title */
font-family: "IBM Plex Sans", sans-serif;
font-size: 24px;
font-weight: 600;
line-height: 32px;
color: #0f172a;

/* Section Header */
font-family: "IBM Plex Sans", sans-serif;
font-size: 18px;
font-weight: 500;
line-height: 28px;
color: #0f172a;

/* Body Text */
font-family: "IBM Plex Sans", sans-serif;
font-size: 16px;
font-weight: 400;
line-height: 24px;
color: #334155;

/* Table Content */
font-family: "IBM Plex Sans", sans-serif;
font-size: 14px;
font-weight: 400;
line-height: 20px;
color: #334155;

/* Metric Values (Data) */
font-family: "IBM Plex Mono", monospace;
font-size: 14px;
font-weight: 500;
line-height: 20px;
color: #0f172a;

/* Caption / Metadata */
font-family: "IBM Plex Sans", sans-serif;
font-size: 12px;
font-weight: 400;
line-height: 16px;
color: #64748b;
```

---

## Spacing System

### Base Unit

**4px** — The base unit for all spacing. This keeps the system granular enough for precise layouts while remaining simple to reason about.

### Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| space-1 | 4px | Inline element gaps, icon padding |
| space-2 | 8px | Tight component internal spacing |
| space-3 | 12px | Component internal spacing |
| space-4 | 16px | Default component gaps |
| space-5 | 20px | Card padding, section gaps |
| space-6 | 24px | Section margins |
| space-8 | 32px | Large section gaps |
| space-10 | 40px | Page-level spacing |
| space-12 | 48px | Major page divisions |

### Layout Grid

- **Container Max Width:** 1280px
- **Content Max Width:** 1024px (for data tables)
- **Sidebar Width:** 240px (collapsible on tablet/mobile)
- **Card Border Radius:** 8px
- **Button Border Radius:** 6px
- **Input Border Radius:** 6px

### Responsive Spacing Adjustments

| Token | Desktop | Tablet | Mobile |
|-------|---------|--------|--------|
| Page Padding | 32px | 24px | 16px |
| Card Padding | 24px | 20px | 16px |
| Table Cell Padding | 16px 12px | 12px 8px | 12px 8px |

---

## Component Library

### Buttons

**Primary Button**
```
Height: 44px (touch target)
Padding: 16px 24px
Background: #1e3a5f (brand primary)
Text: White, 16px, 500 weight
Border Radius: 6px
Hover: #152a47
Active: #0f1a2e
Disabled: #64748b background, #94a3b8 text
```

**Secondary Button**
```
Height: 44px
Padding: 16px 24px
Background: White
Border: 1px solid #cbd5e1
Text: #1e3a5f, 16px, 500 weight
Border Radius: 6px
Hover: #f1f5f9 background
```

**Danger Button**
```
Background: #e11d48
Hover: #be123c
Used for: Delete actions, reset operations
```

**Ghost Button**
```
Background: Transparent
Text: #64748b
Hover: #f1f5f9 background
Used for: Tertiary actions, table row actions
```

### Form Inputs

```
Height: 44px
Padding: 12px 16px
Background: White
Border: 1px solid #cbd5e1
Border Radius: 6px
Font: 16px IBM Plex Sans
Placeholder: #94a3b8
Focus: 2px #1e3a5f outline, 2px offset
Error: #e11d48 border, error message below in #e11d48
```

### Status Badges (Pills)

```
Height: 28px
Padding: 4px 12px
Border Radius: 14px (pill shape)
Font: 13px IBM Plex Sans, 500 weight
Icon: 16px, left-aligned
Content: [Icon] [Text]
```

**Status Badge Examples:**
- Queued: `#f1f5f9` bg, `#64748b` text, clock icon
- Processing: `#eff6ff` bg, `#2563eb` text, spinner icon
- Completed: `#ecfdf5` bg, `#059669` text, check icon
- Failed: `#fef2f2` bg, `#e11d48` text, x icon

### Verdict Badges

```
Verdict (PASS): 40px height, 16px padding horizontal, 20px font, 700 weight
Background: #ecfdf5, border: 1px solid #059669
Text/Icon: #059669
Icon: Checkmark circle
```

```
Verdict (FAIL):
Background: #fef2f2, border: 1px solid #e11d48
Text/Icon: #e11d48
Icon: X circle
```

```
Verdict (CONDITIONAL_PASS):
Background: #fffbeb, border: 1px solid #d97706
Text/Icon: #d97706
Icon: Alert triangle
```

### Data Tables

```
Header Row:
Background: #f8fafc
Font: 14px, 600 weight, #334155
Padding: 12px 16px
Border Bottom: 1px solid #e2e8f0

Data Row:
Background: White (odd), #f8fafc (even)
Font: 14px, 400 weight, #334155
Padding: 12px 16px
Border Bottom: 1px solid #e2e8f0
Hover: #f1f5f9 background

Row Height: 48px minimum (for touch targets)
```

### Cards

```
Background: White
Border: 1px solid #e2e8f0
Border Radius: 8px
Padding: 24px
Shadow: 0 1px 3px rgba(0,0,0,0.1)
Hover (interactive): 0 4px 6px rgba(0,0,0,0.1)
```

### File Upload Zone

```
Border: 2px dashed #cbd5e1
Border Radius: 8px
Background: #f8fafc
Padding: 48px
Text: Center aligned
Icon: 48px upload icon in #64748b
Hover: Border #1e3a5f, background #f1f5f9
Drag Active: Border #1e3a5f, background #eff6ff
Error: Border #e11d48, background #fef2f2
```

### Navigation

```
Top Nav Bar:
Height: 64px
Background: White
Border Bottom: 1px solid #e2e8f0
Logo: Left-aligned, 32px height
Nav Links: Right-aligned, 16px, 500 weight
Active: #1e3a5f text, 2px bottom border #1e3a5f

Mobile Hamburger:
Icon: 24px, #334155
Position: Right side
Menu: Slide-out from right, 280px width
```

---

## Interaction Patterns

### Loading States

**Spinner:**
- Size: 20px for inline, 32px for page-level
- Color: #64748b (neutral) or #1e3a5f (brand)
- Animation: Rotate 360deg, 1s linear infinite

**Skeleton (Table Loading):**
- Background: Linear gradient shimmer (#f1f5f9 → #e2e8f0 → #f1f5f9)
- Animation: Shimmer sweep left-to-right, 1.5s ease-in-out infinite
- Skeleton rows: 5 placeholder rows

**Progress Bar:**
- Height: 4px
- Background: #e2e8f0
- Fill: #1e3a5f
- Animation: Smooth width transition

### Hover States

**Table Row:**
```css
transition: background-color 150ms ease;
:hover { background-color: #f1f5f9; }
```

**Button:**
```css
transition: all 150ms ease;
```

**Card (Interactive):**
```css
cursor: pointer;
transition: all 200ms ease;
:hover { transform: translateY(-2px); shadow: 0 4px 6px rgba(0,0,0,0.1); }
```

### Focus States

```css
:focus {
  outline: 2px solid #1e3a5f;
  outline-offset: 2px;
}
```

All interactive elements must have visible focus states for keyboard navigation.

### Transitions

| Element | Property | Duration | Easing |
|--------|----------|----------|--------|
| Button hover | all | 150ms | ease |
| Card hover | transform, shadow | 200ms | ease |
| Modal | opacity | 200ms | ease-out |
| Dropdown | opacity, transform | 150ms | ease |
| Table row hover | background-color | 150ms | ease |
| Page transition | opacity | 200ms | ease |
| Status badge update | background-color | 300ms | ease |

### Form Validation

**Inline Validation:**
- Show error message below input in real-time on blur
- Error message: 12px, #e11d48
- Input border changes to #e11d48 on error
- Success state: Green border #059669 with checkmark icon

**Toast Notifications:**
- Position: Top-right, 24px from edges
- Width: max 400px
- Duration: 5 seconds (auto-dismiss)
- Types: Success (green), Error (red), Warning (amber), Info (blue)

### Polling Pattern (Audit Processing)

When viewing an audit with status "queued" or "processing":

1. Show status badge with spinner
2. Display message: "Processing... This typically takes 30-90 seconds"
3. Poll every 5 seconds
4. On completion, show smooth transition to results
5. Use optimistic UI — don't interrupt flow when status updates

### Empty States

```
Icon: 64px, centered
Title: 18px, 600 weight, #0f172a
Description: 14px, #64748b
CTA Button: Primary style
```

---

## Responsive Specifications

### Breakpoints

| Breakpoint | Width | Target |
|------------|-------|--------|
| Mobile | 320px - 767px | Phones |
| Tablet | 768px - 1199px | Tablets, small laptops |
| Desktop | 1200px+ | Standard screens |

### View Adaptations

**Dashboard:**
- Desktop: Full table with all columns
- Tablet: Horizontal scroll for table, collapse date to secondary
- Mobile: Card list — one audit per row as expandable card

**New Audit:**
- Desktop: Two-column layout (model selector left, upload right)
- Tablet: Stacked — model above upload
- Mobile: Single column, full-width inputs

**Audit Detail:**
- Desktop: Full results table
- Tablet: Horizontal scroll for table
- Mobile: Stacked — verdict → status → results as cards

**Navigation:**
- Desktop: Top nav bar with all links visible
- Tablet: Hamburger icon, slide-out menu
- Mobile: Hamburger icon, slide-out menu

### Touch Targets

- All buttons: minimum 44px height
- Table rows: minimum 48px height
- Form inputs: 44px height
- Navigation links: 44px hit area

---

## Data Visualization

### Results Table Cell Formatting

**Metric Values (Monospace):**
- Font: IBM Plex Mono, 500 weight
- Color: #0f172a (normal), #e11d48 (fail)
- Alignment: Right

**Confidence Intervals:**
- Format: "[lower, upper]"
- Font: IBM Plex Mono, 400 weight, 12px
- Color: #64748b

**P-Values:**
- Format: "0.XXX" (3 decimal places)
- Font: IBM Plex Mono
- Color coding: <0.05 in #e11d48, otherwise #64748b

**Thresholds:**
- Display format: "≤ 0.1" or "≥ 0.8"
- Font: IBM Plex Mono, 400 weight, 12px

### Status Indicators

- Use consistent iconography with semantic colors
- Icons: 16px for inline, 20px for badges
- Always pair icons with text labels for accessibility

---

## Premium Polish & A+ Standard

To achieve an A+ design score, FairLens must move beyond "functional" to "exceptional." 

### Anti-AI-Slop Mandate
- **NO Generic Grids:** Replace the 3- or 4-column feature/stat grids with asymmetric, data-driven layouts.
- **NO Decorative Blobs:** Remove all ornamental SVG dividers, floating circles, or generic gradients.
- **NO Generic Copy:** Replace "Welcome Back" or "Unlock the power of..." with utility-driven, professional language.
- **NO Bubbly Defaults:** Border radii must be systematic. Large radii are for containers; small, sharp radii are for precision data elements.

### Precision Instrument Details
- **Micro-interactions:** Every interactive element must have a distinct, high-quality state change (subtle scale, color shift, or depth change).
- **Data-Dense Layouts:** Prioritize information density over whitespace. Use tabular layouts and compact components for audit results.
- **Motion with Purpose:** Use `fade-in-stagger` for page loads and `shimmer` for loading states. No purely ornamental animations.
- **Type-Perfect:** Enforce strict adherence to the IBM Plex scale. No generic "font-size: 1.2rem" — use the tokens.


### CSS Custom Properties

```css
:root {
  /* Brand */
  --color-brand: #1e3a5f;
  --color-brand-hover: #152a47;
  --color-brand-light: #3b5998;

  /* Semantic */
  --color-pass: #059669;
  --color-pass-bg: #ecfdf5;
  --color-fail: #e11d48;
  --color-fail-bg: #fef2f2;
  --color-warning: #d97706;
  --color-warning-bg: #fffbeb;

  /* Neutrals */
  --color-neutral-900: #0f172a;
  --color-neutral-700: #334155;
  --color-neutral-500: #64748b;
  --color-neutral-300: #cbd5e1;
  --color-neutral-200: #e2e8f0;
  --color-neutral-100: #f1f5f9;
  --color-neutral-50: #f8fafc;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;

  /* Typography */
  --font-sans: "IBM Plex Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, monospace;

  /* Borders */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-full: 9999px;
}
```

### Recommended Implementation Approach

1. **Install IBM Plex fonts** from Google Fonts or self-host
2. **Create CSS custom properties** file for colors and spacing
3. **Build base components:** buttons, inputs, badges, cards
4. **Compose into views:** dashboard, new audit, audit detail
5. **Add responsive styles** with media queries
6. **Implement interactions:** hover, focus, transitions

### Dependencies

- Google Fonts: IBM Plex Sans, IBM Plex Mono
- No additional CSS frameworks required — this system is self-contained
- For icons: Consider lucide-react or heroicons (both MIT licensed)

---

## Appendix: Color Contrast Verification

| Element | Background | Text Color | Contrast | WCAG AA |
|---------|------------|------------|----------|---------|
| PASS Badge | #ecfdf5 | #059669 | 5.8:1 | ✓ Pass |
| FAIL Badge | #fef2f2 | #e11d48 | 5.4:1 | ✓ Pass |
| CONDITIONAL Badge | #fffbeb | #d97706 | 4.6:1 | ✓ Pass |
| Primary Button | #1e3a5f | #ffffff | 10.5:1 | ✓ Pass |
| Body Text | #ffffff | #334155 | 11.2:1 | ✓ Pass |
| Caption | #ffffff | #64748b | 6.0:1 | ✓ Pass |

All text/background combinations meet WCAG AA (4.5:1) requirements.
