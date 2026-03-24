import { motion, easeInOut } from "framer-motion"
import BookRibbon from "../../../../icons/book_ribbon.svg"
import { useContext, useEffect, useRef } from "react"
import { ChatContext } from "@/app/context/chatbot/ChatContext"
import { SessionInitMessage } from "@/app/utils/types"
import { wsSendAsync } from "@/app/utils/retryOpernation"

const StoryModeExtraOptions = () => {
    const { setOpenStoryModeExtraOptions, wsRef } = useContext(ChatContext)!
    const overlayRef = useRef<HTMLDivElement | null>(null)

    useEffect(() => {
        const handleOutsideClick = (e: MouseEvent) => {
            if (
                overlayRef.current &&
                !overlayRef.current.contains(e.target as Node)
            ) {
                setOpenStoryModeExtraOptions(false);
            }
        };
        document.addEventListener("click", handleOutsideClick);
        return () => {
            document.removeEventListener("click", handleOutsideClick);
        };
    }, [setOpenStoryModeExtraOptions]);

    const initializeTadabburMode = async () => {
        if (!wsRef.current) return

        const user = localStorage.getItem("user");
        let user_id = null;
        if (user) {
            try {
                const userData = JSON.parse(user);
                user_id = userData.id;
            } catch (e) {
                console.error("Error parsing user data:", e);
            }
        }
        const sessionInit: SessionInitMessage = {
            type: "session-init",
            session_id: "",
            user_id: "",
            model: "",
            mode: "normal"
        };

        try {
            await wsSendAsync(
                wsRef.current,
                sessionInit,
                8,
                500
            );
        }
        catch (error) {
            console.error("❌ Failed to initialize WebSocket session:", error);
        }
    }

    return (
        <motion.div
            ref={overlayRef}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2, ease: easeInOut }} className="absolute bg-black/80 backdrop-blur-md border border-white/10 w-48 h-max -top-13 left-0 rounded-lg shadow-md p-1.5 z-20">
            <div onClick={() => {
                initializeTadabburMode()
                setOpenStoryModeExtraOptions(false)
            }} className="p-1 rounded-md cursor-pointer flex tracking-tight  items-center gap-x-2 hover:bg-neutral-700/80">
                <BookRibbon className="w-5 h-5 fill-current text-white" />
                <p className="switzer-500 text-white tracking-tighter ml-2">Tadabbur</p>
            </div>

        </motion.div>
    )
}

export default StoryModeExtraOptions