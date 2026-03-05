import { motion } from "framer-motion"
import { useContext } from "react"
import { ChatContext } from "@/app/context/chatbot/ChatContext"
import { wsSendAsync } from "@/app/utils/retryOpernation"

const HamBurger = () => {
    const { wsRef, openChatHistoryDialogueBox, setOpenChatHistoryDialogueBox, currentMode } = useContext(ChatContext)!
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
                }
                else {
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
                    wsSendAsync
                        (wsRef.current, { type: "chat_history", user_id: user_id }).catch(() => { });
                    setOpenChatHistoryDialogueBox(true);
                }

            }} id="ham-burger" className="absolute top-8 left-4 self-start flex flex-col gap-y-1 cursor-pointer z-40">
            <div className={`w-7 h-[3.5px] rounded-full bg-${fontTheme}`}></div>
            <div className={`w-5 h-[3.5px] rounded-full bg-${fontTheme}`}></div>
        </motion.div>
    )
}

export default HamBurger