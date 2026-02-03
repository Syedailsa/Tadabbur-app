import { useState, ReactNode, Ref } from "react";
import { ChatContext, ChatRecord } from "@/app/context/chatbot/ChatContext";
import { Dispatch, SetStateAction } from "react";
import { ChatRecordType } from "@/app/utils/types";

interface ChatProviderProps {
  children: ReactNode;
  wsRef: React.Ref<WebSocket>;
  chatHistory: ChatRecordType[] | null;
  setChatHistory: React.Dispatch<React.SetStateAction<ChatRecordType[] | null>>;
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
  const [reportedMessageID, setReportedMessageID] = useState<{
    messageID: string;
  } | null>(null);
  const [userId, setUserId] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      const user = sessionStorage.getItem('user');
      if (user) {
        try {
          const userData = JSON.parse(user);
          return userData.id;
        } catch {
          return null;
        }
      }
    }
    return null;
  });

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
        reportedMessageID,
        setReportedMessageID,
        attachedFile,
        setAttachedFile,
        sessionID,
        messages,
        setMessages,
        userId,
        setUserId,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export default ChatProvider;
