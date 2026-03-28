# Design System Document

## 1. Overview & Creative North Star: "The Academic Sanctuary"

This design system is engineered to transform the often-stressful experience of exam preparation into a focused, serene, and authoritative journey. Moving away from the cluttered, high-density layouts typical of traditional test-prep platforms, we adopt the **Creative North Star: The Academic Sanctuary.**

The goal is to provide a digital environment that feels like a premium, quiet library. We achieve this through "breathable" layouts, intentional asymmetry that guides the eye, and a sophisticated editorial approach to data visualization. By utilizing expansive white space and high-contrast typography, we create an experience that is not just a tool, but a professional partner in a student's success.

---

## 2. Colors

The color palette is rooted in a deep, authoritative blue, supported by a system of functional tints that provide clarity without visual noise.

### Palette Strategy
- **Primary (`#003fb1`)**: Our "Anchor Blue." Used for key brand moments and primary actions.
- **Secondary (`#006686`)**: A calmer teal-blue for secondary information and specialized modules.
- **Tertiary (`#005438`)**: An organic green used for "Success" states and progress indicators.
- **Surface System**: A 5-tier hierarchy from `surface-container-lowest` (`#ffffff`) to `surface-container-highest` (`#e0e3e5`) to create depth.

### The "No-Line" Rule
To maintain a premium, modern feel, **1px solid borders are prohibited for sectioning.** Structural boundaries must be defined through background color shifts. For example, a `surface-container-low` card should sit directly on a `surface` background. The change in tonal value provides the boundary, keeping the UI clean and "frameless."

### Glass & Gradient Rule
For high-level interactive elements (like floating navigation or active state cards), use Glassmorphism. 
- **Backdrop Blur:** 12px - 20px.
- **Fill:** `surface` at 70% opacity.
- **Signature Gradient:** Use a subtle linear gradient from `primary` to `primary_container` for hero CTAs to add "soul" and depth that flat color cannot provide.

---

## 3. Typography

Our typography is an editorial-first pairing designed for high legibility and academic authority.

*   **Display & Headlines (Manrope):** A modern, geometric sans-serif with a high X-height. It feels progressive and "expert." Used for page titles and large data points to command attention.
*   **Body & Labels (Inter):** The industry standard for screen readability. Its neutral tone ensures that complex question text is easy to digest over long study sessions.

**Hierarchy as Identity:**
- **Display-LG (3.5rem):** Used exclusively for high-impact motivation or key score percentages.
- **Headline-SM (1.5rem):** The standard for section headers, providing clear entry points into content blocks.
- **Body-MD (0.875rem):** The workhorse for question content and explanations.

---

## 4. Elevation & Depth

We eschew traditional "drop shadows" in favor of **Tonal Layering** and **Ambient Light**.

*   **The Layering Principle:** Depth is achieved by stacking tiers. Place a `surface-container-lowest` (#ffffff) card on a `surface-container-low` (#f2f4f6) background. This creates a "soft lift" that feels architectural rather than digital.
*   **Ambient Shadows:** Where floating is required (e.g., Modals), use extra-diffused shadows: `box-shadow: 0 12px 40px rgba(25, 28, 30, 0.06)`. Note the low opacity (6%) and large blur—this mimics natural ambient light.
*   **The Ghost Border:** If a boundary is strictly required for accessibility, use the `outline-variant` token at **15% opacity**. It should be felt, not seen.

---

## 5. Components

### Buttons
- **Primary:** Gradient fill (`primary` to `primary_container`), `xl` (1.5rem) roundedness. High-contrast `on_primary` text.
- **Tertiary/Ghost:** No container. Use `primary` text with an icon. For hover, use a `primary_fixed_dim` background at 20% opacity.

### Roundness Scale
- **Containers:** `lg` (1rem) for standard cards.
- **Input Fields:** `md` (0.75rem) to maintain a crisp, professional look.
- **Action Chips:** `full` (9999px) for a "pill" aesthetic that distinguishes them from cards.

### Input Fields
- Avoid boxes. Use a `surface-container-high` background with a `title-sm` label. 
- **Focus State:** Transitions to a `primary` "Ghost Border" (20% opacity) and a 2px bottom-accent-line in `primary`.

### Cards & Lists (The "Breath" Rule)
- **Prohibit Dividers:** Never use horizontal lines to separate list items. 
- **Separation Strategy:** Use `spacing-4` (1.4rem) or `spacing-5` (1.7rem) vertical gaps. If content is dense, use alternating `surface` and `surface-container-low` backgrounds.

### Specific Academic Components
- **Question Card:** `surface-container-lowest` fill, `xl` roundedness, with a `secondary_container` accent for the question number.
- **Progress Ring:** Use `tertiary` for completion. The track should be `surface-container-highest` rather than grey.

---

## 6. Do's and Don'ts

### Do
- **DO** use the `spacing-8` (2.75rem) or `spacing-10` (3.5rem) tokens between major sections to increase "breathing room."
- **DO** use `surface_bright` for background areas where you want the student to feel energized and focused.
- **DO** use `manrope` for any number-heavy data to give the system a "FinTech" level of precision.

### Don't
- **DON'T** use pure black `#000000` for text. Always use `on_surface` (`#191c1e`) to reduce eye strain.
- **DON'T** nest more than three levels of surface containers. It breaks the "Academic Sanctuary" serenity.
- **DON'T** use high-saturation reds for error states. Use the `error` (`#ba1a1a`) and `error_container` tokens to ensure the tone remains professional, not alarming.