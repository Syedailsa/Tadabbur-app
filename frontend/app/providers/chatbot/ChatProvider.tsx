import { useState, ReactNode, Ref } from "react";
import { ChatContext } from "@/app/context/chatbot/ChatContext";

interface ChatProviderProps {
  children: ReactNode;
  wsRef: React.Ref<WebSocket>;
}

const ChatProvider: React.FC<ChatProviderProps> = ({ children, wsRef }) => {
  const [hideExtraOptions, setHideExtraOptions] = useState<boolean>(true);
  const [selectedModel, setSelectedModel] = useState<string | null>(
    "Kimi-k2-instruct-0905"
  );
  const [active, setActive] = useState<boolean[]>([false, false, false]);
  const [hideModelBox, setHideModelBox] = useState<boolean>(true);
  const [chatHistory, setChatHistory] = useState<
    { session_id: string; title: string } | null[] | null
  >(null);
  const [selectedSessionID, setSelectedSessionID] = useState<string | null>(
    null
  );

  const [openChatHistoryDialogueBox, setOpenChatHistoryDialogueBox] = useState<
    boolean | null
  >(false);

  return (
    <ChatContext.Provider
      value={{
        wsRef,
        hideExtraOptions,
        setHideExtraOptions,
        selectedModel,
        setSelectedModel,
        hideModelBox,
        setHideModelBox,
        active,
        setActive,
        chatHistory,
        setChatHistory,
        selectedSessionID,
        setSelectedSessionID,
        openChatHistoryDialogueBox,
        setOpenChatHistoryDialogueBox,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export default ChatProvider;
