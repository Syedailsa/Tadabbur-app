import { useContext, useEffect, useRef } from "react";
import { motion } from "framer-motion"
import { ChatContext, ChatRecord } from "@/app/context/chatbot/ChatContext";
import { wsSendAsync } from "@/app/utils/retryOpernation";
import NewChatIcon from "../../../../icons/new_chat_icon.svg"
import { X } from "lucide-react";

const ChatHistoryCupboard = () => {

    const { wsRef, openChatHistoryDialogueBox, setOpenChatHistoryDialogueBox, setSelectedSessionID, chatHistory, currentMode } = useContext(ChatContext)!
    const cupBoardRef = useRef<HTMLDivElement>(null)

    const backgroundTheme = currentMode === "normal" ? "white" : "black"
    const fontTheme = currentMode === "normal" ? "black" : "white"

    useEffect(() => {
        if (!openChatHistoryDialogueBox) return;
        const handleOutsideClick = (e: MouseEvent) => {
            if (
                cupBoardRef.current &&
                !cupBoardRef.current.contains(e.target as Node)
            ) {
                setOpenChatHistoryDialogueBox(false);
            }
        };

        document.addEventListener("click", handleOutsideClick);

        return () => {
            document.removeEventListener("click", handleOutsideClick);
        };
    }, [openChatHistoryDialogueBox, setOpenChatHistoryDialogueBox]);


    const InitializeNewSession = () => {
        if (!wsRef.current) return;

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
        wsSendAsync(
            wsRef.current,
            {
                type: "session-init",
                session_id: "",
                user_id: user_id,
                mode: currentMode
            }).catch(() => { })
        setOpenChatHistoryDialogueBox(false)

    };


    return (
        <motion.div ref={cupBoardRef} transition={{ duration: 0.3, ease: "linear" }} initial={{ x: "-100%" }}
            animate={{ x: "0%" }}
            exit={{ x: "-100%" }} className={`h-screen p-2 absolute left-0 z-20 border-r bg-${backgroundTheme} border-${fontTheme}/10 min-w-60 w-max max-w-60 md:w-70`}>

            <div className="mt-16"></div>
            <div className="px-2 flex justify-between">
                <p className="switzer-600 text-white tracking-tight">Chat history</p>
                <div onClick={InitializeNewSession}
                    className="cursor-pointer">
                    <NewChatIcon className={`w-5 h-5 fill-current text-${fontTheme}/80 hover:text-${fontTheme}/90`} />
                </div>
            </div>
            <motion.div className={`grid grid-cols-1 gap-y-1 h-max max-h-120 ${currentMode === "normal" ? "overflow-y-auto" : "chat-history-cupboard-scrollbar"}`}>
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
                            whileHover={{ backgroundColor: "#ffffff0d" }}
                            key={chat.session_id || index}
                            className={`w-full h-max border-b border-${fontTheme}/10 px-2 py-1 flex flex-col gap-y-1 relative group`}
                        >

                            <div
                                className="flex justify-between cursor-pointer"

                            >
                                <p className={`switzer-500 text-sm text-${fontTheme} tracking-tight`}>
                                    {index + 1}. {chat.title}
                                </p>
                            </div>
                            <p
                                className={`switzer-500 text-[13px] text-${fontTheme}/70 cursor-pointer`}
                            >
                                {chat.description}
                            </p>
                            {/* <p className="switzer-500 text-sm text-white/70 tracking-tight">
                                    {formatDateToDMY(chat.created_at)}
                                </p> */}

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
                                        wsSendAsync(wsRef.current, {
                                            type: "delete_session",
                                            user_id: user_id,
                                            session_id: chat.session_id,
                                        });
                                    }
                                }}
                                className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-red-500 hover:bg-red-600 text-white rounded-full p-1"
                            >
                                <X size={12} />
                            </button>
                        </motion.div>
                    ))
                ) : (
                    <motion.div
                        className="px-2 py-1"
                    >
                        <p className={`switzer-500 text-sm text-${fontTheme}/70`}>
                            No previous chats.
                        </p>
                    </motion.div>
                )}
            </motion.div>

        </motion.div>
    )

}


export default ChatHistoryCupboard











