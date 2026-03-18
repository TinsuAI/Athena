# UI/UX Design Guideline

**Purpose:** Reusable, project-agnostic design system and UX pattern reference.
**Origin:** Extracted and generalized from the Athena project (2026).
**Stack:** Next.js (React 19+), Tailwind CSS v4, shadcn/ui, TypeScript.

---

## 1. Design Philosophy

### Core Principles

1. **Speed over features** — Every design decision optimizes for time-to-value. If an interaction takes more than 2 clicks, question it.
2. **Progressive disclosure** — Show essential info first, details on demand. Dense doesn't mean cluttered.
3. **Keyboard-first, mouse-friendly** — Power users fly with shortcuts; casual users stay comfortable with mouse/touch.
4. **Confidence through clarity** — Clear visual hierarchy, predictable behavior, honest feedback. Never leave the user guessing.
5. **No dead ends** — Every error, empty state, and edge case offers a clear next step.
6. **Celebrate quietly** — No confetti. Smooth flow to the next task is the reward.

### Emotional Design Goals

| Emotion | Design Implication |
|---------|-------------------|
| **Confident** | Clear feedback, validated actions, trustworthy data display |
| **Efficient** | Sub-second interactions, minimal clicks, keyboard shortcuts |
| **In control** | Predictable behavior, undo-friendly actions, no surprise modals |
| **Informed** | Transparent states (loading, error, empty), honest messaging |

### Anti-Patterns to Avoid

| Anti-Pattern | Why | Alternative |
|--------------|-----|-------------|
| Pagination for primary lists | Breaks flow, hides results | Load more / infinite scroll |
| Modal confirmations for frequent actions | Slows high-volume workflow | Inline actions with undo |
| Complex filters upfront | Cognitive overload | Progressive filter reveal |
| Auto-playing tutorials | Interrupts expert users | Help on demand |
| Skeleton loaders everywhere | Creates anxiety | Optimistic UI where possible |
| Status enums for loading | Adds complexity | Boolean flags (`isLoading`, `isError`) |

---

## 2. Color System

### Token Architecture

Colors are defined as CSS custom properties in `globals.css` using Tailwind v4's `@theme` directive. Every project forks these tokens and customizes.

**Principle:** Use semantic tokens (`--primary`, `--destructive`), never raw hex values in components.

### Light Theme Tokens

| Token | Role | Reference Value |
|-------|------|-----------------|
| `--background` | Page background | slate-100 `#f1f5f9` |
| `--foreground` | Primary text | slate-900 `#0f172a` |
| `--card` | Card/surface background | white `#ffffff` |
| `--card-foreground` | Text on cards | slate-900 `#0f172a` |
| `--primary` | Primary actions, focus, brand | emerald-600 `#059669` |
| `--primary-foreground` | Text on primary | white `#ffffff` |
| `--secondary` | Secondary surfaces | slate-100 `#f1f5f9` |
| `--secondary-foreground` | Text on secondary | slate-900 `#0f172a` |
| `--muted` | Subtle backgrounds | slate-50 `#f8fafc` |
| `--muted-foreground` | De-emphasized text | slate-500 `#64748b` |
| `--accent` | Highlight/hover backgrounds | emerald-50 `#ecfdf5` |
| `--accent-foreground` | Text on accent | emerald-700 `#047857` |
| `--destructive` | Error/danger actions | red-500 `#ef4444` |
| `--border` | Borders, dividers | slate-200 `#e2e8f0` |
| `--input` | Input borders | slate-200 `#e2e8f0` |
| `--ring` | Focus rings | emerald-600 `#059669` |

### Dark Theme Tokens

| Token | Role | Reference Value |
|-------|------|-----------------|
| `--background` | Page background | slate-900 `#0f172a` |
| `--foreground` | Primary text | slate-50 `#f8fafc` |
| `--card` | Card surface | slate-800 `#1e293b` |
| `--primary` | Primary actions | emerald-500 `#10b981` |
| `--border` | Borders | `rgba(255,255,255,0.1)` |

### Semantic Status Colors

Use these for contextual meaning — never for decoration.

| Purpose | Color | Hex | Usage |
|---------|-------|-----|-------|
| Success / High confidence | Green | `#16a34a` | Confirmed actions, high-match results |
| Warning / Medium confidence | Amber | `#d97706` | Caution states, partial matches |
| Error / Low confidence | Red | `#ef4444` | Errors, low-match results, destructive |
| Info | Blue | `#2563eb` | Informational badges, links |

### Chart Palette

For data visualization, use a coordinated 5-color palette:

| Token | Hex | Role |
|-------|-----|------|
| `--chart-1` | `#059669` | Primary series |
| `--chart-2` | `#10b981` | Secondary series |
| `--chart-3` | `#334155` | Tertiary / contrast |
| `--chart-4` | `#eab308` | Highlight / warning |
| `--chart-5` | `#f97316` | Accent / alert |

### Color Usage Rules

1. **Never use color alone** to convey meaning — always pair with icons, text, or patterns (WCAG).
2. **Minimum contrast:** 4.5:1 for text, 3:1 for UI components.
3. **Primary color** is for interactive elements only (buttons, links, focus rings) — not decoration.
4. **Dark theme** must be fully tokenized — no hardcoded light colors in components.
5. **oklch() warning:** Tailwind v4 + Turbopack silently converts oklch() to grayscale. Always use hex values in CSS custom properties.

---

## 3. Typography

### Font Stack

```css
--font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

**Plus Jakarta Sans** — Geometric sans-serif with excellent readability at small sizes. Professional without being sterile. Load weights: 400, 500, 600, 700, 800.

**JetBrains Mono** — For code, IDs, technical data. Load weights: 400, 500, 600, 700.

### Type Scale

| Role | Size | Weight | Line Height | Example |
|------|------|--------|-------------|---------|
| Hero / Page title | 32px | 700–800 | 1.2 | Main landing heading |
| Section header | 22px | 700 | 1.3 | Page section titles |
| Card title | 14–15px | 600–700 | 1.4 | Card headers, list items |
| Body text | 13–14px | 400–500 | 1.5 | Descriptions, paragraphs |
| Label | 12–13px | 600–700 | 1.5 | Form labels, column headers |
| Caption | 11px | 400–500 | 1.5 | Timestamps, helper text |
| Fine print | 10px | 400 | 1.5 | Legal, footnotes |

### Typography Rules

1. Use `antialiased` rendering on the root element.
2. Monospace font for all codes, IDs, and technical identifiers — displayed at 14px bold with `letter-spacing: 0.05em`.
3. Labels use `uppercase` + `tracking-wider` + `font-semibold` for clear visual separation from body text.
4. Never use more than 3 font weights on a single screen.
5. Line length: max `65ch` for body text readability.

---

## 4. Spacing & Layout

### Base Unit

**4px** base unit. All spacing is a multiple of 4.

### Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `space-1` | 4px | Tight gaps, icon padding |
| `space-2` | 8px | Inline elements, badge padding |
| `space-3` | 12px | Small card padding |
| `space-4` | 16px | Default element spacing |
| `space-5` | 20px | Medium gaps |
| `space-6` | 24px | Section spacing, card padding |
| `space-8` | 32px | Large section gaps |
| `space-10` | 40px | Page section margins |
| `space-12` | 48px | Major section dividers |

### Border Radius Scale

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | 6px | Small elements, badges, pills |
| `radius-md` | 8px | Buttons, inputs |
| `radius` | 10px | Cards, panels (base) |
| `radius-xl` | 14px | Large cards, modals |
| `radius-2xl` | 18px | Hero elements |
| `radius-3xl` | 22px | Feature cards |
| `radius-4xl` | 26px | Large decorative elements |
| `radius-full` | 9999px | Circular elements, avatar, pill badges |

### Layout Grid

```css
/* Container */
.container {
  max-width: 1280px;     /* Default */
  padding: 0 24px;
  margin: 0 auto;
}

/* Wide container for data-heavy pages */
.container-wide {
  max-width: 1600px;
}

/* Narrow container for forms/auth */
.container-narrow {
  max-width: 448px;      /* max-w-md */
}
```

### Common Layout Patterns

**Header + Content:**
```
┌──────────────────────────────────────┐
│  Header (sticky, dark bg, z-50)      │
├──────────────────────────────────────┤
│                                      │
│  Content (container, centered)       │
│                                      │
└──────────────────────────────────────┘
```

**Content + Sidebar:**
```
┌──────────────────────────────────────┐
│  Header                             │
├────────────────────────┬─────────────┤
│                        │             │
│  Main content          │  Sidebar    │
│  (flexible)            │  (sticky)   │
│                        │  ~280px     │
│                        │             │
├────────────────────────┴─────────────┤
│  Footer                              │
└──────────────────────────────────────┘
```

**Centered Form:**
```
┌──────────────────────────────────────┐
│  Header                             │
├──────────────────────────────────────┤
│          ┌──────────────┐            │
│          │  Form Card   │            │
│          │  max-w-md    │            │
│          │  centered    │            │
│          └──────────────┘            │
└──────────────────────────────────────┘
```

---

## 5. Component Patterns

### Button Hierarchy

| Variant | Style | Usage |
|---------|-------|-------|
| **Default** | Filled primary color | Main CTA — Search, Save, Confirm |
| **Secondary** | Muted background | Alternative actions — Cancel, Back |
| **Outline** | Border only | Lower-priority actions |
| **Ghost** | Text only, no border | Tertiary actions — Help, Skip, inline links |
| **Destructive** | Red background | Delete, Clear, Remove |
| **Link** | Underlined text | Navigation-style actions |

**Button sizes:** `sm` (32px), `default` (36px), `lg` (40px), `icon` (36×36px).

### Input Fields

- Border: `--input` color, 1px solid
- Focus: `ring-ring/50` with 3px ring width
- Error: red border + red helper text below
- Validation: on blur, never on keystroke
- Required fields: asterisk + "(required)" for accessibility

### Cards

```
┌─────────────────────────────────┐
│  CardHeader                     │
│    CardTitle        CardAction  │
│    CardDescription              │
├─────────────────────────────────┤
│  CardContent                    │
│    (flexible content area)      │
├─────────────────────────────────┤
│  CardFooter (optional)          │
└─────────────────────────────────┘
```

- Background: `--card` (white in light theme)
- Border: 1px solid `--border`
- Shadow: subtle `shadow-sm` or `shadow-md`
- Radius: `--radius` (10px)
- Padding: 16–24px

### Badges & Pills

| Variant | Background | Text | Usage |
|---------|-----------|------|-------|
| Success | emerald-50 | emerald-700 | Approved, high match |
| Warning | amber-50 | amber-700 | Pending, medium match |
| Error | red-50 | red-700 | Rejected, low match |
| Info | blue-50 | blue-700 | Informational tags |
| Neutral | slate-100 | slate-700 | Default tags, counts |

Shape: `rounded-full`, padding `px-3 py-1`, font `text-xs font-semibold`.

### Tables

- Header: uppercase labels, `text-xs font-semibold tracking-wider`, muted foreground
- Rows: alternating backgrounds optional, hover highlight
- Cells: `py-3 px-4`, left-aligned text, right-aligned numbers
- Mobile: horizontal scroll wrapper or card-based alternate layout

---

## 6. Header & Navigation

### Header Design

- **Background:** Dark (`#0f172a`) — creates strong visual anchor
- **Border:** Subtle `border-white/[0.06]` bottom
- **Shadow:** `0 2px 12px rgba(0,0,0,0.15)` for depth
- **Position:** `sticky top-0 z-50`
- **Height:** ~64px

### Header Anatomy

```
┌─────────────────────────────────────────────────┐
│  [Logo + Brand]     [Nav Links]     [Auth Area] │
└─────────────────────────────────────────────────┘
```

- **Logo:** Icon (gradient primary-500 → primary-700) + brand name + optional subtitle
- **Nav links:** Text links with active state (primary bg/text highlight)
- **Auth area:** User-specific actions (favorites count, settings, logout)

### Mobile Navigation

- Hamburger icon replaces nav links below `md` breakpoint
- Animated menu button (transforms between bars and X)
- Overlay menu: slide-down with `backdrop-blur`
- All nav items + auth section in mobile overlay

### Active State

- Desktop: background highlight (`bg-white/10` or `bg-primary/20`) + text color change
- Mobile: left border accent or background highlight

---

## 7. Feedback & Notification Patterns

### Toast Notifications

| Type | Background | Icon | Duration | Dismiss |
|------|-----------|------|----------|---------|
| Success | green-50 / green-600 icon | CheckCircle | 3s | Auto + click |
| Error | red-50 / red-700 text | AlertCircle | 5s | Click only |
| Info | blue-50 / blue-600 icon | Info | 4s | Auto + click |
| Undo | amber-50 / amber text | Undo | 5s | Click (action) |

**Position:** Fixed, top-right or bottom-right.
**Animation:** Slide-in from edge, fade-out on dismiss.

### Inline Alerts

For persistent, contextual messages within the page flow.

```
┌─ [Icon] ──────────────────────────────┐
│  Alert message text with context.      │
│  [Optional action button]             │
└────────────────────────────────────────┘
```

- Background: status color at 50 opacity (e.g., `bg-amber-50`)
- Border: status color at 100 opacity
- Text: status color at 700

### Confirmation Dialogs

Use **sparingly** — only for destructive or irreversible actions.

```
┌────────────────────────────────────┐
│         [Warning Icon]             │
│                                    │
│    Are you sure you want to        │
│    delete this item?               │
│                                    │
│    Description text explaining     │
│    the consequences.               │
│                                    │
│    [Cancel]        [Delete]        │
└────────────────────────────────────┘
```

- Overlay: `fixed inset-0 bg-black/40`
- Card: white, centered, max-w-md, rounded-xl, shadow-2xl
- Destructive button: red variant

### Loading States

| Context | Pattern |
|---------|---------|
| Page load | Full skeleton layout |
| Section load | Skeleton lines/cards with pulse animation |
| Button action | Spinner inside button, button disabled |
| Search | 3 skeleton cards, subtle pulse |
| Inline | Small spinner + "Loading..." text |

### Empty States

```
┌────────────────────────────────────┐
│                                    │
│           [Gray Icon]              │
│                                    │
│    No items to display             │
│    Helpful description of what     │
│    the user can do next.           │
│                                    │
│    [Primary CTA Button]           │
│                                    │
└────────────────────────────────────┘
```

Every empty state must have:
1. An icon (gray, 48px)
2. A headline
3. A helpful description
4. A clear call-to-action

### Error States

```
┌─ [AlertTriangle] ─────────────────┐
│  Something went wrong.             │
│  Error detail message here.        │
│  [Try Again]                       │
└────────────────────────────────────┘
```

- Background: `bg-red-50`, border: `border-red-100`, text: `text-red-700`
- Always offer a recovery path (retry, go back, contact support)
- Never blame the user

---

## 8. Animation & Motion

### Principles

1. **Purposeful** — Animation communicates state changes, not decoration
2. **Fast** — 150–300ms for most transitions. Never block interaction.
3. **Respectful** — Always honor `prefers-reduced-motion`

### Standard Durations

| Type | Duration | Easing | Usage |
|------|----------|--------|-------|
| Micro-interactions | 150ms | ease-out | Hover, focus, toggle |
| Transitions | 200–300ms | ease-in-out | Panel open/close, page elements |
| Page transitions | 300ms | ease-out | Slide-in content |
| Attention | 1000ms | linear | Spinner rotation |

### Common Animations

| Animation | Implementation | Usage |
|-----------|---------------|-------|
| Fade in | `animate-in fade-in duration-200` | Content appearing |
| Slide in from top | `animate-in slide-in-from-top-2 duration-300` | Page content reveal |
| Slide in from right | `animate-in slide-in-from-right duration-300` | Panels, drawers |
| Spin | `animate-spin` | Loading spinners |
| Pulse | `animate-pulse` | Skeleton loaders |
| Collapse/expand | Height transition + `rotate-0`/`rotate-180` on chevron | Accordions, collapsible sections |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  .animate-spin { animation: none; }
  /* Reduce all transitions to instant */
}
```

```tsx
// Component pattern
<Spinner className="animate-spin motion-reduce:animate-none" />
```

---

## 9. Responsive Design

### Breakpoints

| Name | Min Width | Target |
|------|-----------|--------|
| (default) | 0 | Mobile portrait |
| `sm` | 640px | Mobile landscape |
| `md` | 768px | Tablet |
| `lg` | 1024px | Desktop |
| `xl` | 1280px | Large desktop |
| `2xl` | 1536px | Ultra-wide |

### Strategy: Mobile-First

All styles start from mobile and layer up:

```css
/* Mobile default */
.grid { grid-template-columns: 1fr; }

/* Tablet */
@media (min-width: 768px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
}

/* Desktop */
@media (min-width: 1024px) {
  .grid { grid-template-columns: repeat(3, 1fr); }
}
```

### Responsive Patterns by Component

| Component | Mobile | Tablet | Desktop |
|-----------|--------|--------|---------|
| Header nav | Hamburger overlay | Hamburger overlay | Inline links |
| Sidebar | Hidden or collapsible above content | Collapsible | Visible, 280px |
| Detail panel | Full-screen overlay | Modal overlay | Right drawer |
| Card grid | 1 column | 2 columns | 3–4 columns |
| Data tables | Card-based or horizontal scroll | Horizontal scroll | Full table |
| Search bar | Full width | Full width | Full width with sidebar |
| Footer | Stacked | Stacked | Inline |

### Touch Targets

- Minimum touch target: **44×44px** (WCAG)
- Spacing between touch targets: minimum **8px**
- Mobile buttons: full-width where appropriate

---

## 10. Accessibility (WCAG 2.1 AA)

### Requirements

| Area | Standard | Implementation |
|------|----------|----------------|
| Color contrast | 4.5:1 text, 3:1 UI | Test with axe-core |
| Keyboard nav | Full tab order | All interactive elements focusable |
| Screen readers | ARIA labels | `aria-label`, `aria-live`, `role` |
| Focus indicators | Visible ring | 2–3px solid primary with offset |
| Motion | Respect preference | `prefers-reduced-motion` checks |
| Touch targets | 44×44px minimum | Tailwind sizing classes |

### Keyboard Patterns

| Key | Action |
|-----|--------|
| `Tab` | Move focus forward |
| `Shift+Tab` | Move focus backward |
| `Enter` / `Space` | Activate button/link |
| `Escape` | Close modal/panel/dropdown |
| `Arrow keys` | Navigate within lists/menus |
| `/` | Focus search bar (global shortcut) |

### ARIA Patterns

```tsx
// Loading state
<button aria-busy={isLoading} aria-label={isLoading ? "Loading..." : "Submit"} disabled={isLoading}>
  {isLoading ? <Spinner /> : "Submit"}
</button>

// Live region for dynamic results
<div aria-live="polite" aria-atomic="true">
  {resultCount} results found
</div>

// Expandable section
<button aria-expanded={isOpen} aria-controls="panel-id">
  Toggle Section
</button>
<div id="panel-id" hidden={!isOpen}>...</div>
```

### Accessibility Checklist

- [ ] All images have descriptive `alt` text
- [ ] All form inputs have associated `<label>` elements
- [ ] All interactive elements are keyboard accessible
- [ ] Color is never the sole indicator of meaning
- [ ] Focus order matches visual order
- [ ] Error messages are associated with their fields
- [ ] Skip-to-main-content link exists
- [ ] Heading hierarchy is logical (h1 → h2 → h3)
- [ ] Modals trap focus and return focus on close
- [ ] Live regions announce dynamic content changes

### Testing Strategy

**Automated:** axe-core in CI, Lighthouse audits, ESLint `jsx-a11y` plugin.
**Manual:** Keyboard-only navigation, screen reader test (NVDA/VoiceOver), color blindness simulation.

---

## 11. Form Design

### Validation Strategy

| When | What |
|------|------|
| On blur | Validate individual field |
| On submit | Validate entire form |
| On keystroke | **Never** (except real-time search) |

### Form Layout

```
┌────────────────────────────────────┐
│  Form Title (h2)                   │
│                                    │
│  Label *                           │
│  ┌──────────────────────────────┐  │
│  │  Input field                 │  │
│  └──────────────────────────────┘  │
│  Helper text or error message      │
│                                    │
│  Label                             │
│  ┌──────────────────────────────┐  │
│  │  Input field                 │  │
│  └──────────────────────────────┘  │
│                                    │
│  [Cancel]            [Submit]      │
└────────────────────────────────────┘
```

### Field States

| State | Visual |
|-------|--------|
| Default | `border-input` (slate-200) |
| Focus | `ring-ring/50` + `ring-[3px]` (emerald) |
| Error | Red border + red error text below |
| Disabled | Reduced opacity (0.5), `cursor-not-allowed` |
| Read-only | Muted background, no focus ring |

### Error Display

- Position: immediately below the field
- Color: `text-red-600`, `text-sm`
- Icon: optional small alert icon
- Association: `aria-describedby` linking error to field

### Form Libraries

- **Validation schema:** Zod
- **Form management:** React Hook Form
- **Integration:** `zodResolver` from `@hookform/resolvers`

---

## 12. Data Display

### Confidence / Score Visualization

For any system that surfaces ranked or scored results:

| Score Range | Color | Label Pattern | Icon |
|-------------|-------|--------------|------|
| 80–100% | Green (success) | "High [noun]" | CheckCircle |
| 50–79% | Amber (warning) | "Medium [noun]" | AlertTriangle |
| 0–49% | Red (error) | "Low [noun] — Verify" | XCircle |

Always include a tooltip explaining what the score means.

### Tree / Hierarchy Display

For parent-child data (org charts, category trees, taxonomies):

```
Section 01
├─ Chapter 01
│  ├─ Heading 0101
│  │  ├─ Subheading 0101.10
│  │  │  └─ Item 0101.10.10 ← highlighted if matched
│  │  └─ Subheading 0101.20
│  └─ Heading 0102
└─ Chapter 02
```

- Use Unicode tree connectors: `├─`, `└─`, `│`
- Color-code matched/selected nodes (primary color)
- Lazy-load children with loading indicator
- Collapsible sections with chevron rotation

### Detail Panels

For viewing full details of a selected item:

| Screen Size | Pattern |
|-------------|---------|
| Desktop | Right drawer (slide-in from right, ~400px wide) |
| Tablet | Modal overlay |
| Mobile | Full-screen page |

Content structure: Tabbed sections for multi-faceted data.

### Numeric Data

- Use monospace font for codes, IDs, numeric identifiers
- Right-align numbers in tables
- Use locale-appropriate formatting for currencies and percentages
- Group large numbers (1,234,567 or 1.234.567 per locale)

---

## 13. Iconography

### Icon Library

**Lucide React** — consistent, lightweight, tree-shakeable.

### Icon Sizing

| Context | Size | Tailwind |
|---------|------|----------|
| Inline with text | 16px | `w-4 h-4` |
| Buttons | 16–20px | `w-4 h-4` to `w-5 h-5` |
| Card/section headers | 20–24px | `w-5 h-5` to `w-6 h-6` |
| Empty states | 48px | `w-12 h-12` |
| Hero elements | 64px | `w-16 h-16` |

### Icon Usage Rules

1. Icons must always have an `aria-label` when used without visible text
2. Decorative icons use `aria-hidden="true"`
3. Interactive icons (buttons) need minimum 44×44px touch target
4. Color: inherit from parent text color — never hardcoded
5. Pair with text labels wherever space allows; icon-only for well-known patterns (star = favorite, X = close)

---

## 14. Dark Mode

### Implementation Strategy

1. Define all dark tokens in `:root.dark` or `@media (prefers-color-scheme: dark)` block
2. Every light token must have a dark counterpart
3. Components use semantic tokens only — never raw colors
4. Images/illustrations: consider `filter: brightness(0.9)` or alternate assets
5. Shadows: reduce opacity or switch to border-based elevation

### Dark Theme Mapping Pattern

| Light | Dark |
|-------|------|
| White backgrounds | slate-800/900 |
| slate-100 backgrounds | slate-800 |
| slate-900 text | slate-50 text |
| Colored badges | Same hue, adjusted lightness |
| Borders: slate-200 | `rgba(255,255,255,0.1)` |
| Primary: emerald-600 | emerald-500 (slightly lighter) |

### Testing

- Test all components in both themes
- Verify contrast ratios in dark mode independently
- Check that no hardcoded colors bleed through

---

## 15. Content & Microcopy

### Tone of Voice

- **Professional** — Respect the user's expertise
- **Concise** — Say it in fewer words
- **Helpful** — Every message suggests a next step
- **Honest** — Don't hide uncertainty behind vague language

### Microcopy Patterns

| Context | Pattern | Example |
|---------|---------|---------|
| Empty state headline | State what's missing | "No saved items yet" |
| Empty state body | Explain how to populate | "Items you save will appear here for quick access" |
| Error headline | State what happened | "Could not load results" |
| Error body | Suggest recovery | "Check your connection and try again" |
| Button label | Verb + object | "Save changes", "Delete item" |
| Loading | Present participle | "Loading...", "Searching..." |
| Success | Past tense confirmation | "Item saved", "Changes applied" |
| Confirmation prompt | Question format | "Delete this item? This cannot be undone." |

### Localization Considerations

- Set `<html lang="...">` to match the UI language
- Use `toLocaleDateString(locale, options)` for dates
- Keep brand names unchanged across locales
- Maintain universal terms (Email, URL, API) unchanged
- Use professional terminology appropriate to the domain

---

## 16. Search UX

### Search Bar

- **Position:** Always accessible — in header or as prominent page element
- **Behavior:** Auto-focus on page load, debounce input (150ms)
- **Features:** Clear button (X), keyboard shortcut hint (`/`), optional language detection indicator
- **Placeholder:** Descriptive — "Search by name, code, or description..."

### Results Display

1. Show results immediately as they arrive
2. Highlight matched terms in results
3. Show confidence/relevance when applicable
4. Offer "Load more" rather than pagination
5. Preserve search state on back navigation

### No Results

```
[Search icon, gray]
No results found for "query"

Suggestions:
• Check your spelling
• Try more general terms
• Browse categories instead

[Browse Categories]
```

---

## 17. Implementation Checklist for New Projects

### Phase 1: Foundation
- [ ] Fork `globals.css` and customize color tokens
- [ ] Set up font loading (Plus Jakarta Sans + JetBrains Mono)
- [ ] Install shadcn/ui and configure theme
- [ ] Build header/layout shell with responsive nav
- [ ] Set up dark mode toggle infrastructure

### Phase 2: Core Components
- [ ] Button variants (all 6)
- [ ] Input fields with validation states
- [ ] Card component with header/content/footer
- [ ] Badge variants (5 semantic colors)
- [ ] Toast notification system
- [ ] Loading/skeleton states
- [ ] Empty states template

### Phase 3: Patterns
- [ ] Search bar with debounce
- [ ] Data table with responsive fallback
- [ ] Form layout with Zod + React Hook Form
- [ ] Confirmation dialog for destructive actions
- [ ] Error boundary with recovery UI

### Phase 4: Polish
- [ ] Keyboard shortcuts
- [ ] Animation with `prefers-reduced-motion`
- [ ] Accessibility audit (axe-core)
- [ ] Dark mode verification
- [ ] Mobile device testing

---

## Appendix: Technology Reference

| Layer | Technology | Version |
|-------|-----------|---------|
| Framework | Next.js (App Router) | 16+ |
| UI Library | React | 19+ |
| Styling | Tailwind CSS | v4 |
| Component Library | shadcn/ui | Latest |
| Icons | Lucide React | Latest |
| State Management | Zustand | Latest |
| Forms | React Hook Form + Zod | Latest |
| Type System | TypeScript (strict) | 5+ |

---

*This guideline is a living document. Update it as design patterns evolve across projects.*
