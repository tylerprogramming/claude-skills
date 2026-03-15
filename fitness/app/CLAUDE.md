# Project Context: React + Vite with shadcn/ui and Tailwind CSS

This project is a React application using Vite, TypeScript, Tailwind CSS v3, and shadcn/ui for UI components.

## Technology Stack
* **React 18** - UI library
* **Vite** - Build tool and dev server
* **TypeScript** - Type safety
* **Tailwind CSS v3** - Utility-first styling (**IMPORTANT: Must be v3.x, NOT v4**)
* **shadcn/ui** - Reusable component library
* **next-themes** - Dark mode support

## Project Structure
* `/src`: Main application source code
  * `/components/ui`: shadcn/ui components (auto-generated, do not manually edit)
  * `/lib`: Utility functions (includes `cn()` for className merging)
* `/public`: Static assets
* `components.json`: shadcn/ui configuration

## Critical Configuration Requirements

### Tailwind CSS Version
**⚠️ CRITICAL:** This project **MUST** use Tailwind CSS v3.x.

**DO NOT upgrade to Tailwind v4** - it is incompatible with shadcn/ui and will cause:
- Heavy/incorrect border rendering
- Broken component styling
- Calendar and date picker layout issues

**Correct versions:**
```json
{
  "devDependencies": {
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

### PostCSS Configuration
File: `postcss.config.js`
```js
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### CSS Structure
File: `src/index.css`

**Must follow this exact structure:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* CSS variables for light mode */
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    /* ... other variables */
  }

  .dark {
    /* CSS variables for dark mode */
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... other variables */
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
  }
}
```

**DO NOT:**
- Use `@import "tailwindcss"` (Tailwind v4 syntax)
- Use `@theme inline` directives
- Add custom typography or animations to `index.css`
- Modify CSS variable values unless intentional theming

## shadcn/ui Usage Guidelines

### Installing Components
**Always use the shadcn CLI:**
```bash
npx shadcn@latest add [component-name]
```

**To avoid overwriting existing components:**
- The CLI will prompt "File already exists. Overwrite?"
- Type `n` to skip or `y` to overwrite
- Use `echo "n" | npx shadcn@latest add [component]` to automatically skip

**Examples:**
```bash
# Install single component
npx shadcn@latest add button

# Install multiple components
npx shadcn@latest add card dialog calendar

# Auto-skip existing files
echo "n" | npx shadcn@latest add button card
```

### Component Usage
* **Always** use components from `src/components/ui/` if they exist
* Do not generate component code from scratch - install via CLI
* Do not manually edit generated components in `/components/ui/`
* Import components: `import { Button } from '@/components/ui/button'`

### Available Components
Currently installed:
- alert-dialog
- badge
- button
- calendar
- card
- dialog
- input
- label
- popover
- select
- textarea

## Development Workflows

### Installation
```bash
npm install
```

### Running Development Server
```bash
npm run dev
# Server runs on http://localhost:5173 (or next available port)
```

### Building for Production
```bash
npm run build
# Outputs to /dist directory
```

### Adding New shadcn/ui Components
```bash
npx shadcn@latest add [component-name]
```

### Troubleshooting

#### Heavy Borders or Broken Styling
**Cause:** Tailwind v4 was accidentally installed

**Fix:**
```bash
npm uninstall tailwindcss @tailwindcss/postcss
npm install -D tailwindcss@^3.4.0 autoprefixer postcss
rm -rf node_modules package-lock.json
npm install
```

Then update `postcss.config.js` and `src/index.css` to v3 syntax (see above).

#### Calendar/Date Picker Not Working
**Cause:** Usually component needs reinstall or CSS issue

**Fix:**
```bash
rm src/components/ui/calendar.tsx
npx shadcn@latest add calendar
```

#### Component Styling Issues
1. Check `tailwind.config.js` has proper `content` paths
2. Verify `src/index.css` uses `@tailwind` directives (not `@import`)
3. Ensure CSS variables are inside `@layer base`
4. Clear build cache: `rm -rf dist && npm run build`

## Design Principles
* Use shadcn/ui defaults - avoid custom styling unless necessary
* Prioritize the existing design system
* Keep `index.css` minimal - only shadcn/ui defaults
* Do not add unnecessary abstractions
* Components should be reusable and follow shadcn/ui patterns

## Theme Configuration
* Base color scheme: Slate (default shadcn/ui)
* Dark mode: Enabled via `next-themes` with class-based toggling
* CSS variables in HSL format for theming
* Border radius: `0.5rem` default

## Key Files
* `components.json` - shadcn/ui configuration (don't modify)
* `tailwind.config.js` - Tailwind configuration
* `src/index.css` - Global styles and CSS variables
* `src/components/ui/` - shadcn/ui components (auto-generated)
* `src/lib/utils.ts` - Utility functions including `cn()`
