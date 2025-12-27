import { useContext, useState } from "react";
import { PromptExtraOptionsContext } from "@/app/context/chatbot/PromptExtraOptionsContext";
import { motion } from "framer-motion";
import PromptExtraOptionsModelBox from "./PromptExtraOptionsModelBox";
import ThumbsUp from "../../../../icons/thumbs-up.svg";
import ThumbsDown from "../../../../icons/thumbs-down.svg";
import Copy from "../../../../icons/copy.svg";
import Refresh from "../../../../icons/refresh.svg";
import MoreOptions from "../../../../icons/more_options.svg";

const PromptExtraOptions = ({
  messageType,
}: {
  messageType: string | null;
}) => {
  const {
    messages,
    index,
    message_id,
    wsRef,
    hidePromptExtraOptionsModelBox,
    setHidePromptExtraOptionsModelBox,
    sessionID,
    ask,
  } = useContext(PromptExtraOptionsContext);
  const [overlayTranslateAmount, setOverlayTranslateAmount] = useState<
    number | null
  >(0);
  const [isCopied, setIsCopied] = useState<boolean | null>(null);
  const [overlayText, setOverlayText] = useState<string | null>(null);
  const [active, setActive] = useState<boolean | null>(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  // useEffect(() => {
  //   console.log("Feedback", feedback);
  // }, [feedback]);

  type OptionType = "copy" | "resend" | "like" | "dislike";
  const handleOptionClick = ({ type }: { type: OptionType }) => {
    switch (type) {
      case "copy":
        navigator.clipboard
          .writeText(messages[index].content)
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
            index: index,
            message_id: message_id,
            session_id: sessionID,
          })
        );
        break;
      case "dislike":
        wsRef?.current.send(
          JSON.stringify({
            type: "dislike",
            index: index,
            message_id: message_id,
            session_id: sessionID,
          })
        );
        break;
      case "resend":
        ask(messages[index - 1].content);
        break;
      default:
        break;
    }
  };

  return (
    <div>
      {messageType === "assistant" ? (
        <div className="flex gap-x-1.5 px-2 py-2 relative">
          <div
            onMouseOver={() => {
              setOverlayTranslateAmount(4);
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
              setOverlayTranslateAmount(38);
              setOverlayText("Like");
              setActive(true);
            }}
            onMouseLeave={() => {
              setActive(false);
            }}
            onClick={() => {
              handleOptionClick({ type: "like" });
              setFeedback("liked");
            }}
            className="p-1.5 hover:bg-black/5 rounded-md cursor-pointer"
          >
            <ThumbsUp
              className={`w-4 h-4 ${
                feedback === "liked" ? "fill-blue-400" : ""
              }`}
            />
          </div>
          <div
            onMouseOver={() => {
              setOverlayTranslateAmount(66);
              setOverlayText("Dislike");
              setActive(true);
            }}
            onMouseLeave={() => {
              setActive(false);
            }}
            onClick={() => {
              handleOptionClick({ type: "dislike" });
              setFeedback("disliked");
            }}
            className="p-1.5 hover:bg-black/5 rounded-md cursor-pointer"
          >
            <ThumbsDown
              className={`w-4 h-4 ${
                feedback === "disliked" ? "fill-red-400" : ""
              }`}
            />
          </div>
          <div
            onMouseOver={() => {
              setOverlayTranslateAmount(98);
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
              setOverlayTranslateAmount(132);
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
