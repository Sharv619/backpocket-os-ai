# Prompt for Antigravity - Fix BackPocket OS Dashboard

## Context
The dashboard (static/index.html) was working but we broke it while adding WhatsApp status. Now content is visible but doesn't match the Magic Patterns design quality.

## Goal
Fix static/index.html to match the look and feel of magic 2.0 React app.

---

## WORKING REFERENCE - magic 2.0

### Layout Structure (App.tsx - WORKS)
```jsx
<div className="flex w-full h-screen overflow-hidden font-sans text-brown bg-cream relative">
  {/* Background */}
  <div className="absolute inset-0 z-0" style={{backgroundImage: url...}} />
  <div className="absolute inset-0 z-0 bg-cream/30 backdrop-blur-[2px]" />
  
  {/* Layout */}
  <div className="relative z-10 flex w-full h-full">
    <AppSidebar />  {/* Left sidebar */}
    <HomePage />    {/* Main content - flex-1 */}
  </div>
</div>
```

### HomePage Layout (WORKS)
```jsx
<div className="flex-1 h-full relative overflow-y-auto">
  <div className="min-h-full flex flex-col relative">
    {/* Avatar - positioned behind content */}
    <motion.div className="absolute right-0 top-0 bottom-0 ... z-0">
      <img src={CHERRY_PHOTO} style={{mixBlendMode: 'multiply', filter: 'saturate(1.1) contrast(1.05)'}} />
    </motion.div>
    
    {/* Content sections have higher z-index */}
    <WelcomeHeader z-index={5} />
    <TodoHero z-index={5} />         {/* Stats row */}
    <ChatPanel z-index={10} />      {/* Chat on top */}
    <ApprovalModal z-index={100} /> {/* Modal highest */}
  </div>
</div>
```

### Key CSS (index.css)
```css
body {
  background-color: #FAF7F2;  /* cream */
  color: #1A1613;               /* brown */
  font-family: 'DM Sans', sans-serif;
}
```

---

## BROKEN - static/index.html (FIX THIS)

### Current Issues

1. **Instructions/SOPs sections are blurry**
   - They appear but are behind the overlay
   - Need higher z-index to appear clearly on top

2. **Magnifier button not working**
   - The toggleMagnifier() function exists but doesn't zoom properly
   - Should scale all UI by 120% when active

3. **Icons are simple, not premium**
   - Need duotone/multi-color icons like magic 2.0
   - Current icons use single color fill

4. **Avatar blends poorly**
   - Currently overlaps/blocks content
   - Need position: absolute, z-index: 1, mix-blend-mode: multiply

5. **No frosted glass effects**
   - Cards/lists need: `background: rgba(255,255,255,0.4); backdrop-filter: blur(12px)`

---

## SPECIFIC FIXES NEEDED

### 1. Fix z-index layering (fix blurriness)
In static/index.html, find these sections and add:
```css
.instructions-section {
  z-index: 50;  /* was missing or too low */
  position: relative;
}

.chat-section {
  z-index: 10;
}

.welcome-section, .stats-row {
  z-index: 5;
}

.avatar-container {
  position: absolute;
  z-index: 1;  /* behind content */
  right: 0;
  mix-blend-mode: multiply;
}
```

### 2. Avatar positioning (CORRECT WAY - flexible, centered right)
The avatar should be flexible/flexbox positioned - centered vertically but on the right side of content:
```css
.avatar-container {
  position: absolute;
  right: 5%;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
  width: 35%;
  max-width: 400px;
  pointer-events: none;
}
.avatar-img {
  width: 100%;
  height: auto;
  max-height: 85vh;
  object-fit: contain;
  object-position: bottom right;
}
```

### 3. Fix magnifier function
The toggleMagnifier() adds "magnifier-on" class to body but zoom isn't working properly. Fix the scale/zoom implementation.

### 4. Add premium icon styles
Replace simple colored icons with duotone style matching magic 2.0/PremiumIcons.tsx

### 5. Add frosted glass to cards
```css
.expanded-list, .instructions-section {
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(12px);
  border-radius: 16px;
}
```

---

## Files to Compare
- **WORKING:** magic 2.0/src/App.tsx, magic 2.0/src/pages/HomePage.tsx, magic 2.0/src/index.css
- **BROKEN:** static/index.html

---

## Task
1. Read magic 2.0/src/App.tsx and magic 2.0/src/pages/HomePage.tsx for layout reference
2. Read magic 2.0/src/index.css for styling reference  
3. Fix static/index.html CSS to match the layout and styling
4. Ensure all sections are visible, properly layered, and match the Magic Patterns premium look

Focus on: z-index layering, avatar positioning (flexible but on right side), frosted glass effects, and magnifier functionality.