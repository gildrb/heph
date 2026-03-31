import { useState, useCallback } from "react";
import { useKeyboard } from "@opentui/react";
import type { SessionInfo } from "../lib/types";

interface ArmoryMenuProps {
  onClose: () => void;
  onOpenArmory: (path: string) => void;
  onCreateArmory: (path: string) => void;
  onResumeSession: (sessionId: string) => void;
  onNewChat: () => void;
  armoryPath: string | null;
}

const ARMORY_OPTIONS = [
  { name: "Open existing armory", description: "Attach a workspace and load its study context." },
  { name: "Create new armory", description: "Initialize a new workspace." },
  { name: "Resume saved chat", description: "Pick a saved conversation." },
  { name: "New chat", description: "Start a fresh chat." },
  { name: "Cancel", description: "Return to chat." },
];

export function ArmoryMenu({
  onClose,
  onOpenArmory,
  onCreateArmory,
  onResumeSession,
  onNewChat,
  armoryPath,
}: ArmoryMenuProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [mode, setMode] = useState<"menu" | "open" | "create">("menu");
  const [inputPath, setInputPath] = useState(armoryPath ?? "");

  useKeyboard(
    useCallback(
      (key) => {
        if (key.name === "escape") {
          if (mode === "menu") {
            onClose();
          } else {
            setMode("menu");
            setInputPath(armoryPath ?? "");
          }
          return;
        }

        if (mode !== "menu") {
          if (key.name === "enter") {
            if (inputPath.trim()) {
              if (mode === "open") {
                onOpenArmory(inputPath.trim());
              } else if (mode === "create") {
                onCreateArmory(inputPath.trim());
              }
              onClose();
            }
          }
          return;
        }

        switch (key.name) {
          case "up":
          case "k":
            setSelectedIndex((i) => Math.max(0, i - 1));
            break;
          case "down":
          case "j":
            setSelectedIndex((i) => Math.min(ARMORY_OPTIONS.length - 1, i + 1));
            break;
          case "enter":
            if (selectedIndex === 0) {
              setMode("open");
            } else if (selectedIndex === 1) {
              setMode("create");
            } else if (selectedIndex === 2) {
              // TODO: show session list
            } else if (selectedIndex === 3) {
              onNewChat();
              onClose();
            } else {
              onClose();
            }
            break;
        }
      },
      [mode, selectedIndex, inputPath, armoryPath, onClose, onOpenArmory, onCreateArmory, onNewChat]
    ),
    { release: false }
  );

  if (mode === "open") {
    return (
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
        <box border padding={2} width={60}>
          <text>Open Armory</text>
          <text fg="dim" paddingTop={1}>
            Enter path:
          </text>
          <input
            value={inputPath}
            onChange={setInputPath}
            placeholder="/path/to/armory"
            width={50}
            focused
          />
          <text fg="dim" paddingTop={1}>
            Enter to confirm, Esc to cancel
          </text>
        </box>
      </box>
    );
  }

  if (mode === "create") {
    return (
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
        <box border padding={2} width={60}>
          <text>Create Armory</text>
          <text fg="dim" paddingTop={1}>
            Enter path for new armory:
          </text>
          <input
            value={inputPath}
            onChange={setInputPath}
            placeholder="/path/to/new-armory"
            width={50}
            focused
          />
          <text fg="dim" paddingTop={1}>
            Enter to create, Esc to cancel
          </text>
        </box>
      </box>
    );
  }

  return (
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
      <box border padding={2} width={60}>
        <text>
          <strong>Armory</strong>
        </text>
        <box flexDirection="column" marginTop={1}>
          {ARMORY_OPTIONS.map((option, index) => (
            <box key={option.name} flexDirection="row" paddingY={1}>
              <text width={3} fg={index === selectedIndex ? "#00ff00" : "dim"}>
                {index === selectedIndex ? ">" : " "}
              </text>
              <text fg={index === selectedIndex ? "#ffffff" : "dim"}>
                {option.name}
              </text>
            </box>
          ))}
        </box>
        <text fg="dim" paddingTop={1}>
          j/k or arrows to navigate, Enter to select, Esc to cancel
        </text>
      </box>
    </box>
  );
}
