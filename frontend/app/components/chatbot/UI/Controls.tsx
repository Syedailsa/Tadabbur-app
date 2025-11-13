import { easeInOut, motion } from "framer-motion";
import { div } from "framer-motion/m";
import React, { FC, useEffect, useRef, useState } from "react";
import SettingIcon from "../../../../icons/settings_icon.svg";
import HistoryIcon from "../../../../icons/history_icon.svg";
import NewChatIcon from "../../../../icons/new_chat_icon.svg";
import { generateNewSessionId } from "@/app/session/session";

interface ControlProps {
  wsRef: React.RefObject<WebSocket | null>;
}

const Controls: FC<ControlProps> = ({ wsRef }): React.ReactElement | null => {
  const [active, setActive] = useState<boolean | null>(false);
  const controlRef = useRef<HTMLDivElement | null>(null);
  const [overlayText, setOverlayText] = useState<string | null>(null);

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

  const InitializeNewSession = () => {
    if (!wsRef.current) return;
    const session_id = generateNewSessionId();
    wsRef.current.send(JSON.stringify({ session_id: session_id }));
  };
  return (
    <div className="w-full flex justify-center-safe">
      <motion.div
        ref={controlRef}
        onClick={() => {
          setActive((prev) => !prev);
        }}
        whileHover={{ scale: 1.02, backgroundColor: "#000000" }}
        animate={{ width: active ? 140 : 72 }}
        transition={{ duration: 0.3, ease: easeInOut }}
        className="h-8 w-18 backdrop-blur-md border border-white bg-black/5 rounded-full cursor-pointer flex justify-center items-center px-2  text-black hover:text-white relative"
      >
        {overlayText && (
          <div className="absolute overlay left-2 top-9 py-2 px-3 h-2 rounded-full bg-black/20 flex justify-center items-center">
            <p className="switzer-500 text-xs">{overlayText}</p>
          </div>
        )}
        {active && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-x-4"
          >
            <div
              onMouseOver={() => {
                setOverlayText("Chat history");
              }}
              onMouseLeave={() => {
                setOverlayText("");
              }}
            >
              <HistoryIcon className="w-5 h-5 fill-current" />
            </div>
            <div
              onClick={InitializeNewSession}
              onMouseOver={() => {
                setOverlayText("New Chat");
              }}
              onMouseLeave={() => {
                setOverlayText("");
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
