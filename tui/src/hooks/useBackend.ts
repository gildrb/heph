import { useState, useEffect, useCallback, useRef } from "react";
import { BackendClient } from "../lib/client";
import type { Message, SessionInfo, ArmoryInfo, ServerMessage } from "../lib/types";
import { generateId } from "../lib/types";

interface UseBackendReturn {
  messages: Message[];
  session: SessionInfo | null;
  armory: ArmoryInfo | null;
  isConnected: boolean;
  isStreaming: boolean;
  error: string | null;
  pendingMessageId: string | null;
  sendMessage: (content: string) => void;
  switchArmory: (path: string) => void;
  createArmory: (path: string) => void;
  listSessions: () => void;
  resumeSession: (sessionId: string, armoryPath: string) => void;
  save: () => void;
  newChat: () => void;
  clearError: () => void;
}

export function useBackend(port = 8765): UseBackendReturn {
  const [client] = useState(() => new BackendClient(port));
  const [messages, setMessages] = useState<Message[]>([]);
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [armory, setArmory] = useState<ArmoryInfo | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingMessageId, setPendingMessageId] = useState<string | null>(null);
  const messageBufferRef = useRef<Map<string, string>>(new Map());

  useEffect(() => {
    client.connect().then(() => {
      setIsConnected(true);
    }).catch(() => {
      setError("Failed to connect to backend");
    });

    const unsubscribe = client.onMessage((msg: ServerMessage) => {
      switch (msg.type) {
        case "session_info":
          setSession({
            session_id: msg.session_id ?? "",
            model: msg.model ?? "",
            base_url: msg.base_url ?? "",
          });
          break;

        case "armory_info":
          setArmory({
            path: msg.armory_path ?? null,
            source_file_count: msg.source_file_count ?? 0,
          });
          break;

        case "message":
          setMessages((prev) => [...prev, {
            id: msg.message_id ?? generateId(),
            role: msg.role ?? "assistant",
            content: msg.content ?? "",
            timestamp: Date.now(),
          }]);
          break;

        case "message_chunk": {
          const id = msg.message_id ?? generateId();
          const buffer = messageBufferRef.current;
          const current = buffer.get(id) ?? "";
          buffer.set(id, current + (msg.content ?? ""));
          setMessages((prev) => {
            const existing = prev.findIndex((m) => m.id === id);
            if (existing >= 0) {
              const updated = [...prev];
              const existingMsg = updated[existing];
              if (existingMsg) {
                updated[existing] = { ...existingMsg, content: current + (msg.content ?? "") };
              }
              return updated;
            } else {
              return [...prev, {
                id,
                role: msg.role ?? "assistant",
                content: current + (msg.content ?? ""),
                timestamp: Date.now(),
              }];
            }
          });
          break;
        }

        case "message_done":
          setIsStreaming(false);
          messageBufferRef.current.delete(msg.message_id ?? "");
          break;

        case "error":
          setError(msg.error ?? "Unknown error");
          setIsStreaming(false);
          break;

        case "saved":
          break;
      }
    });

    const unsubConnection = client.onConnectionChange((connected: boolean) => {
      setIsConnected(connected);
      if (!connected) {
        setIsStreaming(false);
      }
    });

    return () => {
      unsubscribe();
      unsubConnection();
      client.disconnect();
    };
  }, [client]);

  const sendMessage = useCallback((content: string) => {
    const id = generateId();
    setPendingMessageId(id);
    setIsStreaming(true);
    messageBufferRef.current.set(id, "");
    client.sendMessage(content);
  }, [client]);

  const switchArmory = useCallback((path: string) => {
    client.switchArmory(path);
  }, [client]);

  const createArmory = useCallback((path: string) => {
    client.createArmory(path);
  }, [client]);

  const listSessions = useCallback(() => {
    client.listSessions();
  }, [client]);

  const resumeSession = useCallback((sessionId: string, armoryPath: string) => {
    client.resumeSession(sessionId, armoryPath);
  }, [client]);

  const save = useCallback(() => {
    client.save();
  }, [client]);

  const newChat = useCallback(() => {
    setMessages([]);
    client.newChat();
  }, [client]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    messages,
    session,
    armory,
    isConnected,
    isStreaming,
    error,
    pendingMessageId,
    sendMessage,
    switchArmory,
    createArmory,
    listSessions,
    resumeSession,
    save,
    newChat,
    clearError,
  };
}
