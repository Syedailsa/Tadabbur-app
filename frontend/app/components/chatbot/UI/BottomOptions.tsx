import { useState, useContext } from "react";
import { OptionsContext } from "@/app/context/chatbot/OptionsContext";
import { motion } from "framer-motion";
import DownArrow from "../../../../icons/arrow-down-head.svg";
import AttachIcon from "../../../../icons/attach_icon.svg";
import PlusIcon from "../../../../icons/plus-icon.svg";
import StoryIcon from "../../../../icons/story_telling_icon.svg";
import MicIcon from "../../../../icons/mic_icon.svg";

const BottomOptions = () => {
  const {
    hideExtraOptions,
    setHideExtraOptions,
    selectedModel,
    setSelectedModel,
    hideModelBox,
    setHideModelBox,
  } = useContext(OptionsContext);

  return (
    <div
      id="bottom-options"
      className="w-full flex gap-x-1 mt-auto items-center"
    >
      <motion.div
        whileTap={{ backgroundColor: "#0000003D" }}
        whileHover={{ backgroundColor: "#0000000D" }}
        id="choose-model-box"
        onClick={(e) => {
          e.stopPropagation();
          setHideModelBox((prev: boolean | null) => !prev);
        }}
        className="relative flex flex-row-reverse gap-x-1 py-1 pr-3 pl-4 rounded-full cursor-pointer items-center"
      >
        <motion.div className="mt-0.2">
          <DownArrow className="w-5 h-5" />
        </motion.div>
        <p className="switzer-500 text-[0.96rem]">{selectedModel}</p>
      </motion.div>
      <motion.div className={`ml-auto flex gap-x-1`}>
        <motion.div
          onClick={(e) => {
            e.stopPropagation();
            setHideExtraOptions((prev: boolean) => !prev);
          }}
          animate={{
            backgroundColor: hideExtraOptions ? "#00000000" : "#0000000D",
          }}
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          className={`w-9 h-9 rounded-full flex items-center justify-center cursor-pointer
          }`}
        >
          <PlusIcon className="fill-current w-5 h-5 text-black" />
        </motion.div>
        <motion.div
          id="story-telling-box"
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          className="flex gap-x-1 px-3 py-1 rounded-full cursor-pointer items-center"
        >
          <StoryIcon className="fill-current w-5 h-5 text-black" />
          <span className="w-max switzer-500 text-[0.96rem]">
            Story telling
          </span>
        </motion.div>

        <motion.div
          id="mic-icon-box"
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          className="w-9 h-9 rounded-full flex items-center justify-center cursor-pointer"
        >
          <MicIcon className="w-5 h-5 fill-current text-black" />
        </motion.div>

        <motion.div
          whileTap={{ backgroundColor: "#0000003D" }}
          whileHover={{ backgroundColor: "#0000000D" }}
          className="rounded-full w-9 h-9 cursor-pointer flex justify-center items-center"
          id="attach-files-box"
        >
          <AttachIcon className="fill-current text-black w-5 h-5" />
        </motion.div>
      </motion.div>
    </div>
  );
};

export default BottomOptions;
