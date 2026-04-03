import { useState, useCallback } from "react";
import { useKeyboard, useRenderer } from "@opentui/react";
import { useBackend } from "./hooks/useBackend";
import { Header } from "./components/Header";
import { MessageList } from "./components/MessageList";
import { ChatInput } from "./components/ChatInput";
import { ArmoryMenu } from "./components/ArmoryMenu";

export function App() {
  const renderer = useRenderer();
  const backend = useBackend(8765);
  const [showArmoryMenu, setShowArmoryMenu] = useState(false);
  const [inputValue, setInputValue] = useState("");

  const handleSend = useCallback((text: string) => {
    if (text.trim() && !backend.isStreaming) {
      backend.sendMessage(text.trim());
      setInputValue("");
    }
  }, [backend]);

  useKeyboard(
    useCallback(
      (key) => {
        if (backend.error) {
          backend.clearError();
          return;
        }
        if (key.name === "escape") {
          if (showArmoryMenu) {
            setShowArmoryMenu(false);
            return;
          }
          backend.save();
          renderer.destroy();
          return;
        }
        if (key.ctrl && key.name === "s") {
          backend.save();
        }
        if (key.ctrl && key.name === "a") {
          setShowArmoryMenu(true);
        }
        if (key.name === "enter" && !key.shift && !backend.isStreaming && !showArmoryMenu) {
          if (inputValue.trim()) {
            backend.sendMessage(inputValue.trim());
            setInputValue("");
          }
        }
      },
      [backend, inputValue, renderer, showArmoryMenu]
    ),
    { release: false }
  );

  const prompt = backend.armory?.path
    ? `${backend.armory.path.split("/").pop()} › `
    : "› ";

  return (
    <box flexDirection="column" width="100%" height="100%" backgroundColor="#0d0d0d">
      <box borderBottom>
        <Header
          session={backend.session}
          armory={backend.armory}
          isConnected={backend.isConnected}
          isStreaming={backend.isStreaming}
        />
      </box>
      <MessageList messages={backend.messages} isStreaming={backend.isStreaming} />
      <box borderTop paddingX={2} paddingY={1} backgroundColor="#141414">
        <ChatInput
          value={inputValue}
          onChange={setInputValue}
          onSend={handleSend}
          disabled={backend.isStreaming || showArmoryMenu}
          prompt={prompt}
        />
      </box>
      {showArmoryMenu && (
        <ArmoryMenu
          onClose={() => setShowArmoryMenu(false)}
          onOpenArmory={backend.switchArmory}
          onCreateArmory={backend.createArmory}
          onResumeSession={backend.resumeSession}
          onNewChat={backend.newChat}
          armoryPath={backend.armory?.path ?? null}
        />
      )}
      {backend.error && (
        <box
          position="absolute"
          top={0}
          left={0}
          right={0}
          bottom={0}
          backgroundColor="rgba(0,0,0,0.85)"
          justifyContent="center"
          alignItems="center"
        >
          <box border padding={3} backgroundColor="#1a0a0a" borderColor="#dc2626">
            <text fg="#dc2626" bold>Error</text>
            <text fg="#e5e5e5" paddingTop={1}>{backend.error}</text>
            <text fg="#737373" paddingTop={1}>Press any key to dismiss</text>
          </box>
        </box>
      )}
    </box>
  );
}
