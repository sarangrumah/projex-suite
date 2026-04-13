---
name: tailwind-styling
description: ProjeX Suite design system and Tailwind CSS styling guide. Use when styling components, creating layouts, designing UI elements, choosing colors, or implementing responsive design. Covers the ProjeX brand palette, typography, spacing, cards, badges, and dark mode.
allowed-tools: Read, Write, Edit, Grep
---

# ProjeX Suite Design System — Tailwind CSS

## Brand Color Palette

```js
// tailwind.config.js extended colors
colors: {
  brand: {
    navy:    '#0F172A',  // Primary dark (sidebar, dark slides)
    blue:    '#0A66C2',  // Primary action (buttons, links)
    sky:     '#0EA5E9',  // Accent (highlights, hover)
    50:      '#EFF6FF',  // Lightest blue bg
    100:     '#DBEAFE',
  },
  surface: {
    primary: '#FFFFFF',  // Cards, modals
    secondary: '#F8FAFC', // Page background
    tertiary: '#F1F5F9',  // Alternate rows, subtle sections
  },
  text: {
    primary:   '#1E293B',  // Headings
    secondary: '#374151',  // Body
    muted:     '#64748B',  // Captions, placeholders
    disabled:  '#9CA3AF',
  },
  status: {
    success: '#059669',  green: '#059669',
    warning: '#D97706',  amber: '#D97706',
    error:   '#DC2626',  red: '#DC2626',
    info:    '#0EA5E9',
  },
  priority: {
    critical: '#DC2626',
    high:     '#F59E0B',
    normal:   '#3B82F6',
    low:      '#6B7280',
  },
}
```

## Typography Scale
- Page title: `text-2xl font-bold text-text-primary` (24px)
- Section header: `text-lg font-semibold text-text-primary` (18px)
- Card title: `text-sm font-semibold text-text-primary` (14px)
- Body: `text-sm text-text-secondary` (14px)
- Caption: `text-xs text-text-muted` (12px)
- Badge: `text-xs font-medium` (12px)

Font stack: `font-sans` (defaults to Inter via @fontsource, fallback system)

## Spacing Rules
- Page padding: `p-6` (24px)
- Section gap: `gap-6` (24px)
- Card padding: `p-4` (16px)
- Card gap: `gap-3` (12px)
- Inline spacing: `gap-2` (8px)
- Minimum touch target: `h-9 min-w-9` (36px)

## Component Patterns

### Card
```html
<div class="rounded-lg border border-slate-200 bg-white p-4 shadow-sm hover:shadow-md transition-shadow">
  <!-- content -->
</div>
```

### Board Card (Kanban)
```html
<div class="rounded-md border border-slate-200 bg-white p-3 shadow-sm cursor-grab active:cursor-grabbing
            hover:border-brand-sky hover:shadow-md transition-all">
  <div class="flex items-center justify-between mb-2">
    <span class="text-xs font-mono text-brand-blue">AIM-101</span>
    <span class="priority-badge"><!-- priority --></span>
  </div>
  <h4 class="text-sm font-medium text-text-primary line-clamp-2">Task title here</h4>
  <div class="flex items-center justify-between mt-3">
    <div class="flex items-center gap-1">
      <img class="h-5 w-5 rounded-full" src="avatar" alt="" />
    </div>
    <span class="text-xs text-text-muted">5 SP</span>
  </div>
</div>
```

### Button Variants
```html
<!-- Primary -->
<button class="inline-flex items-center gap-2 rounded-md bg-brand-blue px-4 py-2 text-sm font-medium text-white
               hover:bg-brand-blue/90 focus:ring-2 focus:ring-brand-sky focus:ring-offset-2 transition-colors">
  + Create
</button>

<!-- Secondary -->
<button class="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-2 text-sm
               font-medium text-text-secondary hover:bg-slate-50 transition-colors">
  Cancel
</button>

<!-- Danger -->
<button class="inline-flex items-center gap-2 rounded-md bg-status-error px-4 py-2 text-sm font-medium text-white
               hover:bg-red-700 transition-colors">
  Delete
</button>
```

### Priority Badge
```html
<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium
             bg-red-100 text-red-700">Critical</span>
<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium
             bg-amber-100 text-amber-700">High</span>
<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium
             bg-blue-100 text-blue-700">Normal</span>
<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium
             bg-slate-100 text-slate-600">Low</span>
```

### Status Badge
```html
<span class="inline-flex items-center gap-1 text-xs">
  <span class="h-2 w-2 rounded-full bg-status-success"></span>
  Done
</span>
```

### Sidebar Navigation
```html
<nav class="flex flex-col w-60 bg-brand-navy text-white h-screen">
  <div class="p-4 border-b border-white/10">
    <span class="text-lg font-bold text-brand-sky">ProjeX</span>
  </div>
  <div class="flex-1 overflow-y-auto py-2">
    <a class="flex items-center gap-3 px-4 py-2 text-sm text-slate-300 hover:bg-white/10 hover:text-white
              rounded-md mx-2 transition-colors">
      <HomeIcon class="h-4 w-4" />
      For You
    </a>
    <!-- active state: bg-white/10 text-white -->
  </div>
</nav>
```

## Layout Patterns

### App Shell (sidebar + content)
```html
<div class="flex h-screen bg-surface-secondary">
  <aside class="w-60 flex-shrink-0"><!-- sidebar --></aside>
  <main class="flex-1 overflow-y-auto">
    <header class="sticky top-0 z-10 bg-white border-b border-slate-200 px-6 py-3">
      <!-- space tabs -->
    </header>
    <div class="p-6"><!-- page content --></div>
  </main>
</div>
```

### Board Layout (Kanban columns)
```html
<div class="flex gap-4 overflow-x-auto pb-4 min-h-[calc(100vh-12rem)]">
  <div class="flex-shrink-0 w-72 bg-surface-tertiary rounded-lg p-3">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-text-primary">To Do</h3>
      <span class="text-xs text-text-muted bg-white rounded-full px-2 py-0.5">6</span>
    </div>
    <div class="flex flex-col gap-2">
      <!-- cards here -->
    </div>
  </div>
</div>
```

## CRITICAL RULES
- NEVER use arbitrary values `[#123456]` — extend tailwind.config.js instead
- ALWAYS use the brand color palette above — no random colors
- ALWAYS include hover/focus states on interactive elements
- ALWAYS include `transition-*` for state changes
- ALWAYS use `text-sm` (14px) as base font size, not `text-base` (16px)
- ALWAYS use `rounded-lg` for cards, `rounded-md` for buttons, `rounded-full` for badges
- ALWAYS test responsive: mobile sidebar collapses to hamburger menu
