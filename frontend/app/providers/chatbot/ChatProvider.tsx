import { useState, ReactNode, Ref } from "react";
import { ChatContext, ChatRecord } from "@/app/context/chatbot/ChatContext";
import { Dispatch, SetStateAction } from "react";

interface ChatProviderProps {
  children: ReactNode;
  wsRef: React.Ref<WebSocket>;
  chatHistory: ChatRecord[] | null;
  setChatHistory: React.Dispatch<React.SetStateAction<ChatRecord[] | null>>;
  sessionID: string | null;
  messages: any;      
  setMessages: any;
  attachedFile: File | null;
  setAttachedFile: Dispatch<SetStateAction<File | null>>;
}

const ChatProvider: React.FC<ChatProviderProps> = ({
  children,
  wsRef,
  chatHistory,
  setChatHistory,
  sessionID,
  messages,
  setMessages,
  attachedFile,
  setAttachedFile,
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
  const [reportedMessageInfo, setReportedMessageInfo] = useState<{
    messageID: string;
  } | null>(null);

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
        attachedFile,
        setAttachedFile,
        selectedSessionID,
        setSelectedSessionID,
        openChatHistoryDialogueBox,
        setOpenChatHistoryDialogueBox,
        chatHistory,
        setChatHistory,
<<<<<<< HEAD
        reportedMessageInfo,
        setReportedMessageInfo,
=======
        sessionID,
        messages,
        setMessages,
>>>>>>> 0a9fd875e9285f0bbd715f6ad16060e0c201aa0a
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export default ChatProvider;
