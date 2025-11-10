import React, { useState, ReactNode } from "react";
import { OptionsContext } from "@/app/context/chatbot/OptionsContext";

interface OptionsProviderProps {
  children: ReactNode;
  wsRef: React.Reference;
}

const OptionsProvider: React.FC<OptionsProviderProps> = ({
  children,
  wsRef,
}) => {
  const [hideExtraOptions, setHideExtraOptions] = useState<boolean>(true);
  const [selectedModel, setSelectedModel] = useState<string | null>(
    "Kimi-k2-instruct-0905"
  );
  const [hideModelBox, setHideModelBox] = useState<boolean>(true);

  return (
    <OptionsContext.Provider
      value={{
        wsRef,
        hideExtraOptions,
        setHideExtraOptions,
        selectedModel,
        setSelectedModel,
        hideModelBox,
        setHideModelBox,
      }}
    >
      {children}
    </OptionsContext.Provider>
  );
};

export default OptionsProvider;
