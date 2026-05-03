import { motion, easeInOut } from "framer-motion"
import BookRibbon from "../../../../icons/book_ribbon.svg"
import { useContext, useEffect, useRef } from "react"
import { ChatContext } from "@/app/context/chatbot/ChatContext"
import { SessionInitMessage } from "@/app/utils/types"
import { wsSendAsync } from "@/app/utils/retryOpernation"

const StoryModeExtraOptions = () => {
    const { setOpenStoryModeExtraOptions, wsRef, requestExists, setResponseBasedActions, showFriendlyError } = useContext(ChatContext)!
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
            document.removeEventListener("click",handleOutsideClick);
        };
    }, [setOpenStoryModeExtraOptions]);

    const initializeTadabburMode = async () => {
        if (!wsRef.current || requestExists("session-init")) return
        const sessionInit: SessionInitMessage = {
            type: "session-init",
            session_id: "",
            mode: "normal"
        };

        try {
            wsSendAsync(
                wsRef.current,
                sessionInit,
                8,
                500
            ).then(() => {
                setResponseBasedActions(prev => [...(prev || []), { action: "session-init" }])
            }).catch(() => { showFriendlyError("Failed to switch mode. Please try again.") });
        }
        catch (error) {
            showFriendlyError("Failed to switch mode. Please try again.")
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