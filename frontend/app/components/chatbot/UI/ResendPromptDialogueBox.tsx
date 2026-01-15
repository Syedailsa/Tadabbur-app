import { PromptExtraOptionsContext } from "@/app/context/chatbot/PromptExtraOptionsContext";
import { motion, easeInOut } from "framer-motion";
import { useContext, useEffect, useRef, useState } from "react";
import SendIcon from "../../../../icons/send_icon.svg";
import Regenrate from "../../../../icons/refresh.svg";
import ShortText from "../../../../icons/short_text.svg";
import LongText from "../../../../icons/long_text.svg";
import Reference from "../../../../icons/reference.svg";
import Engaging from "../../../../icons/engage_icon.svg";
import { ChatMessage } from "../interfaces/ChatMessage";

const ResendPromptDialogueBox = () => {
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLDivElement>(null);
  const [customPrompt, setCustomPrompt] = useState<string>("");
  const [hidePlaceholder, setHidePlaceholder] = useState<boolean>(false);
  const {
    parent_index,
    assistant_index,
    hideResendPromptDialogue,
    setHideResendPromptDialogue,
    index,
    messages,
    setMessages,
    message_id,
    reply_to_message_id,
    ask,
  } = useContext(PromptExtraOptionsContext);

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        overlayRef.current &&
        !overlayRef.current.contains(e.target as Node)
      ) {
        setHideResendPromptDialogue(true);
      }
    };
    document.addEventListener("click", handleOutsideClick);
    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [hideResendPromptDialogue, setHideResendPromptDialogue]);

  // have to handle input tomorrow
  const handleInput = () => {
    if (!inputRef.current) return;
    const input = inputRef.current?.innerText;
    if (input.trim() != "") {
      const old_assistant_responses = messages?.[parent_index]?.responses;
      ask(
        messages[parent_index]?.content,
        input,
        true,
        reply_to_message_id,
        old_assistant_responses
      );
      setHideResendPromptDialogue(true);
    } else {
      return;
    }
  };
  return (
    <motion.div
      ref={overlayRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2, ease: easeInOut }}
      className="absolute bottom-12 left-28 rounded-md shadow-md bg-white h-max w-48 py-2"
    >
      <div className="flex w-full gap-x-2 px-2">
        <div className="relative w-full">
          <div
            ref={inputRef}
            onInput={(e) => {
              const target = e.target as HTMLDivElement;
              const text = target.textContent.trim() ?? "";
              setHidePlaceholder(text !== "");
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleInput();
                const old_assistant_responses =
                  messages?.[parent_index]?.responses;
                ask(
                  messages[parent_index]?.content,
                  inputRef.current?.innerText,
                  true,
                  reply_to_message_id,
                  old_assistant_responses
                );
              }
            }}
            contentEditable
            className="px-2 switzer-500 focus:outline-none border border-black/10 rounded-md max-w-37 max-h-10 overflow-y-auto"
          ></div>
          {!hidePlaceholder && (
            <span className="absolute text-[0.9rem] pointer-events-none text-black/70 switzer-500 top-[0.2rem] left-2">
              Your prompt here
            </span>
          )}
        </div>
        <div
          onClick={() => {
            handleInput();
            setHideResendPromptDialogue(true);
          }}
        >
          <SendIcon className="fill-current text-black/70 hover:text-black cursor-pointer" />
        </div>
      </div>

      <div className="flex flex-col gap-y-1 px-2 mt-1">
        {options?.map((option, idx) => {
          const Icon = IconMap[option.icon as keyof typeof IconMap];
          return (
            <div
              onClick={() => {
                console.log("reply_to_message_id", reply_to_message_id);
                console.log("message_id", message_id);
                if (option.text === "Regenerate") {
                  const user_message_index = parent_index;
                  if (user_message_index === null || user_message_index < 0)
                    return;
                  console.log("User message", messages[user_message_index]);

                  // save the assistant messsages before deleting the message object
                  const old_assistant_responses =
                    messages?.[parent_index]?.responses;
                  // remove the message object only with the user's message id
                  setMessages((prev: ChatMessage[]) =>
                    prev.filter(
                      (m: any) => m.message_id !== reply_to_message_id
                    )
                  );
                  ask(
                    messages[user_message_index]?.content,
                    null,
                    true,
                    reply_to_message_id,
                    old_assistant_responses
                  );
                } else {
                  if (!option.prompt) return;
                  const user_message_index = parent_index;

                  // save the assistant messsages before deleting the message object
                  const old_assistant_responses =
                    messages?.[parent_index]?.responses;
                  // remove the user and assistant message
                  setMessages((prev: ChatMessage[]) =>
                    prev.filter(
                      (m: any) => m.message_id !== reply_to_message_id
                    )
                  );
                  ask(
                    messages[user_message_index]?.content,
                    option?.prompt,
                    true,
                    reply_to_message_id,
                    old_assistant_responses
                  );
                }
                setHideResendPromptDialogue(true);
              }}
              className="py-1 px-1 flex gap-x-3 tracking-tight hover:bg-black/5 rounded-md items-center cursor-pointer"
              key={idx}
            >
              {Icon}
              <p className="switzer-500">{option.text}</p>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
};

const options = [
  { icon: "Regenerate", text: "Regenerate" },
  { icon: "ShortText", text: "Too short", prompt: "Give a longer response" },
  { icon: "LongText", text: "Too long", prompt: "Give a shorter response" },
  {
    icon: "Reference",
    text: "Include references",
    prompt: "Include references in the response",
  },
  {
    icon: "Engaging",
    text: "Be engaging",
    prompt: "Give a more engaging response",
  },
];

const IconMap = {
  Regenerate: <Regenrate className="w-4 h-4 fill-current text-black" />,
  ShortText: <ShortText className="w-5.5 h-5.5 fill-current text-black" />,
  LongText: <LongText className="w-4.5 h-4.5 fill-current text-black" />,
  Reference: <Reference className="w-4.5 h-4.5 fill-current text-black" />,
  Engaging: <Engaging className="w-4.5 h-4.5 fill-current text-black" />,
};
export default ResendPromptDialogueBox;
