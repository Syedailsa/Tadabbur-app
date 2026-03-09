import React, { useContext, useEffect, useRef } from "react";
import ReadAloud from "../../../../icons/read_aloud.svg";
import Flag from "../../../../icons/flag.svg";
import Pause from "../../../../icons/pause.svg";
import Play from "../../../../icons/play.svg"
import { motion } from "framer-motion";
import { ChatContext } from "@/app/context/chatbot/ChatContext";
import { AssistantMessage, ChatMessage } from "../interfaces/ChatMessage";
import hidePromptExtraOptionsModelBoxArray from "../interfaces/hidePromptExtraOptionsModelBoxArray";
import { wsSendAsync } from "@/app/utils/retryOpernation";

type PromptExtraOptionsModelBoxProps = {
  message_id: string | null;
  reply_to_message_id: string | null;
  parent_index: number;
  assistant_index: number | null;
};

const PromptExtraOptionsModelBox = ({
  message_id,
  reply_to_message_id,
  parent_index,
  assistant_index,
}: PromptExtraOptionsModelBoxProps) => {

  const { wsRef, sessionID, messages, setMessages, setReportedMessageID, audioRef, currentPlayableAudio, setHidePromptExtraOptionsModelBoxArray, setHideReportContentDialogueBox, currentMode } = useContext(ChatContext)!
  const overlayRef = useRef<HTMLDivElement | null>(null);

  const audio_state = messages?.find((m: ChatMessage) => m.message_id === reply_to_message_id)?.responses.find((r: AssistantMessage) => r.message_id === message_id)?.audio_state
  const backgroundTheme = currentMode === "normal" ? "white" : "black"
  const fontTheme = currentMode === "normal" ? "black" : "white"

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {

      if (
        overlayRef.current &&
        !overlayRef.current.contains(e.target as Node)
      ) {
        setHidePromptExtraOptionsModelBoxArray((prev: hidePromptExtraOptionsModelBoxArray[]) => prev.map(m => m.assistant_message_id === message_id ? { ...m, hidePromptExtraOptionsModelBox: true } : m))
      }
    };

    document.addEventListener("click", handleOutsideClick);
    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [message_id, setHidePromptExtraOptionsModelBoxArray]);

  type OptionType = "read_aloud" | "report";
  const handleOptionClick = ({ type }: { type: OptionType }) => {
    if (assistant_index == null) return
    switch (type) {
      case "read_aloud":
        if (wsRef?.current?.readyState === WebSocket.OPEN) {
          const currentAudioInfo: { user_message_id: string | null, response_message_id: string | null, state: "loading" | "playing" | "paused" | "ended" | null } | null = { user_message_id: reply_to_message_id, response_message_id: message_id, state: "loading" }

          currentPlayableAudio.current = currentAudioInfo
          // first check if audio already exists
          const audio_link = messages?.find((m: ChatMessage) => m.message_id === reply_to_message_id)?.responses.find((r: AssistantMessage) => r.message_id === message_id)?.audio_link

          if (audio_link && audioRef.current) {
            audioRef.current.src = ""
            audioRef.current.src = audio_link
            audioRef.current.play()
            break
          }
          wsSendAsync(wsRef.current, {
            type: "tts_request",
            text:
              messages?.[parent_index]?.responses?.[assistant_index]
                ?.content || "",
            message_id: message_id,
            reply_to_message_id: reply_to_message_id,
            session_id: sessionID,
          });

          setMessages((prev: ChatMessage[]) =>
            prev.map((m) =>
              m.message_id === reply_to_message_id
                ? {
                  ...m,
                  responses: m.responses.map((n) =>
                    n.message_id === message_id
                      ? { ...n, audio_state: "loading" }
                      : { ...n, audio_state: null }
                  )
                }
                : {
                  ...m,
                  responses: m.responses.map(o => ({ ...o, audio_state: null }))
                }
            )

          );

        }
        break;
      case "report":
        setHidePromptExtraOptionsModelBoxArray((prev: hidePromptExtraOptionsModelBoxArray[]) => prev.map(m => m.assistant_message_id === message_id ? { ...m, hidePromptExtraOptionsModelBox: !m.hidePromptExtraOptionsModelBox } : m))
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
      className={`absolute bottom-12 left-36 w-42 h-max border rounded-xl ${backgroundTheme} ${backgroundTheme === "white" ? "border-black/5 bg-white" : "bg-black/80 border-white/10 backdrop-blur-md"} shadow-md overflow-clip px-1 p-2`}
    >

      <div className="w-full h-full flex flex-col items-center">
        {audio_state === "loading" ? (
          <div className={`w-full flex rounded-md items-center p-1 ${backgroundTheme === "white" ? "hover:bg-black/5" : "hover:bg-neutral-700/80"} cursor-pointer`}>
            <motion.div style={{
              borderLeftWidth: '2px',
              borderRightWidth: '2px',
              borderColor: fontTheme === "black" ? 'rgba(0,0,0,0.5)' : 'white'
            }} animate={{ rotate: 360 }} transition={{ duration: 0.6, repeat: Infinity, repeatType: "loop" }} className={`ml-2 w-4 h-4 rounded-full fill-current`}></motion.div>
            <p className={`ml-2 switzer-500 text-${fontTheme === "black" ? "black/50" : "white"} text-[0.94rem]`}>
              Loading
            </p>
          </div>
        ) : (audio_state === "ended" || !audio_state) ? (
          <div className={`w-full flex rounded-md items-center p-1 ${backgroundTheme === "white" ? "hover:bg-black/5" : "hover:bg-neutral-700/80"} cursor-pointer`}
            onClick={() => handleOptionClick({ type: "read_aloud" })}>
            <ReadAloud className={`ml-2 w-5 h-5 fill-current ${fontTheme === "black" ? "text-black/80" : "text-white"}`} />
            <p className={`ml-2 switzer-500 text-[0.94rem] text-${fontTheme}`}>Read aloud</p>
          </div>
        ) : audio_state === "playing" ? (
          <div onClick={() => {
            audioRef?.current?.pause()

          }} className={`w-full flex rounded-md items-center p-1 ${backgroundTheme === "white" ? "hover:bg-black/5" : "hover:bg-neutral-700/80"} cursor-pointer`}>
            <Pause className={`ml-2 w-5 h-5 fill-current ${fontTheme === "black" ? "text-black/80" : "text-white"}`} />
            <p className={`ml-2 switzer-500 text-[0.94rem] text-${fontTheme}`}>Pause</p>
          </div>
        ) : audio_state === "paused" ? (
          <div onClick={() => {
            audioRef?.current?.play()
          }} className={`w-full flex rounded-md items-center p-1 ${backgroundTheme === "white" ? "hover:bg-black/5" : "hover:bg-neutral-700/80"} cursor-pointer`}>
            <Play className={`ml-2 w-5 h-5 fill-current ${fontTheme === "black" ? "text-black/80" : "text-white"}`} />
            <p className={`ml-2 switzer-500 text-[0.94rem] text-${fontTheme}`}>Play</p>
          </div>

        ) : (null)}

      </div>
      <div
        onClick={() => handleOptionClick({ type: "report" })}
        className={`w-full flex rounded-md items-center p-1 ${backgroundTheme === "white" ? "hover:bg-black/5" : "hover:bg-neutral-700/80"} cursor-pointer`}
      >
        <Flag className={`ml-2 w-5 h-5 fill-current text-${fontTheme}`} />
        <p className={`ml-2 switzer-500 text-[0.94rem] text-${fontTheme}`}>Report Content</p>
      </div>
    </motion.div>
  );
};

export default PromptExtraOptionsModelBox;