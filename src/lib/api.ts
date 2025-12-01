// Define missing types locally
interface ApiKeyDisplay {
  id: string;
  name: string;
  apiKey: string;
}

interface SecurityAuditLog {
  id: string;
  log: string;
  timestamp: string;
}

interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

type PipelineStage = 'pending' | 'processing' | 'completed' | 'failed';

// Rest of your code...

// Fix the 'success' property error
interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

// Example usage:
const response: ApiResponse<Document[]> = {
  data: [],
  success: true,
  message: 'Success',
};

// Fix the 'PipelineStage' type error
const pipelineStage: PipelineStage = 'pending';

// Rest of your code...