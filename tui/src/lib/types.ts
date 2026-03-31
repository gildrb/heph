export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export interface ArmoryInfo {
  path: string | null;
  source_file_count: number;
}

export interface SessionInfo {
  session_id: string;
  model: string;
  base_url: string;
}

export interface ServerMessage {
  type: "session_info" | "armory_info" | "message" | "message_chunk" | "message_done" | "error" | "saved";
  session_id?: string;
  model?: string;
  base_url?: string;
  armory_path?: string | null;
  source_file_count?: number;
  message_id?: string;
  role?: "user" | "assistant";
  content?: string;
  error?: string;
}

export interface ClientMessage {
  type: "send_message" | "switch_armory" | "create_armory" | "list_sessions" | "resume_session" | "save" | "new_chat";
  armory_path?: string;
  message?: string;
  session_id?: string;
}

export function createWebSocketUrl(port: number = 8765): string {
  return `ws://localhost:${port}`;
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}
