import { createContext } from "react";

export interface OptionsContextType {
  hideExtraOptions: boolean;
  setHideExtraOptions: React.Dispatch<React.SetStateAction<boolean>>;
  selectedModel: string;
  setSelectedModel: React.Dispatch<React.SetStateAction<string>>;
  hideModelBox: boolean;
  setHideModelBox: React.Dispatch<React.SetStateAction<boolean>>;
}
const OptionsContext = createContext<OptionsContextType | any>(null);

export { OptionsContext };
