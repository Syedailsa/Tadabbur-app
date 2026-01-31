import { useContext, useEffect, useRef, useState } from "react";
import { PromptExtraOptionsContext } from "@/app/context/chatbot/PromptExtraOptionsContext";
import { audioScheduler } from "@/app/utils/AudioScheduler";
import ReadAloud from "../../../../icons/read_aloud.svg";
import Flag from "../../../../icons/flag.svg";
import Pause from "../../../../icons/pause.svg";
import LoadCircle from "../../../../icons/load_circle.svg";
import { motion } from "framer-motion";
import { ChatContext } from "@/app/context/chatbot/ChatContext";

const PromptExtraOptionsModelBox = () => {
  const {
    parent_index,
    messages,
    hidePromptExtraOptionsModelBox,
    setHidePromptExtraOptionsModelBox,
    wsRef,
    message_id,
    assistant_index,
    sessionID,
    setHideReportContentDialogueBox,
  } = useContext(PromptExtraOptionsContext);
  const [audioLoading, setAudioLoading] = useState<boolean>(false);
  const [isPlayed, setIsPlayed] = useState<boolean>(false);
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const { setReportedMessageID } = useContext(ChatContext);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        overlayRef.current &&
        !overlayRef.current.contains(e.target as Node)
      ) {
        setHidePromptExtraOptionsModelBox(true);
      }
    };

    document.addEventListener("click", handleOutsideClick);
    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [hidePromptExtraOptionsModelBox, setHidePromptExtraOptionsModelBox]);

  type OptionType = "read_aloud" | "report";
  const handleOptionClick = ({ type }: { type: OptionType }) => {
    switch (type) {
      case "read_aloud":
        if (wsRef?.current?.readyState === WebSocket.OPEN) {
          // ⚡ FORCE RESET AUDIO ENGINE ⚡
          audioScheduler.reset();

          wsRef.current.send(
            JSON.stringify({
              type: "tts_request",
              text:
                messages?.[parent_index]?.responses?.[assistant_index]
                  ?.content || "",
              message_id: message_id,
               reply_to_message_id: messages?.[parent_index]?.responses?.[assistant_index]?.reply_to_message_id || null,  
              session_id: sessionID,
            })
          );
          setAudioLoading(true);
        }
        break;
      case "report":
        setHidePromptExtraOptionsModelBox(true);
        setReportedMessageID(message_id);
        setHideReportContentDialogueBox(false);

        break;
      default:
        break;
    }
  };
  return (
    <motion.div
      ref={overlayRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="absolute bottom-12 left-36 w-42 h-max rounded-xl bg-white shadow-md overflow-clip border border-black/5 px-1 pt-1 pb-2"
    >
      <div className="w-full h-full flex flex-col items-center">
        <div
          onClick={() => handleOptionClick({ type: "read_aloud" })}
          className="w-full flex rounded-md items-center p-1.5 hover:bg-black/5 cursor-pointer"
        >
          {/* {audioLoading && (
            <div>
              <div className="ml-2">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 0.6, repeat: Infinity }}
                >
                  <LoadCircle className="w-5 h-5 fill-current text-black/50" />
                </motion.div>
              </div>

              <p className="ml-2 switzer-500 text-black/50 text-[0.94rem]">
                Loading
              </p>
            </div>
          )} */}

          {/* <Pause className="ml-2 w-5 h-5 fill-current text-black/80" />
          <p className="ml-2 switzer-500 text-[0.94rem]">Pause</p> */}
          <ReadAloud className="ml-2 w-5 h-5 fill-current text-black/80" />
          <p className="ml-2 switzer-500 text-[0.94rem]">Read aloud</p>
        </div>
        <div
          onClick={() => handleOptionClick({ type: "report" })}
          className="w-full flex rounded-md items-center p-1.5 hover:bg-black/5 cursor-pointer"
        >
          <Flag className="ml-2 w-5 h-5 " />
          <p className="ml-2 switzer-500 text-[0.94rem]">Report Content</p>
        </div>
      </div>
    </motion.div>
  );
};

export default PromptExtraOptionsModelBox;
