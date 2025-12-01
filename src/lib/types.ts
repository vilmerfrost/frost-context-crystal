export type ConversationSource = "chatgpt" | "claude" | "perplexity" | "moonshot" | "deepseek" | "manual";

export type PipelineStage = "initializing" | "extraction" | "compression" | "verification" | "optimization" | "completed" | "failed";

// Denna saknades och orsakade kraschen
export type ProcessingStatus = PipelineStage;

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: number;
  model?: string;
}

export interface Conversation {
  id: string;
  source: ConversationSource;
  extracted_at: number;
  messages: Message[];
  metadata?: {
    title?: string;
    model?: string;
    total_tokens?: number;
  };
}

// Dessa saknades också
export interface Document {
  id: string;
  content: string;
  metadata: Record<string, any>;
}

export interface ApiResponse<T> {
  data: T;
  error?: string;
  status: number;
}

export interface PipelineStatus {
  id: string;
  conversation_id: string;
  stage: PipelineStage;
  progress: number;
  current_step?: string;
  error?: string;
  started_at: number;
  completed_at?: number;
  metrics?: PipelineMetrics;
}

export interface PipelineMetrics {
  original_tokens: number;
  compressed_tokens: number;
  compression_ratio: number;
  information_density_ratio: number;
  grounding_score: number;
  estimated_cost: number;
  time_elapsed: number;
}

export interface CompressionResult {
  compressed_content: string;
  facts_extracted: number;
  discarded_tokens: number;
  pass1_output?: string;
  pass2_output?: string;
}

export interface VerificationResult {
  claims_checked: number;
  claims_verified: number;
  grounding_score: number;
  corrections: VerificationCorrection[];
}

export interface VerificationCorrection {
  original_claim: string;
  corrected_claim: string;
  confidence: number;
  source_reference?: string;
}

export interface OptimizedPrompt {
  system_instruction: string;
  critical_constraints: string;
  compressed_history: string;
  state_snapshot: string;
  total_tokens: number;
}

export interface ApiKey {
  provider: string;
  key: string;
  is_valid: boolean;
  last_checked?: number;
}

export interface ExtractionConfig {
  source: ConversationSource;
  url?: string;
  include_metadata: boolean;
  max_messages?: number;
}
