import { useState, ReactNode, Ref } from "react";
import { ChatContext, ChatRecord } from "@/app/context/chatbot/ChatContext";

interface ChatProviderProps {
  children: ReactNode;
  wsRef: React.Ref<WebSocket>;
  chatHistory: ChatRecord[] | null;
  setChatHistory: React.Dispatch<React.SetStateAction<ChatRecord[] | null>>;
}

const ChatProvider: React.FC<ChatProviderProps> = ({
  children,
  wsRef,
  chatHistory,
  setChatHistory,
}) => {
  const [hideExtraOptions, setHideExtraOptions] = useState<boolean>(true);
  const [selectedModel, setSelectedModel] = useState<string | null>(
    "Kimi-k2-instruct-0905"
  );
  const [active, setActive] = useState<boolean[]>([false, false, false]);
  const [hideModelBox, setHideModelBox] = useState<boolean>(true);

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
        selectedSessionID,
        setSelectedSessionID,
        openChatHistoryDialogueBox,
        setOpenChatHistoryDialogueBox,
        chatHistory,
        setChatHistory,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export default ChatProvider;
