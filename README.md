# Model Autopsy — Frontend

> **Find Out Why AI Fails.**  
> A research-grade frontend interface for empirical machine learning robustness testing, failure boundary detection, and stress-testing evaluation.

---

## 🏛 Architecture & Design System

The Model Autopsy frontend is engineered with research-first aesthetics, dark-mode ergonomics, and strict scientific honesty guarantees.

### Typography
- **Headings & Primary UI**: [Manrope](https://fonts.google.com/specimen/Manrope) (sans-serif, geometric, readable)
- **Body & Longform Copy**: [Cabin](https://fonts.google.com/specimen/Cabin) (humanist sans-serif)
- **Monospace & Data Points**: `Fira Code`, `JetBrains Mono`, `monospace`
- **Editorial Taglines**: [Instrument Serif](https://fonts.google.com/specimen/Instrument+Serif) (italic, serif)

### Design Tokens
- **Background**: Deep carbon black (`#070709`)
- **Surface 1**: Layered card carbon (`#0c0c0f`, border: `rgba(255,255,255,0.08)`)
- **Surface 2**: Elevated slate (`#141419`, border: `rgba(255,255,255,0.12)`)
- **Accent**: High-energy electric coral/orange (`#FF4D2D`) with subtle glow filters
- **Muted Text**: Subtle cool silver (`#94a3b8` / `#64748b`)

---

## 🖥 The 6 Core Screens

| Screen # | Screen Name | Route | Key Features |
|---|---|---|---|
| **1** | **Landing Page** | [`/`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/app/page.tsx) | Hero section with interactive 3D rotating wireframe brain canvas, quick autopsy launcher, scientific methodology overview, live results teaser, and keyboard navigation. |
| **2** | **Autopsy Workspace** | [`/workspace`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/app/workspace/page.tsx) | 5-step stepper workflow (Dataset → Model → Baseline → Stress Test → Review) with sticky real-time preview card, validation gates, and dual YAML/JSON export. |
| **3** | **Autopsy Running** | [`/experiments/[id]`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/app/experiments/[id]/page.tsx) | Circular SVG progress ring, 6-stage execution checklist with icon+text indicators, real-time Recharts telemetry, live test ticker, and cancel dialog. |
| **4** | **Results Dashboard** | [`/experiments/[id]/results`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/app/experiments/[id]/results/page.tsx) | 4 StatCards with CountUp animations, interactive Robustness Curve with accessible table toggle, client-side Boundary Simulator slider, and Feature Vulnerability rankings. |
| **5** | **Failure Explorer** | [`/experiments/[id]/failures`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/app/experiments/[id]/failures/page.tsx) | Summary strip, local-privacy callout, multi-filter bar with CSV export, keyboard-navigable (`↑`/`↓`/`Enter`) paginated failure table, and sticky 2D scatter analysis card. |
| **6** | **Research Report** | [`/experiments/[id]/report`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/app/experiments/[id]/report/page.tsx) | 3-column layout featuring sticky scroll-spy navigation, 3D mouse-tilt perspective cover, executive highlights, 12 formal sections, JSON export, and `@media print` PDF styles. |

### Supporting Resource Catalogs
- **Experiment History**: [`/experiments`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/app/experiments/page.tsx)
- **Dataset Registry**: [`/datasets`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/app/datasets/page.tsx) & `/datasets/[id]`
- **Model Adapter Registry**: [`/models`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/app/models/page.tsx) & `/models/[id]`
- **Documentation**: [`/docs`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/app/docs/page.tsx)
- **Dev Kitchen Sink**: [`/dev`](file:///c:/MODEL_AUTOSPY/Model-Autopsy/frontend/app/dev/page.tsx)

---

## ⚖️ Scientific Honesty Rules

The UI strictly enforces these non-negotiable scientific constraints:

1. **Mandated Boundary Caption**:  
   Any presentation of empirical failure boundary is permanently captioned verbatim:  
   > *"Observed failure boundary under the specified experimental configuration."*
2. **Mandated Sensitivity Caveat**:  
   Any feature vulnerability ranking or perturbation delta is captioned verbatim:  
   > *"Empirical sensitivity — not a causal explanation."*
3. **No Aggregate Scores**:  
   The platform never presents an arbitrary "robustness score", "grade", or "safety index".
4. **Metric Direction Awareness**:  
   Improvements vs degradations explicitly respect metric polarity (e.g. F1 / Accuracy drop is bad; MAE / MSE rise is bad).
5. **Percentage Points vs Percentage**:  
   Absolute metric differences are designated in **percentage points (`pp`)**, distinct from relative percentage changes (`%`).
6. **No File Uploads**:  
   Arbitrary model binary weights are strictly prevented from upload. Models are selected via deterministic adapter configurations.
7. **Accessibility & Status Encoding**:  
   Status and error mismatches are **never conveyed by color alone** (always paired with dedicated icons like `XCircle` / `CheckCircle2` and explanatory text).
8. **Reduced Motion**:  
   All 3D perspective transforms, rotating canvases, and spring physics respect `prefers-reduced-motion: reduce`.

---

## 🛠 Tech Stack

- **Framework**: [Next.js 14](https://nextjs.org/) (App Router, React Server Components + Client Islands)
- **Language**: [TypeScript 5](https://www.typescriptlang.org/) (strict mode)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/) with custom tokens
- **Animations**: [Framer Motion](https://www.framer.com/motion/)
- **Charts**: [Recharts](https://recharts.org/)
- **Icons**: [Lucide React](https://lucide.dev/)
- **Validation**: [Zod](https://zod.dev/)
- **Testing**: [Vitest](https://vitest.dev/) with JSDOM

---

## 🚀 Getting Started

### Development Server
```bash
# Install dependencies
pnpm install

# Start the local development server (runs on port 3000)
pnpm run dev
```

### Type Checking & Linting
```bash
# Run TypeScript compilation check
pnpm run typecheck

# Run Next.js ESLint
pnpm run lint
```

### Running Tests
```bash
# Run the complete Vitest test suite
pnpm run test
```

### Production Build
```bash
# Build the production bundle
pnpm run build

# Start the production server
pnpm run start
```
