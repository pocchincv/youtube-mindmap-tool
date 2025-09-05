// Global types for the application

export interface YouTubeVideo {
  id: string;
  title: string;
  url: string;
  duration: number;
  thumbnailUrl?: string;
  channelName?: string;
  uploadDate?: string;
}

export interface MindMapNode {
  id: string;
  text: string;
  x: number;
  y: number;
  level: number;
  parentId?: string;
  children?: string[];
}

export interface MindMap {
  id: string;
  videoId: string;
  title: string;
  nodes: MindMapNode[];
  createdAt: string;
  updatedAt: string;
}

export interface AppState {
  currentVideo: YouTubeVideo | null;
  currentMindMap: MindMap | null;
  isLoading: boolean;
  error: string | null;
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark';
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

export interface BreakpointConfig {
  mobile: string;
  tablet: string;
  desktop: string;
  largeDesktop: string;
}