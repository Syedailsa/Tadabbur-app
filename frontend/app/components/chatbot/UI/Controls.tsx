import { AnimatePresence, easeInOut, motion } from "framer-motion";
import { ChatContext } from "@/app/context/chatbot/ChatContext";
import React, { FC, useContext, useEffect, useRef, useState } from "react";
import SettingIcon from "../../../../icons/settings_icon.svg";
import HistoryIcon from "../../../../icons/history_icon.svg";
import NewChatIcon from "../../../../icons/new_chat_icon.svg";
import { ControlProps } from "../interfaces/ControlProps";
import { wsSendAsync } from "@/app/utils/retryOpernation";

const Controls: FC<ControlProps> = ({ wsRef, connectionStatus }): React.ReactElement | null => {
  const [active, setActive] = useState<boolean | null>(false);
  const controlRef = useRef<HTMLDivElement | null>(null);
  const [overlayText, setOverlayText] = useState<string | null>(null);
  const { requestExists, setResponseBasedActions, setOpenChatHistoryDialogueBox, showFriendlyError } = useContext(ChatContext)!;
  const [overlayTranslate, setOverlayTranslate] = useState<number>(0);
  const [showOfflineError, setShowOfflineError] = useState(false);

  useEffect(() => {
    if (!active) return;
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        controlRef.current &&
        !controlRef.current.contains(e.target as Node)
      ) {
        setActive(false);
      }
    };
    document.addEventListener("click", handleOutsideClick);

    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [active, setActive]);

  const validateConnection = (callback: () => void) => {
    if (connectionStatus !== "connected") {
      setShowOfflineError(true);
      setTimeout(() => setShowOfflineError(false), 2000);
      return;
    }
    callback();
  };

  const InitializeNewSession = () => {
    if (!wsRef.current || requestExists("session-init")) return;
    wsSendAsync(
      wsRef.current,
      {
        type: "session-init",
        session_id: "",
        model: "kimi-k2-instruct-0905",
      }).then(() => {
        setResponseBasedActions(prev => [...(prev || []), { action: "session-init"}])
      }).catch(() => {
        showFriendlyError("Failed to start a new chat. Please try again.")
      });
  };
  const fetchChatHistory = () => {
    if (!requestExists('chat_history')) {
      wsSendAsync(wsRef.current, { type: "chat_history" }).then(() => {
        setResponseBasedActions(prev => [...(prev || []), { action: "chat_history"}])
      }).catch(() => { showFriendlyError("Failed to load chat history. Please try again.") });
    }
    setOpenChatHistoryDialogueBox(true);
  };

  return (
    <div className="w-full flex justify-center-safe">
      <AnimatePresence>
        {showOfflineError && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute top-10 left-1/2 -translate-x-1/2 bg-red-500 text-white text-[0.7rem] switzer-600 px-3 py-1.5 rounded-md shadow-lg z-100 whitespace-nowrap flex items-center gap-2"
          >
            <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse" />
            INTERNET DISCONNECTED
          </motion.div>
        )}
      </AnimatePresence>
      <motion.div
        ref={controlRef}
        onClick={() => {
          setActive((prev) => !prev);
        }}
        whileHover={{ scale: 1.02, backgroundColor: "#000000" }}
        animate={{ width: active ? 140 : 72 }}
        transition={{ duration: 0.3, ease: easeInOut }}
        className="h-8 w-18 backdrop-blur-md bg-black/5 rounded-full cursor-pointer flex justify-center items-center px-2 text-black hover:text-white relative"
      >
        {overlayText && active && (
          <motion.div
            animate={{ x: overlayTranslate }}
            className="absolute overlay left-2 top-9 py-2 px-3 h-2 rounded-full bg-black/90 flex justify-center items-center tracking-tighter"
          >
            <p className="switzer-500 text-white text-xs">{overlayText}</p>
          </motion.div>
        )}
        {active && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-x-4"
          >
            <div
              onClick={(e) => {
                e.stopPropagation();
                validateConnection(fetchChatHistory);
              }}
              onMouseOver={() => {
                setOverlayText("Chat History");
                setOverlayTranslate(-20);
              }}
              onMouseLeave={() => {
                setOverlayText("");
                setOverlayTranslate(0);
              }}
            >
              <HistoryIcon className="w-5 h-5 fill-current" />
            </div>
            <div
              onClick={(e) => {
                e.stopPropagation();
                validateConnection(InitializeNewSession);
              }}
              onMouseOver={() => {
                setOverlayText("New Chat");
                setOverlayTranslate(8);
              }}
              onMouseLeave={() => {
                setOverlayText("");
                setOverlayTranslate(0);
              }}
            >
              <NewChatIcon className="w-5 h-5 fill-current" />
            </div>
          </motion.div>
        )}
        <SettingIcon className="ml-auto w-5 h-5 fill-current" />
      </motion.div>
    </div>
  );
};

export default Controls;
