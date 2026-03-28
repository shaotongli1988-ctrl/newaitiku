# Frontend Style Rules

## Design Tokens

- Token file: `frontend/src/assets/styles/variables.css`
- Global import: `frontend/src/style.css`

## Mandatory Rule For `.vue` Components

- Do not write hex colors such as `#1890ff` or `#ffffff` directly in component styles.
- Use design tokens with `var(--qb-*)` for all colors, radius, spacing, and shadows.

## Required Usage Examples

```css
/* text color */
color: var(--qb-text-main);

/* card container */
.card-item {
  background: var(--qb-bg-card);
  border-radius: var(--qb-radius-base);
  padding: calc(var(--qb-spacing-unit) * 4); /* 16px */
  box-shadow: var(--qb-shadow-card);
}
```

## Shared Utility Classes

- `.qb-text-main`: applies `color: var(--qb-text-main)`
- `.card-item`: applies card background, radius, spacing, and shadow tokens
