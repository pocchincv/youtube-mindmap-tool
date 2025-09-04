---
id: 019-video-mind-map-synchronization
title: Video Player and Mind Map Synchronization
epic: youtube-mindmap-tool
status: backlog
priority: high
complexity: medium
estimated_days: 2
dependencies: [008-video-player-component, 009-mind-map-visualization-component]
created: 2025-09-04
updated: 2025-09-04
assignee: TBD
labels: [frontend, synchronization, video, mind-map, interaction]
---

# Video Player and Mind Map Synchronization

## Description
Implement bidirectional synchronization between the video player and mind map visualization, enabling seamless navigation where mind map node clicks jump to video timestamps and video playback highlights corresponding mind map nodes.

## Acceptance Criteria
- [ ] Mind map node clicks trigger accurate video timestamp navigation
- [ ] Video playback time automatically highlights corresponding mind map nodes
- [ ] Active node highlighting with ancestor dimming as specified in Epic
- [ ] Smooth synchronization without performance lag during playback
- [ ] Timestamp accuracy within ±1 second tolerance
- [ ] Synchronization state persistence across video seeking
- [ ] Auto-scroll mind map to keep active node visible
- [ ] Keyboard navigation support for both video and mind map
- [ ] Synchronization works during different playback speeds
- [ ] Error handling when timestamps don't align perfectly
- [ ] Visual feedback for synchronization state
- [ ] Performance optimization for large mind maps (500+ nodes)

## Technical Requirements

### Synchronization Controller:
```typescript
interface SyncState {
  currentVideoTime: number;
  activeNodeId: string | null;
  previousActiveNodeId: string | null;
  isVideoSeeking: boolean;
  isMindMapTriggered: boolean;
  syncEnabled: boolean;
}

class VideoMindMapSynchronizer {
  private state: SyncState = {
    currentVideoTime: 0,
    activeNodeId: null,
    previousActiveNodeId: null,
    isVideoSeeking: false,
    isMindMapTriggered: false,
    syncEnabled: true
  };
  
  private mindMapNodes: MindMapNode[] = [];
  private videoPlayerRef: React.RefObject<YouTubePlayer>;
  private mindMapRef: React.RefObject<MindMapVisualization>;
  private syncThrottleTimer: NodeJS.Timeout | null = null;
  
  constructor(
    videoPlayerRef: React.RefObject<YouTubePlayer>,
    mindMapRef: React.RefObject<MindMapVisualization>
  ) {
    this.videoPlayerRef = videoPlayerRef;
    this.mindMapRef = mindMapRef;
    this.setupEventListeners();
  }
  
  setupEventListeners() {
    // Video player time updates
    if (this.videoPlayerRef.current) {
      this.videoPlayerRef.current.addEventListener('timeupdate', this.handleVideoTimeUpdate);
      this.videoPlayerRef.current.addEventListener('seeking', this.handleVideoSeeking);
      this.videoPlayerRef.current.addEventListener('seeked', this.handleVideoSeeked);
    }
    
    // Mind map node interactions
    if (this.mindMapRef.current) {
      this.mindMapRef.current.addEventListener('nodeClick', this.handleNodeClick);
      this.mindMapRef.current.addEventListener('nodeHover', this.handleNodeHover);
    }
  }
  
  handleVideoTimeUpdate = (currentTime: number) => {
    if (this.state.isMindMapTriggered) {
      // Skip sync if navigation was triggered by mind map
      this.state.isMindMapTriggered = false;
      return;
    }
    
    this.throttledTimeSync(currentTime);
  };
  
  throttledTimeSync = (currentTime: number) => {
    if (this.syncThrottleTimer) {
      clearTimeout(this.syncThrottleTimer);
    }
    
    this.syncThrottleTimer = setTimeout(() => {
      this.syncMindMapToTime(currentTime);
    }, 100); // Throttle to avoid excessive updates
  };
  
  syncMindMapToTime(currentTime: number) {
    const activeNode = this.findNodeByTimestamp(currentTime);
    
    if (activeNode && activeNode.id !== this.state.activeNodeId) {
      this.updateActiveNode(activeNode.id);
      this.scrollMindMapToNode(activeNode.id);
    }
    
    this.state.currentVideoTime = currentTime;
  }
  
  handleNodeClick = (nodeId: string) => {
    const node = this.mindMapNodes.find(n => n.id === nodeId);
    if (!node) return;
    
    this.state.isMindMapTriggered = true;
    this.seekVideoToTimestamp(node.timestampStart);
    this.updateActiveNode(nodeId);
  };
  
  seekVideoToTimestamp(timestamp: number) {
    if (this.videoPlayerRef.current) {
      this.state.isVideoSeeking = true;
      this.videoPlayerRef.current.seekTo(timestamp, true);
    }
  }
  
  findNodeByTimestamp(currentTime: number): MindMapNode | null {
    // Find the most specific (deepest) node that contains the current time
    let candidateNode: MindMapNode | null = null;
    let maxDepth = -1;
    
    for (const node of this.mindMapNodes) {
      if (currentTime >= node.timestampStart && currentTime <= node.timestampEnd) {
        if (node.depth > maxDepth) {
          maxDepth = node.depth;
          candidateNode = node;
        }
      }
    }
    
    return candidateNode;
  }
  
  updateActiveNode(nodeId: string) {
    this.state.previousActiveNodeId = this.state.activeNodeId;
    this.state.activeNodeId = nodeId;
    
    // Update mind map visualization
    this.mindMapRef.current?.highlightNode(nodeId);
    this.dimAncestorNodes(nodeId);
    
    // Dispatch state change event
    this.dispatchSyncEvent('activeNodeChanged', {
      activeNodeId: nodeId,
      previousNodeId: this.state.previousActiveNodeId
    });
  }
  
  dimAncestorNodes(activeNodeId: string) {
    const activeNode = this.mindMapNodes.find(n => n.id === activeNodeId);
    if (!activeNode) return;
    
    // Get all ancestor nodes up to root
    const ancestorIds = this.getAncestorNodeIds(activeNode);
    
    // Apply dimming to ancestors, normal styling to others
    this.mindMapNodes.forEach(node => {
      const isDimmed = ancestorIds.includes(node.id) && node.id !== activeNodeId;
      this.mindMapRef.current?.setNodeDimmed(node.id, isDimmed);
    });
  }
  
  getAncestorNodeIds(node: MindMapNode): string[] {
    const ancestors: string[] = [];
    let currentNode = node;
    
    while (currentNode.parentNodeId) {
      ancestors.push(currentNode.parentNodeId);
      currentNode = this.mindMapNodes.find(n => n.id === currentNode.parentNodeId)!;
      if (!currentNode) break;
    }
    
    return ancestors;
  }
  
  scrollMindMapToNode(nodeId: string) {
    // Ensure active node is visible in mind map viewport
    this.mindMapRef.current?.scrollToNode(nodeId, {
      behavior: 'smooth',
      block: 'center'
    });
  }
  
  // Public API methods
  enableSync() {
    this.state.syncEnabled = true;
  }
  
  disableSync() {
    this.state.syncEnabled = false;
  }
  
  getCurrentSyncState(): SyncState {
    return { ...this.state };
  }
  
  private dispatchSyncEvent(eventType: string, data: any) {
    window.dispatchEvent(new CustomEvent(`mindmap:${eventType}`, { detail: data }));
  }
}
```

### React Hook for Synchronization:
```typescript
const useMindMapSync = (
  videoPlayerRef: React.RefObject<YouTubePlayer>,
  mindMapRef: React.RefObject<MindMapVisualization>,
  mindMapNodes: MindMapNode[]
) => {
  const [synchronizer, setSynchronizer] = useState<VideoMindMapSynchronizer | null>(null);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  const [isVideoSeeking, setIsVideoSeeking] = useState(false);
  
  useEffect(() => {
    if (videoPlayerRef.current && mindMapRef.current) {
      const sync = new VideoMindMapSynchronizer(videoPlayerRef, mindMapRef);
      sync.setMindMapNodes(mindMapNodes);
      setSynchronizer(sync);
      
      // Listen for sync events
      const handleActiveNodeChanged = (event: CustomEvent) => {
        setActiveNodeId(event.detail.activeNodeId);
      };
      
      const handleVideoSeeking = () => setIsVideoSeeking(true);
      const handleVideoSeeked = () => setIsVideoSeeking(false);
      
      window.addEventListener('mindmap:activeNodeChanged', handleActiveNodeChanged);
      window.addEventListener('video:seeking', handleVideoSeeking);
      window.addEventListener('video:seeked', handleVideoSeeked);
      
      return () => {
        window.removeEventListener('mindmap:activeNodeChanged', handleActiveNodeChanged);
        window.removeEventListener('video:seeking', handleVideoSeeking);
        window.removeEventListener('video:seeked', handleVideoSeeked);
        sync.cleanup();
      };
    }
  }, [videoPlayerRef, mindMapRef, mindMapNodes]);
  
  const seekToNode = useCallback((nodeId: string) => {
    if (synchronizer) {
      synchronizer.handleNodeClick(nodeId);
    }
  }, [synchronizer]);
  
  const toggleSync = useCallback((enabled: boolean) => {
    if (synchronizer) {
      enabled ? synchronizer.enableSync() : synchronizer.disableSync();
    }
  }, [synchronizer]);
  
  return {
    activeNodeId,
    isVideoSeeking,
    seekToNode,
    toggleSync,
    synchronizer
  };
};
```

### Enhanced Mind Map Component Integration:
```jsx
const MindMapVisualization = ({ nodes, onNodeClick, activeNodeId, ...props }) => {
  const mindMapRef = useRef<HTMLDivElement>(null);
  const [dimmedNodes, setDimmedNodes] = useState<Set<string>>(new Set());
  
  // Expose methods to synchronizer
  useImperativeHandle(ref, () => ({
    highlightNode: (nodeId: string) => {
      // Update visualization to highlight specific node
      updateNodeHighlight(nodeId);
    },
    
    setNodeDimmed: (nodeId: string, dimmed: boolean) => {
      setDimmedNodes(prev => {
        const newSet = new Set(prev);
        if (dimmed) {
          newSet.add(nodeId);
        } else {
          newSet.delete(nodeId);
        }
        return newSet;
      });
    },
    
    scrollToNode: (nodeId: string, options: ScrollIntoViewOptions) => {
      const nodeElement = document.getElementById(`mindmap-node-${nodeId}`);
      if (nodeElement) {
        nodeElement.scrollIntoView(options);
      }
    },
    
    addEventListener: (event: string, handler: EventListener) => {
      mindMapRef.current?.addEventListener(event, handler);
    },
    
    removeEventListener: (event: string, handler: EventListener) => {
      mindMapRef.current?.removeEventListener(event, handler);
    }
  }));
  
  const handleNodeClick = useCallback((nodeId: string) => {
    // Dispatch custom event for synchronizer
    const event = new CustomEvent('nodeClick', { detail: { nodeId } });
    mindMapRef.current?.dispatchEvent(event);
    
    // Call parent handler
    onNodeClick?.(nodeId);
  }, [onNodeClick]);
  
  return (
    <div ref={mindMapRef} className="mindmap-container">
      {nodes.map(node => (
        <MindMapNode
          key={node.id}
          node={node}
          isActive={node.id === activeNodeId}
          isDimmed={dimmedNodes.has(node.id)}
          onClick={() => handleNodeClick(node.id)}
        />
      ))}
    </div>
  );
};
```

### Performance Optimizations:
```typescript
// Debounced time update for better performance
const useDebouncedTimeUpdate = (callback: (time: number) => void, delay: number = 100) => {
  const debouncedCallback = useMemo(
    () => debounce(callback, delay),
    [callback, delay]
  );
  
  return debouncedCallback;
};

// Memoized node finding for large datasets
const useMemoizedNodeFinder = (nodes: MindMapNode[]) => {
  return useMemo(() => {
    // Create time-indexed lookup for faster node finding
    const timeIndex = new Map<number, MindMapNode[]>();
    
    nodes.forEach(node => {
      for (let time = node.timestampStart; time <= node.timestampEnd; time++) {
        if (!timeIndex.has(time)) {
          timeIndex.set(time, []);
        }
        timeIndex.get(time)!.push(node);
      }
    });
    
    return (currentTime: number): MindMapNode | null => {
      const candidates = timeIndex.get(Math.floor(currentTime)) || [];
      
      // Return the deepest node that contains this time
      return candidates.reduce((deepest, node) => {
        if (currentTime >= node.timestampStart && currentTime <= node.timestampEnd) {
          return !deepest || node.depth > deepest.depth ? node : deepest;
        }
        return deepest;
      }, null);
    };
  }, [nodes]);
};
```

### Synchronization APIs:
```
/**
* Video-MindMap Synchronization
* Synchronize video playback with mind map node highlighting
* Input Parameters: currentTime (number), nodeId (string, optional)
* Return Parameters: SyncResult with active node and state
* URL Address: N/A (Frontend synchronization)
* Request Method: N/A (Frontend functionality)
**/

/**
* Node Click Navigation
* Navigate video to specific timestamp when mind map node is clicked
* Input Parameters: nodeId (string), timestamp (number)
* Return Parameters: NavigationResult with seek status
* URL Address: N/A (Frontend functionality)
* Request Method: N/A (Frontend functionality)
**/
```

## Definition of Done
- Mind map node clicks accurately navigate video to correct timestamps
- Video playback automatically highlights corresponding mind map nodes
- Active node highlighting and ancestor dimming work as specified
- Synchronization performs smoothly without lag during playback
- Timestamp accuracy is within ±1 second tolerance
- Auto-scroll keeps active nodes visible in mind map viewport
- Keyboard navigation works for both video and mind map
- Performance is acceptable with large mind maps (500+ nodes)
- Error handling gracefully manages timestamp misalignments
- Synchronization state is maintained across video seeking operations
- Visual feedback clearly indicates synchronization status