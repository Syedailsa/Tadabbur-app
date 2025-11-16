import { easeIn, easeInOut, motion } from "framer-motion";
import { ChatContext, ChatRecord } from "@/app/context/chatbot/ChatContext";
import { useContext, useEffect, useRef, useState } from "react";
import { dummyChatHistory } from "@/static/data";
import ChatHistory from "../../../../icons/history_icon.svg";

const ChatHisoryDialoguseBox = () => {
  const {
    chatHistory,
    setChatHistory,
    setSelectedSessionID,
    openChatHistoryDialogueBox,
    setOpenChatHistoryDialogueBox,
  } = useContext(ChatContext);
  const [translatePic, setTranslatePic] = useState<boolean | null>(null);
  const dialogueRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setChatHistory(dummyChatHistory);
  }, []);

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

  if (!openChatHistoryDialogueBox) return null;
  // useEffect(() => {
  //     if (!active) return;
  //     const handleOutsideClick = (e: MouseEvent) => {
  //       if (
  //         controlRef.current &&
  //         !controlRef.current.contains(e.target as Node)
  //       ) {
  //         setActive(false);
  //       }
  //     };
  //     document.addEventListener("click", handleOutsideClick);

  //     return () => {
  //       document.removeEventListener("click", handleOutsideClick);
  //     };
  //   }, [active, setActive]);
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
              <div className="px-1 flex justify-between">
                <p className="switzer-600 tracking-tighter text-black/50 text-sm">
                  Chat history
                </p>
              </div>
              <motion.div className="grid grid-cols-1 gap-2 px-1 overflow-y-auto h-45">
                {chatHistory?.map((chat: ChatRecord, index: number) => (
                  <motion.div
                    whileHover={{ scale: 1.01 }}
                    onClick={() => {
                      setSelectedSessionID(chat.session_id);
                      setOpenChatHistoryDialogueBox(false);
                    }}
                    whileTap={{ scale: 0.98, transition: { duration: 0.5 } }}
                    transition={{ duration: 0.2 }}
                    key={chat.session_id || index}
                    className="w-full bg-black cursor-pointer shadow-md h-max border border-black/10 rounded-md px-2 py-1 flex flex-col gap-y-1"
                  >
                    <div className="flex justify-between">
                      <p className="switzer-500 text-sm text-white tracking-tight">
                        {chat.title}
                      </p>
                      <p className="switzer-500 text-sm text-white/70 tracking-tight">
                        {chat.date}
                      </p>
                    </div>
                    <p className="switzer-500 text-sm text-white/70">
                      {chat.description}
                    </p>
                  </motion.div>
                ))}
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export { ChatHisoryDialoguseBox };
