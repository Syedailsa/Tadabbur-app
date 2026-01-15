import { useContext, useEffect, useState } from "react";
import { PromptExtraOptionsContext } from "@/app/context/chatbot/PromptExtraOptionsContext";
import { motion, number } from "framer-motion";
import PromptExtraOptionsModelBox from "./PromptExtraOptionsModelBox";
import ThumbsUp from "../../../../icons/thumbs-up.svg";
import ThumbsDown from "../../../../icons/thumbs-down.svg";
import Copy from "../../../../icons/copy.svg";
import Refresh from "../../../../icons/refresh.svg";
import MoreOptions from "../../../../icons/more_options.svg";
import ResendPromptDialogueBox from "./ResendPromptDialogueBox";
import { ChatMessage } from "../interfaces/ChatMessage";
import ArrowLeft from "../../../../icons/arrow-left-bold.svg";

const PromptExtraOptions = ({
  messageType,
}: {
  messageType: "user" | "assistant";
}) => {
  const {
    parent_index,
    assistant_index,
    messages,
    setMessages,
    message_id,
    wsRef,
    hidePromptExtraOptionsModelBox,
    setHidePromptExtraOptionsModelBox,
    sessionID,
    hideResendPromptDialogue,
    setHideResendPromptDialogue,
  } = useContext(PromptExtraOptionsContext);
  const [overlayTranslateAmount, setOverlayTranslateAmount] = useState<
    number | null
  >(0);
  const [isCopied, setIsCopied] = useState<boolean | null>(null);
  const [overlayText, setOverlayText] = useState<string | null>(null);
  const [active, setActive] = useState<boolean | null>(false);

  const feedback =
    messages?.[parent_index]?.responses?.[assistant_index]?.feedback || null;
  const hasMultipleResponses =
    messages?.[parent_index]?.number_of_responses > 1;
  type OptionType = "copy" | "resend" | "like" | "dislike";
  const handleOptionClick = ({ type }: { type: OptionType }) => {
    switch (type) {
      case "copy":
        let content: string = "";
        if (messageType === "assistant") {
          content = messages[parent_index].responses[assistant_index].content;
        } else if (messageType === "user") {
          content = messages[parent_index].content;
        }
        navigator.clipboard
          .writeText(content)
          .then(() => {
            console.log("Copied to clipboard!");
            setIsCopied(true);
          })
          .catch((err) => console.error("Failed to copy", err));
        break;
      case "like":
        wsRef?.current.send(
          JSON.stringify({
            type: "like",
            message:
              messages?.[parent_index]?.responses?.[assistant_index]?.content,
            message_id: message_id,
            session_id: sessionID,
          })
        );

        if (messages && setMessages) {
          const updatedMessages = [...messages];
          updatedMessages[parent_index].responses[assistant_index].feedback =
            "like";
          setMessages(updatedMessages);
        }

        break;
      case "dislike":
        wsRef?.current.send(
          JSON.stringify({
            type: "dislike",
            message:
              messages?.[parent_index]?.responses?.[assistant_index]?.content,
            message_id: message_id,
            session_id: sessionID,
          })
        );

        if (messages && setMessages) {
          const updatedMessages = [...messages];
          updatedMessages[parent_index].responses[assistant_index].feedback =
            "dislike";
          setMessages(updatedMessages);
        }
        break;
      case "resend":
        setHideResendPromptDialogue((prev: boolean | null) => !prev);
        break;
      default:
        break;
    }
  };
  return (
    <div>
      {messageType === "assistant" ? (
        <div className="flex gap-x-1.5 px-2 py-2 relative">
          {messages?.[parent_index]?.number_of_responses > 1 && (
            <div className="flex gap-x-1 items-center">
              <motion.div
                onClick={() => {
                  const activeIndex =
                    messages?.[parent_index]?.active_message_index;
                  const number_of_responses =
                    messages?.[parent_index]?.number_of_responses;

                  // check if activeIndex is below zero
                  if (activeIndex <= 0) {
                    return;
                  }
                  setMessages((prev: ChatMessage[]) => {
                    const messageArray = [...prev];
                    const msg = messageArray[parent_index];
                    if (msg && typeof msg.active_message_index === "number") {
                      msg.active_message_index -= 1;
                    }

                    return messageArray;
                  });
                }}
                whileTap={{ color: "#0000001a" }}
                id="arrow-right"
                className="p-1 hover:bg-black/5 cursor-pointer rounded-md"
              >
                <ArrowLeft className="w-4 h-4" />
              </motion.div>
              <p className="switzer-500">
                {(messages[parent_index].active_message_index ?? 0) + 1}/
                {messages[parent_index].number_of_responses ?? 0}
              </p>

              <motion.div
                onClick={() => {
                  const activeIndex =
                    messages?.[parent_index]?.active_message_index;
                  const number_of_responses =
                    messages?.[parent_index]?.number_of_responses;

                  if (activeIndex + 1 >= number_of_responses) {
                    return;
                  }

                  setMessages((prev: ChatMessage[]) => {
                    const messageArray = [...prev];
                    const msg = messageArray[parent_index];
                    if (msg && typeof msg.active_message_index === "number") {
                      msg.active_message_index += 1;
                    }

                    return messageArray;
                  });
                }}
                whileTap={{ color: "#0000001a" }}
                id="arrow-right"
                className="p-1 hover:bg-black/5 cursor-pointer rounded-md"
              >
                <ArrowLeft className="w-4 h-4 rotate-180" />
              </motion.div>
            </div>
          )}
          <div
            onMouseOver={() => {
              setOverlayTranslateAmount(hasMultipleResponses ? 82 : 4);
              setOverlayText("Copy");
              setActive(true);
            }}
            onMouseLeave={() => {
              setActive(false);
              setIsCopied(false);
            }}
            onClick={() => {
              handleOptionClick({ type: "copy" });
              setOverlayText("Copied");
            }}
            className="p-1.5 hover:bg-black/5 rounded-md cursor-pointer"
          >
            <Copy className="w-4.5 h-4.5" />
          </div>

          <div
            onMouseOver={() => {
              setOverlayTranslateAmount(hasMultipleResponses ? 120 : 38);
              setOverlayText("Like");
              setActive(true);
            }}
            onMouseLeave={() => {
              setActive(false);
            }}
            onClick={() => {
              handleOptionClick({ type: "like" });
            }}
            className="p-1.5 hover:bg-black/5 rounded-md cursor-pointer"
          >
            <ThumbsUp
              className={`w-4 h-4 ${
                feedback === "like" ? "fill-blue-400" : ""
              }`}
            />
          </div>

          <div
            onMouseOver={() => {
              setOverlayTranslateAmount(hasMultipleResponses ? 150 : 64);
              setOverlayText("Dislike");
              setActive(true);
            }}
            onMouseLeave={() => {
              setActive(false);
            }}
            onClick={() => {
              handleOptionClick({ type: "dislike" });
            }}
            className="p-1.5 hover:bg-black/5 rounded-md cursor-pointer"
          >
            <ThumbsDown
              className={`w-4 h-4 ${
                feedback === "dislike" ? "fill-red-400" : ""
              }`}
            />
          </div>
          <div
            onMouseOver={() => {
              setOverlayTranslateAmount(hasMultipleResponses ? 180 : 95);
              setOverlayText("Resend");
              setActive(true);
            }}
            onMouseLeave={() => {
              setActive(false);
            }}
            onClick={() => {
              handleOptionClick({ type: "resend" });
            }}
            className="p-1.5 hover:bg-black/5 rounded-md cursor-pointer"
          >
            <Refresh className="w-4 h-4" />
          </div>
          <div
            onMouseOver={() => {
              setOverlayTranslateAmount(hasMultipleResponses ? 132 : 102);
            }}
            onClick={() => {
              setHidePromptExtraOptionsModelBox(
                (prev: boolean | null) => !prev
              );
            }}
            className="p-1.5 hover:bg-black/5 rounded-md cursor-pointer"
          >
            <MoreOptions className="w-4 h-4" />
          </div>
          {active && (
            <motion.div
              style={{ left: `${overlayTranslateAmount}px` }}
              id="overlay-prompt-options-name"
              className="absolute top-11 py-2 px-3 h-2 rounded-full bg-black/90 flex justify-center items-center tracking-tighter"
            >
              <p className="switzer-500 text-white text-xs">{overlayText}</p>
            </motion.div>
          )}
          {!hidePromptExtraOptionsModelBox && <PromptExtraOptionsModelBox />}
          {!hideResendPromptDialogue && <ResendPromptDialogueBox />}
        </div>
      ) : messageType === "user" ? (
        <div className="flex gap-x-1.5 pr-1 pl-2 pb-2 pt-1 relative">
          <div
            onMouseOver={() => {
              setOverlayText("Copy");
              setActive(true);
            }}
            onMouseLeave={() => {
              setActive(false);
              setIsCopied(false);
            }}
            onClick={() => {
              handleOptionClick({ type: "copy" });
              setOverlayText("Copied");
            }}
            className="p-1.5 hover:bg-black/5 ml-auto rounded-md cursor-pointer"
          >
            <Copy className="w-4.5 h-4.5" />
          </div>
          {active && (
            <motion.div
              id="overlay-prompt-options-name"
              className="absolute w-max top-10 right-0 py-2 px-3 h-2 rounded-full bg-black/90 flex justify-center items-center tracking-tighter"
            >
              <p className="switzer-500 text-white text-xs">{overlayText}</p>
            </motion.div>
          )}
        </div>
      ) : null}
    </div>
  );
};

export default PromptExtraOptions;
