import { z } from "zod";

export const apiKeySchema = z.object({
  service_name: z.string().min(1, "Service name is required"),
  api_key: z.string().min(10, "API key must be at least 10 characters"),
});

export const openaiKeySchema = z.object({
  service_name: z.literal("openai"),
  api_key: z.string().regex(/^sk-[A-Za-z0-9]{48}$/, "Invalid OpenAI API key format"),
});

export const anthropicKeySchema = z.object({
  service_name: z.literal("anthropic"),
  api_key: z.string().regex(/^sk-ant-[A-Za-z0-9-]{95}$/, "Invalid Anthropic API key format"),
});

export const supabaseKeySchema = z.object({
  service_name: z.literal("supabase"),
  api_key: z.string().min(30, "Invalid Supabase API key format"),
});

export type ApiKeyInput = z.infer<typeof apiKeySchema>;