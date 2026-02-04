import { easeIn, easeInOut, motion } from "framer-motion";
import { ChatContext, ChatRecord } from "@/app/context/chatbot/ChatContext";
import { useContext, useEffect, useRef, useState } from "react";
import ChatHistory from "../../../../icons/history_icon.svg";
import { X } from "lucide-react";
import { useRouter } from "next/navigation";

const formatDateToDMY = (dateString: string | null): string => {
  const date = new Date(dateString || new Date());
  const day = date.getDate().toString().padStart(2, "0");
  const month = (date.getMonth() + 1).toString().padStart(2, "0"); // Months are 0-indexed
  const year = date.getFullYear();

  return `${day}-${month}-${year}`;
};

const ChatHisoryDialoguseBox = () => {
  const {
    chatHistory,
    setChatHistory,
    setSelectedSessionID,
    openChatHistoryDialogueBox,
    setOpenChatHistoryDialogueBox,
    wsRef,
    userId,
  } = useContext(ChatContext);
  const [translatePic, setTranslatePic] = useState<boolean | null>(null);
  const dialogueRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

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
      const user = sessionStorage.getItem('user');
      let user_id = null;
      if (user) {
        try {
          const userData = JSON.parse(user);
          user_id = userData.id;
        } catch (e) {
          console.error("Error parsing user data:", e);
        }
      }
      wsRef.current?.send(
        JSON.stringify({
          type: "chat_history",
          user_id: user_id,
        })
      );
    }
  }, [openChatHistoryDialogueBox, wsRef]);

  if (!openChatHistoryDialogueBox) return null;

  return (
    <motion.div
      initial={{ backdropFilter: "blur(0px)", opacity: 0 }}
      animate={{ backdropFilter: "blur(6px)", opacity: 1 }}
      exit={{ backdropFilter: "blur(0px)", opacity: 0 }}
      transition={{ duration: 0.4, ease: easeInOut }}
      className="w-screen h-screen absolute inset-0 flex justify-center items-center z-10"
    >
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
                    onClick={() => {
                      if (window.confirm("Are you sure you want to delete all chat history?")) {
                        const user = sessionStorage.getItem('user');
                        let user_id = null;
                        if (user) {
                          try {
                            const userData = JSON.parse(user);
                            user_id = userData.id;
                          } catch (e) {
                            console.error("Error parsing user data:", e);
                          }
                        }
                        wsRef.current?.send(
                          JSON.stringify({
                            type: "delete_all_sessions",
                            user_id: user_id,
                          })
                        );
                      }
                    }}
                    className="switzer-500 text-xs text-red-500 hover:text-red-700 underline"
                  >
                    Delete All
                  </button>
                )}
              </div>
              <motion.div className="grid grid-cols-1 gap-2 px-1 overflow-y-auto h-45">
                {chatHistory ? (
                  chatHistory?.map((chat: ChatRecord, index: number) => (
                    <motion.div
                      whileHover={{ scale: 1.01 }}
                      transition={{ duration: 0.2 }}
                      key={chat.session_id || index}
                      className="w-full bg-black shadow-md h-max border border-black/10 rounded-md px-2 py-1 flex flex-col gap-y-1 relative group"
                    >
                      <div
                        className="flex justify-between cursor-pointer"
                        onClick={() => {
                          setSelectedSessionID(chat.session_id);
                          setOpenChatHistoryDialogueBox(false);
                          // wsRef.current?.send(
                          //   JSON.stringify({
                          //     type: "get_chat",
                          //     session_id: chat.session_id,
                          //     user_id: userId,
                          //   })
                          // );
                          router.push(`/pages/chatbot?session_id=${chat.session_id}`);
                        }}
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
                        onClick={() => {
                          setSelectedSessionID(chat.session_id);
                          setOpenChatHistoryDialogueBox(false);
                          // wsRef.current?.send(
                          //   JSON.stringify({
                          //     type: "get_chat",
                          //     session_id: chat.session_id,
                          //     user_id: userId,
                          //   })
                          // );
                          router.push(`/pages/chatbot?session_id=${chat.session_id}`);
                        }}
                      >
                        {chat.description}
                      </p>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (window.confirm(`Are you sure you want to delete "${chat.title}"?`)) {
                            const user = sessionStorage.getItem('user');
                            let user_id = null;
                            if (user) {
                              try {
                                const userData = JSON.parse(user);
                                user_id = userData.id;
                              } catch (e) {
                                console.error("Error parsing user data:", e);
                              }
                            }
                            wsRef.current?.send(
                              JSON.stringify({
                                type: "delete_session",
                                user_id: user_id,
                                session_id: chat.session_id,
                              })
                            );
                          }
                        }}
                        className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-red-500 hover:bg-red-600 text-white rounded-full p-1"
                      >
                        <X size={12} />
                      </button>
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

export { ChatHisoryDialoguseBox };
