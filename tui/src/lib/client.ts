import { createWebSocketUrl, type ServerMessage, type ClientMessage } from "./types";

export type MessageHandler = (msg: ServerMessage) => void;

export class BackendClient {
  private ws: WebSocket | null = null;
  private port: number;
  private handlers: Set<MessageHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageBuffer: ClientMessage[] = [];
  private isConnected = false;

  constructor(port = 8765) {
    this.port = port;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = createWebSocketUrl(this.port);
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        while (this.messageBuffer.length > 0) {
          const msg = this.messageBuffer.shift();
          if (msg) this.send(msg);
        }
        resolve();
      };

      this.ws.onmessage = (event) => {
        try {
          const msg: ServerMessage = JSON.parse(event.data);
          this.handlers.forEach((handler) => handler(msg));
        } catch {
          console.error("Failed to parse server message");
        }
      };

      this.ws.onclose = () => {
        this.isConnected = false;
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        if (!this.isConnected) {
          reject(error);
        }
      };
    });
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      return;
    }
    this.reconnectAttempts++;
    setTimeout(() => {
      this.connect().catch(() => {});
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  send(msg: ClientMessage) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(msg));
    } else {
      this.messageBuffer.push(msg);
    }
  }

  onMessage(handler: MessageHandler): () => void {
    this.handlers.add(handler);
    return () => this.handlers.delete(handler);
  }

  sendMessage(content: string) {
    this.send({ type: "send_message", message: content });
  }

  switchArmory(path: string) {
    this.send({ type: "switch_armory", armory_path: path });
  }

  createArmory(path: string) {
    this.send({ type: "create_armory", armory_path: path });
  }

  listSessions() {
    this.send({ type: "list_sessions" });
  }

  resumeSession(sessionId: string) {
    this.send({ type: "resume_session", session_id: sessionId });
  }

  save() {
    this.send({ type: "save" });
  }

  newChat() {
    this.send({ type: "new_chat" });
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
