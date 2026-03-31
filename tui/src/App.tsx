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

  useKeyboard(
    useCallback(
      (key) => {
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
        if (key.name === "enter" && !backend.isStreaming && !showArmoryMenu) {
          if (inputValue.trim()) {
            backend.sendMessage(inputValue);
            setInputValue("");
          }
        }
      },
      [backend, inputValue, renderer, showArmoryMenu]
    ),
    { release: false }
  );

  const prompt = backend.armory?.path
    ? `${backend.armory.path.split("/").pop()}> `
    : "> ";

  return (
    <box flexDirection="column" width="100%" height="100%">
      <Header
        session={backend.session}
        armory={backend.armory}
        isConnected={backend.isConnected}
        isStreaming={backend.isStreaming}
      />
      <MessageList messages={backend.messages} isStreaming={backend.isStreaming} />
      <ChatInput
        onSend={backend.sendMessage}
        disabled={backend.isStreaming || showArmoryMenu}
        prompt={prompt}
      />
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
          backgroundColor="rgba(0,0,0,0.8)"
          justifyContent="center"
          alignItems="center"
        >
          <box border padding={2} backgroundColor="#2a1a1a">
            <text fg="red">Error: {backend.error}</text>
            <text fg="dim" paddingTop={1}>
              Press any key to dismiss
            </text>
          </box>
        </box>
      )}
    </box>
  );
}
