import { AnimatePresence, easeInOut, motion } from "framer-motion";
import { ChatContext, ChatRecord } from "@/app/context/chatbot/ChatContext";
import { useContext, useEffect, useRef, useState } from "react";
import ChatHistory from "../../../../icons/history_icon.svg";
import { X, Trash2, CheckCircle, Loader2 } from "lucide-react";
import { wsSendAsync } from "@/app/utils/retryOpernation";

const formatDateToDMY = (dateString: string | null): string => {
  const date = new Date(dateString || new Date());
  const day = date.getDate().toString().padStart(2, "0");
  const month = (date.getMonth() + 1).toString().padStart(2, "0");
  const year = date.getFullYear();

  return `${day}-${month}-${year}`;
};

const ChatHisoryDialogueBox = () => {
  const {
    chatHistory,
    setSelectedSessionID,
    openChatHistoryDialogueBox,
    setOpenChatHistoryDialogueBox,
    wsRef,
  } = useContext(ChatContext)!;
  const [translatePic, setTranslatePic] = useState<boolean | null>(null);

  type ToastState = {
  type: "deleting" | "deleted" | "deleting-all" | "deleted-all" | null;
  sessionTitle?: string;
};
  const [toast, setToast] = useState<ToastState>({ type: null });
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);

  const dialogueRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
  const handleSessionDeleted = () => {
    setToast(prev => ({ type: "deleted", sessionTitle: prev.sessionTitle }));
    setDeletingSessionId(null);
  };
  const handleAllDeleted = () => {
    setToast({ type: "deleted-all" });
  };
  window.addEventListener("tadabbur-session-deleted", handleSessionDeleted);
  window.addEventListener("tadabbur-all-sessions-deleted", handleAllDeleted);
  return () => {
    window.removeEventListener("tadabbur-session-deleted", handleSessionDeleted);
    window.removeEventListener("tadabbur-all-sessions-deleted", handleAllDeleted);
  };
}, []);

  useEffect(() => {
  if (toast.type === "deleted" || toast.type === "deleted-all") {
    const timer = setTimeout(() => {
      setToast({ type: null });
    }, 2500);
    return () => clearTimeout(timer);
  }
}, [toast.type]);

// toast reset when dialog close 
useEffect(() => {
  if (!openChatHistoryDialogueBox) {
    setToast({ type: null });
    setDeletingSessionId(null);
  }
}, [openChatHistoryDialogueBox]);

  useEffect(() => {

    if (!openChatHistoryDialogueBox) return;
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        dialogueRef.current &&
        !dialogueRef.current.contains(e.target as Node)
      ) {
        setOpenChatHistoryDialogueBox(false);
      }
    };

    document.addEventListener("click", handleOutsideClick);

    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [openChatHistoryDialogueBox, setOpenChatHistoryDialogueBox]);

  useEffect(() => {
    if (openChatHistoryDialogueBox) {
      const user = localStorage.getItem('user');
      let user_id = null;
      if (user) {
        try {
          const userData = JSON.parse(user);
          user_id = userData.id;
        } catch (e) {
          console.error("Error parsing user data:", e);
        }
      }
      wsSendAsync(wsRef.current, {
        type: "chat_history",
        user_id: user_id,
      });
    }
  }, [openChatHistoryDialogueBox, wsRef]);

const handleDeleteSession = (e: React.MouseEvent, chat: ChatRecord) => {
  e.stopPropagation();
  setDeletingSessionId(chat.session_id);
  setToast({ type: "deleting", sessionTitle: chat.title ?? undefined });
  const user = localStorage.getItem("user");
  let user_id = null;
  if (user) {
    try { const userData = JSON.parse(user); user_id = userData.id; }
    catch (e) { console.error("Error parsing user data:", e); }
  }

  const pending = JSON.parse(localStorage.getItem("tadabbur_pending_deletes") || "[]");
  pending.push({ type: "delete_session", user_id, session_id: chat.session_id });
  localStorage.setItem("tadabbur_pending_deletes", JSON.stringify(pending));
  
  wsSendAsync(wsRef.current, {
    type: "delete_session",
    user_id,
    session_id: chat.session_id,
  });
  
};

const handleDeleteAll = () => {
  setToast({ type: "deleting-all" });
  const user = localStorage.getItem("user");
  let user_id = null;
  if (user) {
    try { const userData = JSON.parse(user); user_id = userData.id; }
    catch (e) { console.error("Error parsing user data:", e); }
  }
  localStorage.setItem("tadabbur_pending_deletes", JSON.stringify([
    { type: "delete_all_sessions",
      user_id 
    }
  ]));
  wsSendAsync(wsRef.current, { type: "delete_all_sessions", user_id });
};

  if (!openChatHistoryDialogueBox) return null;

  return (
    <motion.div
      initial={{ backdropFilter: "blur(0px)", opacity: 0 }}
      animate={{ backdropFilter: "blur(6px)", opacity: 1 }}
      exit={{ backdropFilter: "blur(0px)", opacity: 0 }}
      transition={{ duration: 0.4, ease: easeInOut }}
      className="w-screen h-screen absolute inset-0 flex justify-center items-center z-10"
    >
    <AnimatePresence>
  {toast.type && (
    <motion.div
      key="toast"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      transition={{ duration: 0.25 }}
      className="absolute top-6 z-50 flex items-center gap-x-3 px-4 py-3 rounded-xl shadow-xl border"
      style={{
        background: toast.type === "deleted" || toast.type === "deleted-all" ? "#f0fdf4" : "#fffbeb",
        borderColor: toast.type === "deleted" || toast.type === "deleted-all" ? "#bbf7d0" : "#fde68a",
      }}
    >
      {toast.type === "deleting" || toast.type === "deleting-all" ? (
        <Loader2 size={18} className="animate-spin text-amber-500 shrink-0" />
      ) : (
        <CheckCircle size={18} className="text-green-500 shrink-0" />
      )}
      <p className="switzer-500 text-sm" style={{
        color: toast.type === "deleted" || toast.type === "deleted-all" ? "#15803d" : "#92400e"
      }}>
        {toast.type === "deleting" && `Deleting "${toast.sessionTitle}"...`}
        {toast.type === "deleted" && `"${toast.sessionTitle}" deleted successfully!`}
        {toast.type === "deleting-all" && "Deleting all sessions..."}
        {toast.type === "deleted-all" && "All sessions deleted successfully!"}
      </p>
    </motion.div>
  )}
</AnimatePresence>
      <div
      
        ref={dialogueRef}
        className="w-[95%] max-w-130 h-120 p-2 bg-white border border-gray-500/5 shadow-lg rounded-md "
      >
        <div className="flex flex-col gap-y-2 h-120">
          <div className="w-full h-[45%]">
            <motion.div
              initial={{ x: -10 }}
              animate={{ x: 0 }}
              transition={{ duration: 0.3 }}
              className="h-full flex gap-x-2 justify-center items-center backdrop-blur-xl rounded-md px-4 relative border border-black/5"
            >
              <motion.div
                onMouseOver={() => {
                  setTranslatePic(true);
                }}
                onMouseLeave={() => {
                  setTranslatePic(false);
                }}
                animate={{ y: translatePic ? -10 : 0 }}
                transition={{ duration: 0.5, ease: easeInOut }}
                className="bg-Quran-2 bg-cover bg-center cursor-pointer w-1/2 rounded-md h-5/6"
              ></motion.div>
              <motion.div
                onMouseOver={() => {
                  setTranslatePic(true);
                }}
                onMouseLeave={() => {
                  setTranslatePic(false);
                }}
                animate={{ y: translatePic ? 10 : 0 }}
                transition={{ duration: 0.5, ease: easeInOut }}
                className="bg-aqsa bg-cover w-1/2 rounded-md h-5/6 cursor-pointer"
              ></motion.div>
            </motion.div>
          </div>
          <div className="flex flex-col gap-y-2 w-full h-[60%] relative overflow-x-clip">
            <div className="switzer-600 text-3xl tracking-tighter flex justify-between items-center-safe">
              <p>Lean Quran with Ease </p>
              <div className="w-7 h-7 rounded-md border border-black/5 flex justify-center items-center">
                <ChatHistory className="w-5 h-5 fill-current text-black/80" />
              </div>
            </div>
            <div className="flex flex-col gap-y-1">
              <div className="px-1 flex justify-between items-center">
                <p className="switzer-600 tracking-tighter text-black/50 text-sm">
                  Chat history
                </p>
                {chatHistory && chatHistory.length > 0 && (
                  <button
                  onClick={handleDeleteAll}
                  disabled={toast.type === "deleting-all" || toast.type === "deleting"}
                  className="flex items-center gap-x-1.5 switzer-500 text-xs text-red-500 hover:text-red-700 underline disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {toast.type === "deleting-all" ? (
                    <Loader2 size={11} className="animate-spin" />
                  ) : (
                    <Trash2 size={11} />
                  )}
                  Delete All
                </button>
                
                )}
              </div>
              <motion.div className="grid grid-cols-1 gap-2 px-1 overflow-y-auto h-45">
                {chatHistory && chatHistory?.length > 0 ? (
                  chatHistory?.map((chat: ChatRecord, index: number) => (
                    <motion.div
                      onClick={() => {
                        setSelectedSessionID(chat.session_id);
                        setOpenChatHistoryDialogueBox(false);
            
                        wsSendAsync(wsRef.current, {
                          type: "get_chat",
                          session_id: chat.session_id,
                        });
                      }}
                      whileHover={{ scale: 1.01 }}
                      transition={{ duration: 0.2 }}
                      key={chat.session_id || index}
                      className="w-full bg-black shadow-md h-max border border-black/10 rounded-md px-2 py-1 flex flex-col gap-y-1 relative group"
                    >
                      <div
                        className="flex justify-between cursor-pointer"

                      >
                        <p className="switzer-500 text-sm text-white tracking-tight">
                          {chat.title}
                        </p>
                        <p className="switzer-500 text-sm text-white/70 tracking-tight">
                          {formatDateToDMY(chat.created_at)}
                        </p>
                      </div>
                      <p
                        className="switzer-500 text-sm text-white/70 cursor-pointer"
                      >
                        {chat.description}
                      </p>
                      {deletingSessionId === chat.session_id ? (
                    <div className="absolute top-1.5 right-1.5">
                      <Loader2 size={14} className="animate-spin text-white/70" />
                    </div>
                  ) : (
                    <button
                      onClick={(e) => handleDeleteSession(e, chat)}
                      className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-red-500 hover:bg-red-600 text-white rounded-full p-1"
                    >
                      <X size={12} />
                    </button>
                  )}


                    </motion.div>
                  ))
                ) : (
                  <div className="flex justify-center items-center">
                    <p className="switzer-500 text-sm text-black/50">
                      No chat history.
                    </p>
                  </div>
                )}
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export { ChatHisoryDialogueBox };