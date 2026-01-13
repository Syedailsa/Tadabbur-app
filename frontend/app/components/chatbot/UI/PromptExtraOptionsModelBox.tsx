import { useContext, useEffect, useRef } from "react";
import { PromptExtraOptionsContext } from "@/app/context/chatbot/PromptExtraOptionsContext";
import ReadAloud from "../../../../icons/read_aloud.svg";
import Flag from "../../../../icons/flag.svg";
import { easeInOut, motion } from "framer-motion";
import { ChatContext } from "@/app/context/chatbot/ChatContext";

const PromptExtraOptionsModelBox = () => {
  const {
    parent_index,
    assistant_index,
    message_id,
    hidePromptExtraOptionsModelBox,
    setHidePromptExtraOptionsModelBox,
    setHideReportContentDialogueBox,
  } = useContext(PromptExtraOptionsContext);

  const { setReportedMessageInfo } = useContext(ChatContext);
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

  type OptionType = "read_aloud" | "report_content";
  const handleOptionClick = ({ type }: { type: OptionType }) => {
    switch (type) {
      case "read_aloud":
        // logic needs to be build
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
      transition={{ duration: 0.2, ease: easeInOut }}
      className="absolute bottom-12 left-36 w-42 h-max rounded-xl bg-white shadow-md overflow-clip border border-black/5 px-2 pt-1 pb-2"
    >
      <div className="w-full h-full flex flex-col items-center">
        <div
          onClick={() => {
            setHidePromptExtraOptionsModelBox(true);
          }}
          className="w-full flex rounded-md items-center p-1.5 hover:bg-black/5 cursor-pointer"
        >
          <ReadAloud className="ml-2 w-5 h-5 fill-current text-black/80" />
          <p className="ml-2 switzer-500 text-[0.94rem]">Read aloud</p>
        </div>
        <div
          onClick={() => {
            setHidePromptExtraOptionsModelBox(true);
            setReportedMessageInfo({ messageID: message_id });
            setHideReportContentDialogueBox(false);
          }}
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
