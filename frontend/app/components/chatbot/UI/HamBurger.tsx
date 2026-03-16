import { motion } from "framer-motion"
import { wsSendAsync } from "@/app/utils/retryOpernation"

type HamBurgerProps = {
    wsRef: React.RefObject<WebSocket | null>;
    openChatHistoryDialogueBox: boolean;
    setOpenChatHistoryDialogueBox: React.Dispatch<React.SetStateAction<boolean>>;
    currentMode: "normal" | "story" | null;
}

const HamBurger = ({ wsRef, openChatHistoryDialogueBox, setOpenChatHistoryDialogueBox, currentMode }: HamBurgerProps) => {
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

            }} id="ham-burger" className="flex flex-col gap-y-1 cursor-pointer z-40">
            <div className={`w-7 h-[3.5px] rounded-full bg-${fontTheme}`}></div>
            <div className={`w-5 h-[3.5px] rounded-full bg-${fontTheme}`}></div>
        </motion.div>
    )
}

export default HamBurger