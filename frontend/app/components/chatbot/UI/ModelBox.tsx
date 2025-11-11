import { FC } from "react";
import { useState, useRef, useEffect, useContext } from "react";
import { OptionsContext } from "@/app/context/chatbot/OptionsContext";
import { motion } from "framer-motion";
import NetworkIntelligence from "../../../../icons/network_intelligence_icon.svg";

interface ModelBoxProps {
  modelList: {
    model_name: string;
    provider: string;
    parameters: string;
    isNew: boolean;
    background: string;
  }[];
}

const ModelBox: FC<ModelBoxProps> = ({
  modelList,
}): React.ReactElement | null => {
  const [filteredModels, setFilteredModels] =
    useState<ModelBoxProps["modelList"]>(modelList);
  const { hideModelBox, setHideModelBox, setSelectedModel } =
    useContext(OptionsContext);
  const overlayRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (hideModelBox) return;
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        overlayRef.current &&
        !overlayRef.current.contains(e.target as Node)
      ) {
        setHideModelBox(true);
        setFilteredModels(modelList);
      }
    };

    document.addEventListener("click", handleOutsideClick);
    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [hideModelBox, setHideModelBox]);

  if (hideModelBox) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      ref={overlayRef}
      className="w-60 h-40 absolute left-3 bottom-14 rounded-lg bg-white/80 shadow-md backdrop-blur-md overflow-x-clip overflow-y-auto border border-black/10"
    >
      <div className="p-2 flex justify-center">
        <input
          onInput={(e) => {
            const value = e.currentTarget.value.toLowerCase();
            setFilteredModels(
              modelList.filter((m) =>
                m.model_name.toLowerCase().startsWith(value)
              )
            );
          }}
          placeholder="Search model through id, keyword or name"
          className="w-full focus:outline-none rounded-md border border-black/10 switzer-500 text-sm py-1 px-2 placeholder-black/60"
          type="text"
        />
      </div>
      <div className="flex flex-col gap-y-4 px-2 pb-4">
        {filteredModels.length > 0 ? (
          filteredModels?.map((model, index) => (
            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              key={index}
              onClick={() => {
                setSelectedModel(model.model_name);
                setHideModelBox(true);
                setFilteredModels(modelList);
              }}
              className={`flex flex-col h-24 p-2 ${model.background} text-white cursor-pointer shadow-md`}
            >
              {/* Provider Qwen */}
              {/* Parameters 235B */}
              {/* Kind Base model */}
              <div className="flex gap-x-2 items-center">
                <NetworkIntelligence className="w-6 h-6 fill-current text-white" />
                <p className="switzer-500 text-xl">{model.provider}</p>
                {model.isNew && (
                  <div className="ml-auto w-8 h-4 rounded-md border border-white/50 flex justify-center items-center">
                    <span className="text-[0.5rem] switzer-500">NEW</span>
                  </div>
                )}
              </div>
              <div className="mt-auto flex">
                <p className="inter-600 text-xs">{model.model_name}</p>
                <p className="ml-auto inter-600 text-xs">{model.parameters}</p>
              </div>
            </motion.div>
          ))
        ) : (
          <div className="p-2">
            <p className="switzer-500 text-sm">No model found.</p>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default ModelBox;
