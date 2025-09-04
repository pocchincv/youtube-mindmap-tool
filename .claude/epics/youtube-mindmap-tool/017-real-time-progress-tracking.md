---
id: 017-real-time-progress-tracking
title: Real-time Progress Tracking with WebSockets
epic: youtube-mindmap-tool
status: backlog
priority: medium
complexity: medium
estimated_days: 2
dependencies: [015-video-processing-pipeline, 006-react-app-foundation]
created: 2025-09-04
updated: 2025-09-04
assignee: TBD
labels: [backend, frontend, websockets, real-time, progress]
---

# Real-time Progress Tracking with WebSockets

## Description
Implement real-time progress tracking for video processing using WebSocket connections to provide users with live updates on processing stages, estimated completion times, and queue status.

## Acceptance Criteria
- [ ] WebSocket server implementation for real-time communication
- [ ] Frontend WebSocket client with automatic reconnection
- [ ] Real-time progress updates during video processing
- [ ] Processing stage notifications with descriptive messages
- [ ] Queue position and estimated wait time updates
- [ ] Error notifications and retry status updates
- [ ] Connection state management and fallback to polling
- [ ] Progress visualization components (progress bars, stage indicators)
- [ ] Background processing status when user navigates away
- [ ] Multiple concurrent job tracking per user
- [ ] Message queuing for offline users
- [ ] Performance optimization for high concurrent users

## Technical Requirements

### WebSocket Server Implementation:
```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio

class WebSocketManager:
    def __init__(self):
        # user_id -> List[WebSocket connections]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # user_id -> List[pending messages]
        self.message_queue: Dict[str, List[dict]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept WebSocket connection and register user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        
        # Send queued messages if any
        if user_id in self.message_queue:
            for message in self.message_queue[user_id]:
                await self.send_personal_message(message, user_id)
            del self.message_queue[user_id]
    
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Handle WebSocket disconnection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to specific user's connections"""
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for conn in disconnected:
                self.active_connections[user_id].remove(conn)
        else:
            # Queue message for offline user
            if user_id not in self.message_queue:
                self.message_queue[user_id] = []
            self.message_queue[user_id].append(message)

websocket_manager = WebSocketManager()

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            # Handle client-side messages if needed (ping/pong, etc.)
            
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, user_id)
```

### Frontend WebSocket Client:
```typescript
interface ProgressUpdate {
  jobId: string;
  stage: string;
  progress: number;
  message: string;
  estimatedCompletion?: string;
  error?: string;
}

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 1000;
  private userId: string;
  
  constructor(userId: string) {
    this.userId = userId;
    this.connect();
  }
  
  private connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${this.userId}`;
    
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    
    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.reason);
      this.handleReconnection();
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }
  
  private handleReconnection() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1);
      
      setTimeout(() => {
        console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect();
      }, delay);
    } else {
      console.log('Max reconnection attempts reached. Falling back to polling.');
      this.fallbackToPolling();
    }
  }
  
  private handleMessage(data: ProgressUpdate) {
    // Dispatch to appropriate handlers based on message type
    switch (data.type) {
      case 'progress_update':
        this.onProgressUpdate(data);
        break;
      case 'processing_complete':
        this.onProcessingComplete(data);
        break;
      case 'processing_error':
        this.onProcessingError(data);
        break;
      case 'queue_update':
        this.onQueueUpdate(data);
        break;
    }
  }
  
  // Event handlers - to be implemented by consuming components
  onProgressUpdate: (data: ProgressUpdate) => void = () => {};
  onProcessingComplete: (data: any) => void = () => {};
  onProcessingError: (data: any) => void = () => {};
  onQueueUpdate: (data: any) => void = () => {};
  
  private fallbackToPolling() {
    // Implement HTTP polling fallback
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/processing/status-all/${this.userId}`);
        const updates = await response.json();
        updates.forEach(this.handleMessage.bind(this));
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 5000);
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

### Progress Update Components:
```jsx
const ProcessingProgressModal = ({ isVisible, jobs, onClose }) => {
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null);
  const [progressData, setProgressData] = useState<Map<string, ProgressUpdate>>(new Map());
  
  useEffect(() => {
    if (user?.id && isVisible) {
      const client = new WebSocketClient(user.id);
      
      client.onProgressUpdate = (data) => {
        setProgressData(prev => new Map(prev).set(data.jobId, data));
      };
      
      client.onProcessingComplete = (data) => {
        toast.success(`Video processing completed: ${data.videoTitle}`);
        // Handle completion logic
      };
      
      client.onProcessingError = (data) => {
        toast.error(`Processing failed: ${data.error}`);
      };
      
      setWsClient(client);
      
      return () => client.disconnect();
    }
  }, [user?.id, isVisible]);
  
  return (
    <Modal isOpen={isVisible} onClose={onClose}>
      <ModalHeader>
        <h2>Processing Progress</h2>
      </ModalHeader>
      
      <ModalContent>
        {Array.from(progressData.values()).map(job => (
          <ProcessingJobCard key={job.jobId} job={job} />
        ))}
      </ModalContent>
    </Modal>
  );
};

const ProcessingJobCard = ({ job }) => {
  const stageLabels = {
    'url_validation': 'Validating URL',
    'metadata_extraction': 'Getting video info',
    'transcript_generation': 'Generating transcript',
    'content_analysis': 'Analyzing content',
    'mindmap_generation': 'Creating mind map',
    'data_storage': 'Saving data',
    'indexing': 'Indexing for search',
    'completed': 'Completed'
  };
  
  return (
    <div className="bg-white rounded-lg p-4 shadow mb-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-semibold truncate">{job.videoTitle}</h3>
        <span className="text-sm text-gray-500">{job.progress}%</span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
        <div 
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${job.progress}%` }}
        />
      </div>
      
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600">
          {stageLabels[job.stage] || job.stage}
        </span>
        {job.estimatedCompletion && (
          <span className="text-gray-500">
            Est: {new Date(job.estimatedCompletion).toLocaleTimeString()}
          </span>
        )}
      </div>
      
      {job.error && (
        <div className="mt-2 text-red-600 text-sm">
          Error: {job.error}
        </div>
      )}
    </div>
  );
};
```

### Progress Update APIs:
```
/**
* WebSocket Progress Updates
* Send real-time progress updates via WebSocket connection
* Input Parameters: user_id (string), progress_data (object)
* Return Parameters: None (WebSocket message)
* URL Address: WebSocket: /ws/{user_id}
* Request Method: WebSocket
**/

/**
* Processing Status Polling Fallback
* HTTP fallback for getting processing status when WebSocket unavailable
* Input Parameters: user_id (string)
* Return Parameters: ProcessingStatusList with all active jobs
* URL Address: /api/processing/status-all/{user_id}
* Request Method: GET
**/

/**
* Queue Position Updates
* Get current queue position and estimated wait times
* Input Parameters: user_id (string)
* Return Parameters: QueueStatus with position and estimates
* URL Address: /api/processing/queue-status/{user_id}
* Request Method: GET
**/
```

### Integration with Processing Pipeline:
```python
# Modified update_progress function from processing pipeline
async def update_progress(job: ProcessingJob, stage: ProcessingStage, progress: int):
    """Update job progress and notify frontend via WebSocket"""
    job.current_stage = stage
    job.progress_percentage = progress
    job.updated_at = datetime.utcnow()
    
    # Estimate completion time based on stage and historical data
    estimated_completion = calculate_estimated_completion(job, stage, progress)
    job.estimated_completion = estimated_completion
    
    # Update database
    await update_job_in_database(job)
    
    # Send real-time update to frontend via WebSocket
    progress_message = {
        "type": "progress_update",
        "jobId": job.id,
        "stage": stage.value,
        "progress": progress,
        "message": get_stage_message(stage),
        "estimatedCompletion": estimated_completion.isoformat() if estimated_completion else None,
        "videoTitle": job.video_title or "Processing..."
    }
    
    await websocket_manager.send_personal_message(job.user_id, progress_message)
```

## Definition of Done
- WebSocket connections work reliably with automatic reconnection
- Real-time progress updates are delivered to frontend without delays
- Connection fallback to HTTP polling works when WebSockets fail
- Progress visualization components display accurate status information
- Multiple concurrent job tracking works correctly per user
- Message queuing ensures no updates are lost for offline users
- Error handling provides clear feedback for connection and processing issues
- Performance remains acceptable with high numbers of concurrent users
- Background processing continues when user navigates or closes tab
- WebSocket security prevents unauthorized access to other users' updates