---
id: 010-resizable-split-pane
title: Resizable Split Pane Component
epic: youtube-mindmap-tool
status: backlog
priority: medium
complexity: low
estimated_days: 1
dependencies: [006-react-app-foundation]
created: 2025-09-04
updated: 2025-09-04
assignee: TBD
labels: [frontend, react, ui, layout, resize]
---

# Resizable Split Pane Component

## Description
Implement a resizable split pane component that allows users to adjust the width allocation between the video player section and mind map section with smooth drag interactions and proper cursor states.

## Acceptance Criteria
- [ ] Draggable separator bar between video and mind map sections
- [ ] Smooth resizing with real-time content adjustment
- [ ] Cursor state changes: pointer → fist → pointer during drag
- [ ] Minimum and maximum width constraints for both sections
- [ ] Responsive behavior for different screen sizes
- [ ] Preserve split ratio in user preferences/local storage
- [ ] Double-click to reset to default 50/50 split
- [ ] Visual feedback during drag operation (separator highlighting)
- [ ] Touch support for mobile/tablet devices
- [ ] Keyboard accessibility for resize operations

## Technical Requirements

### Split Pane Component Structure:
```jsx
<div className="flex h-full">
  <div 
    className="flex-shrink-0 overflow-hidden"
    style={{ width: `${leftPaneWidth}px` }}
  >
    <VideoPlayerSection />
  </div>
  
  <ResizableSeparator
    onDrag={handleSeparatorDrag}
    onDragStart={handleDragStart}
    onDragEnd={handleDragEnd}
    className="w-1 bg-gray-300 hover:bg-gray-400 cursor-col-resize"
  />
  
  <div className="flex-1 overflow-hidden">
    <MindMapSection />
  </div>
</div>
```

### Drag Interaction Logic:
```typescript
interface ResizeState {
  isDragging: boolean;
  startX: number;
  startWidth: number;
  currentWidth: number;
  minWidth: number;
  maxWidth: number;
}

const handleMouseDown = (event: MouseEvent) => {
  setIsDragging(true);
  document.body.style.cursor = 'col-resize';
  // Prevent text selection during drag
  document.body.style.userSelect = 'none';
};

const handleMouseMove = (event: MouseEvent) => {
  if (!isDragging) return;
  const deltaX = event.clientX - startX;
  const newWidth = clamp(startWidth + deltaX, minWidth, maxWidth);
  setLeftPaneWidth(newWidth);
};
```

### Split Pane APIs:
```
/**
* Resizable Split Pane Controller
* Manage split pane resizing and state persistence
* Input Parameters: initialSplit (number), minSizes (array), maxSizes (array)
* Return Parameters: SplitPaneState with current dimensions
* URL Address: N/A (Frontend component)
* Request Method: N/A (Frontend component)
**/

/**
* Separator Drag Handler
* Handle mouse/touch events for resizing operations
* Input Parameters: dragEvent (object), constraints (object)
* Return Parameters: DragResult with new dimensions
* URL Address: N/A (Frontend event handler)
* Request Method: N/A (Frontend event handler)
**/
```

### Responsive Constraints:
- **Desktop (>1024px)**: Min 300px, Max 70% of screen width
- **Tablet (768-1024px)**: Min 280px, Max 60% of screen width  
- **Mobile (<768px)**: Switch to vertical stacking, no resize needed

### Persistence Strategy:
- Store split ratio in localStorage as `mindmap-split-ratio`
- Restore on application load with validation
- Fallback to 50/50 split if stored value is invalid

## Definition of Done
- Split pane resizes smoothly without lag or glitches
- Cursor states change appropriately during drag operations
- Minimum/maximum constraints prevent unusable layouts
- User preferences are persisted and restored correctly
- Touch interactions work on mobile/tablet devices
- Double-click reset functionality works reliably
- Component integrates seamlessly with video player and mind map
- Performance remains smooth during continuous resizing