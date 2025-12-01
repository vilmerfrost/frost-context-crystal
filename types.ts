// Define types instead of using 'any'
interface UserType {
  id: number;
  name: string;
}

interface MessageType {
  id: number;
  text: string;
  userId: number;
}

// API types for lib/api.ts
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface Document {
  id: string;
  name: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface ApiKeyDisplay {
  id: string;
  name: string;
  apiKey: string;
}

export interface SecurityAuditLog {
  id: string;
  log: string;
  timestamp: string;
}

export interface Toast {
  // Add Toast interface if it's missing
  message: string;
}

export type PipelineStage = 'pending' | 'processing' | 'completed' | 'failed';

// Example function to fix error TS2353
const exampleFunction = async (): Promise<ApiResponse<Document[]>> => {
  const response: ApiResponse<Document[]> = {
    data: [],
    success: true,
    message: 'Success',
  };

  // Add the 'success' property to the ApiResponse type
  return response;
};

// Example fix for error TS2322
const pipelineStage: PipelineStage = 'pending';