import { motion } from "framer-motion"
import { wsSendAsync } from "@/app/utils/retryOpernation"
import { useContext } from "react";
import { ChatContext } from "@/app/context/chatbot/ChatContext";

const HamBurger = () => {
    const { wsRef, openChatHistoryDialogueBox, setOpenChatHistoryDialogueBox, currentMode, responseBasedActions, requestExists, setResponseBasedActions, showFriendlyError } = useContext(ChatContext)!
    const fontTheme = currentMode === "normal" ? "black" : "white"
    return (
        <motion.div
            animate={{ rotate: openChatHistoryDialogueBox ? -45 : 0 }}
            transition={{
                type: "spring",
                stiffness: 300,
                damping: 20
            }}
            onClick={() => {
                if (openChatHistoryDialogueBox) {
                    setOpenChatHistoryDialogueBox(false)
                    return
                }
                else {
                    setOpenChatHistoryDialogueBox(true);
                    if (!requestExists("chat_history")) {
                        wsSendAsync
                            (wsRef.current, { type: "chat_history" }).then(() => {
                                setResponseBasedActions(prev => [...(prev || []), { action: "chat_history"}])
                            }).catch(() => { showFriendlyError("Failed to load chat history. Please try again.") });
                    } else {
                        return
                    }
                }

            }} id="ham-burger" className="flex flex-col gap-y-1 cursor-pointer z-40">
            <div className={`w-7 h-[3.5px] rounded-full bg-${fontTheme}`}></div>
            <div className={`w-5 h-[3.5px] rounded-full bg-${fontTheme}`}></div>
        </motion.div>
    )
}

export default HamBurger