---
name: frontend-patterns
description: CSS design system principles — token usage, semantic layering, mobile-first, component isolation.
when_to_use: Working on CSS, styling, design tokens, or frontend component structure.
user-invocable: false
---

# Frontend Design Principles

Core principles for maintaining consistent, maintainable frontend code. Framework-agnostic — adapt examples to your stack.

## 1. Single Source of Truth

Every design decision is defined exactly once. Design tokens live in the styles system. Components reference them, never redefine them.

```css
/* Token file */
:root { --color-primary: #5b5956; }

/* Component */
.button { background: var(--color-primary); }  /* yes */
.button { background: #5b5956; }               /* no */
```

For JavaScript/SDK integrations, read tokens at runtime:
```javascript
const primary = getComputedStyle(document.documentElement)
  .getPropertyValue('--color-primary').trim();
SDK.configure({ buttonColor: primary });  /* yes */
SDK.configure({ buttonColor: '#5b5956' }); /* no */
```

## 2. Variable-First Development

If it's a design value, it's a variable. Colors, spacing, fonts, shadows, radii, and breakpoints are always variables — even if used once.

```css
.card { padding: var(--space-xl); border-radius: var(--radius-lg); }     /* yes */
.card { padding: 32px; border-radius: 12px; }                            /* no */
```

Every referenced variable must exist in the token files. Undefined variables fall back to browser defaults silently.

Exceptions: `0`, single-pixel borders (`1px`), proportional values (`100%`), one-off transforms.

## 3. Semantic Layering

Base tokens -> Semantic tokens -> Component usage. Define primitives, map to purposes, use purposes in components.

```css
/* Layer 1: Base primitives */
:root { --color-charcoal: #5b5956; }

/* Layer 2: Semantic purpose */
:root { --color-primary: var(--color-charcoal); }

/* Layer 3: Component usage */
.button { background: var(--color-primary); }     /* yes — semantic */
.button { background: var(--color-charcoal); }    /* no — base primitive */
```

## 4. Separation of Concerns

CSS owns presentation. Never use inline styles. State changes toggle CSS classes, not inline styles.

```css
/* yes — class-driven state */
.card.selected { border-color: var(--color-accent); }

/* no — inline style state */
/* style={selected ? 'border: 2px solid blue;' : ''} */
```

Exception: JavaScript-calculated values unknown at build time.

## 5. Design Token Propagation

External integrations (third-party SDKs, embedded widgets) must read design tokens at runtime, not hardcode values. This keeps the design system as the single source of truth even across integration boundaries.

## 6. Component Isolation with Global Consistency

Components control their own structure (layout, flex, grid) but get their design values (colors, spacing, radii) from global tokens. Don't redefine token values inside components. Don't reach into child components with global selectors.

## 7. Mobile-First Progressive Enhancement

Base styles target mobile. Enhance upward with `min-width` media queries. Never use `max-width`.

```css
.grid { grid-template-columns: 1fr; }                          /* mobile */

@media (min-width: 768px) {
  .grid { grid-template-columns: repeat(2, 1fr); }             /* desktop */
}
```

Desktop-first (`max-width`) leads to undoing styles at smaller sizes — harder to maintain and reason about.

## 8. Explicit Over Implicit

Be clear about sizing, positioning, and state.

```css
.container { max-width: var(--max-width); margin: 0 auto; }    /* yes — explicit */
.container { width: 90%; }                                      /* no — 90% of what? */

.modal { position: fixed; top: 50%; left: 50%; }               /* yes — explicit */
.modal { position: absolute; }                                  /* no — relative to what? */
```

## 9. Consistency Over Cleverness

Prefer boring, predictable patterns over novel solutions. When solving similar problems, use the same approach. Before creating a new pattern, check if an existing one can be adapted.

```html
<!-- yes — consistent pattern for all cards -->
<div class="card"><h3 class="card-title">...</h3></div>

<!-- no — different naming for each similar component -->
<div class="service-box"><h3 class="service-heading">...</h3></div>
<div class="product-container"><h3 class="product-name">...</h3></div>
```
