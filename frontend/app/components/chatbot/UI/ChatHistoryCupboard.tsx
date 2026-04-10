import { useContext, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion"
import { ChatContext, ChatRecord } from "@/app/context/chatbot/ChatContext";
import { wsSendAsync } from "@/app/utils/retryOpernation";
import NewChatIcon from "../../../../icons/new_chat_icon.svg"
import ImageIcon from "../../../../icons/image_icon.svg"
import { X, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";

import { useState, useCallback } from "react";
import { AlertTriangle, Trash2 } from "lucide-react";

const ChatHistoryCupboard = () => {

    const router = useRouter()

    const handleLogout = () => {
        Cookies.remove('auth_token');
        localStorage.clear();
        router.push('/pages/auth');
    };
    const { wsRef, openChatHistoryDialogueBox, setOpenChatHistoryDialogueBox, setSelectedSessionID, chatHistory, currentMode, sessionID } = useContext(ChatContext)!
    const cupBoardRef = useRef<HTMLDivElement>(null)

    const [toasts, setToasts] = useState<{ id: number; message: string }[]>([])
    const [confirmState, setConfirmState] = useState<{ sessionId: string | null; title: string | null; userId: string | null } | null>(null)
    const toastCounter = useRef(0)

    const showToast = useCallback((message: string) => {
        const id = ++toastCounter.current;
        setToasts(prev => [...prev, { id, message }]);
        setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000);
    }, []);

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

    const getAllImages = () => {
        if (!wsRef.current) return
        const user = sessionStorage.getItem('user');
        let user_id = null
        if (user) {
            try {
                const userData = JSON.parse(user)
                user_id = userData.id;
            } catch (e) {
                console.error("Error parsing data:", e)
                return
            }
        }
        wsSendAsync(wsRef.current, {
            type: "get_images",
            user_id: user_id
        }).catch((error) => {
            console.error('Failed to send get_images request:', error);
        })
        setOpenChatHistoryDialogueBox(false)
    }

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
                return
            }
        }
        wsSendAsync(
            wsRef.current,
            {
                type: "session-init",
                session_id: "",
                user_id: user_id,
                mode: currentMode
            }).catch((error) => {
                console.error('Failed to send session-init request:', error);

            })
        setOpenChatHistoryDialogueBox(false)
    };

    return (
        <>

            <motion.div ref={cupBoardRef} transition={{ duration: 0.3, ease: "linear" }} initial={{ x: "-100%" }}
                animate={{ x: "0%" }}
                exit={{ x: "-100%" }} className={`h-svh p-2 absolute left-0 z-30 border-r bg-${backgroundTheme} border-${fontTheme}/10 min-w-60 w-max max-w-60 md:w-70 flex flex-col`}>

                <div className="mt-16"></div>
                <div className="flex flex-col gap-y-1">
                    <motion.div whileTap={{ scale: 0.99 }} whileHover={{ scale: 1.01 }} transition={{ duration: 0.4, ease: "linear" }} onClick={InitializeNewSession}
                        className={`cursor-pointer flex justify-between px-1.5 py-1.5 border-y border-${fontTheme}/10`}>
                        <p className={`switzer-500 text-sm tracking-tight text-${fontTheme}`}>New Chat</p>
                        <NewChatIcon className={`w-5 h-5 fill-current text-${fontTheme}/80 hover:text-${fontTheme}/90`} />
                    </motion.div>
                    <motion.div onClick={getAllImages}
                        whileTap={{ scale: 0.99 }}
                        whileHover={{ scale: 1.01 }} transition={{ duration: 0.4, ease: "linear" }}
                        className={`cursor-pointer flex justify-between px-1.5 py-1.5 border-b border-${fontTheme}/10`}>
                        <p className={`switzer-500 text-sm tracking-tight text-${fontTheme}`}>Images</p>
                        <ImageIcon className={`w-5 h-5 fill-current text-${fontTheme}/80 hover:text-${fontTheme}/90`} />
                    </motion.div>
                </div>
                <div className="mt-4 px-1">
                    <p className={`switzer-500 text-${fontTheme} text-sm tracking-tight`}>Chat history</p>
                </div>
                <motion.div className={`flex-1 grid grid-cols-1 gap-y-1 h-max max-h-120 ${currentMode === "normal" ? "overflow-y-auto" : "chat-history-cupboard-scrollbar"}`}>
                    {chatHistory && chatHistory?.length > 0 ? (
                        chatHistory?.map((chat: ChatRecord, index: number) => (
                            <motion.div
                                onClick={() => {
                                    setSelectedSessionID(chat.session_id);
                                    setOpenChatHistoryDialogueBox(false);
                                    // only send get_chat request if current session is different from required session
                                    if (chat.session_id != sessionID) {
                                        wsSendAsync(wsRef.current, {
                                            type: "get_chat",
                                            session_id: chat.session_id,
                                        });
                                    }
                                }}
                                whileHover={{ backgroundColor: "#ffffff0d" }}
                                key={chat.session_id || index}
                                className={`w-full h-max border-b border-${fontTheme}/10 px-1 py-1 flex flex-col gap-y-1 relative group cursor-pointer`}
                            >

                                <div
                                    className="flex justify-between"
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
                                        const user = sessionStorage.getItem('user');
                                        let user_id = null;
                                        if (user) {
                                            try { user_id = JSON.parse(user).id; }
                                            catch (err) { console.error(err); }
                                        }
                                        setConfirmState({ sessionId: chat.session_id, title: chat.title, userId: user_id });
                                    }}
                                    className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200 bg-red-500 hover:bg-red-600 text-white rounded-full p-1"
                                >
                                    <X size={12} />
                                </button>

                                <AnimatePresence>
                                    {confirmState?.sessionId === chat.session_id && (
                                        <motion.div
                                            initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}
                                            transition={{ duration: 0.15 }}
                                            onClick={e => e.stopPropagation()}
                                            className="mt-1 flex items-center gap-2 bg-red-950/60 border border-red-500/30 rounded-md px-2 py-1.5"
                                        >
                                            <Trash2 size={11} className="text-red-500 shrink-0" />
                                            <span className="switzer-500 text-[11px] text-red-300 flex-1">Delete {confirmState.title}?</span>
                                            <button onClick={() => {
                                                if (!wsRef.current) { showToast("Connection lost. Please refresh."); setConfirmState(null); return; }
                                                wsSendAsync(wsRef.current, {
                                                    type: "delete_session",
                                                    session_id: confirmState.sessionId,
                                                }).catch(() => showToast(`Error deleting "${confirmState.title}". Please try again.`));
                                                setConfirmState(null);
                                            }} className="text-[11px] switzer-600 text-red-400 hover:text-red-300 px-1">Yes</button>
                                            <button onClick={e => { e.stopPropagation(); setConfirmState(null); }}
                                                className="text-[11px] switzer-600 text-white/40 hover:text-white/70 px-1">No</button>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
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

                <div className={`mt-auto pt-2 border-t border-${fontTheme}/10`}>
                    <motion.div
                        whileTap={{ scale: 0.99 }} whileHover={{ scale: 1.01 }}
                        transition={{ duration: 0.4, ease: "linear" }}
                        onClick={handleLogout}
                        className={`w-full flex items-center cursor-pointer justify-between px-1.5 py-2 rounded-md`}
                    >
                        <p className={`switzer-500 text-sm tracking-tight text-${fontTheme}`}>Logout</p>
                        <LogOut className={`text-${fontTheme}/80 hover:text-${fontTheme}/90`} size={16} />
                    </motion.div>
                </div>

            </motion.div>
            <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
                <AnimatePresence>
                    {toasts.map(toast => (
                        <motion.div key={toast.id}
                            initial={{ opacity: 0, x: 60 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 60 }}
                            className="pointer-events-auto flex items-center gap-2.5 px-3.5 py-2.5 rounded-lg shadow-xl border bg-zinc-900 border-red-500/30 text-white max-w-xs"
                        >
                            <AlertTriangle size={14} className="text-red-400 shrink-0" />
                            <p className="switzer-500 text-[13px] flex-1">{toast.message}</p>
                            <button onClick={() => setToasts(p => p.filter(t => t.id !== toast.id))} className="text-white/30 hover:text-white/70"><X size={12} /></button>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </>

    )

}


export default ChatHistoryCupboard