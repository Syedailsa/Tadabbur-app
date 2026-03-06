import DisclaimerIcon from "../../../../icons/disclaimer.svg";
import { ChatContext } from "@/app/context/chatbot/ChatContext";
import { reportOptions } from "@/static/data";
import { useContext, useState } from "react";
import { easeInOut, motion } from "framer-motion";
import { wsSendAsync } from "@/app/utils/retryOpernation";

interface ReportContenDialogueBoxProps {
  hideReportContentDialogueBox: boolean | null;
  setHideReportContentDialogueBox: React.Dispatch<
    React.SetStateAction<boolean | null>
  >;
}

const ReportContentDialogueBox: React.FC<ReportContenDialogueBoxProps> = ({
  hideReportContentDialogueBox,
  setHideReportContentDialogueBox,
}) => {
  const { wsRef, reportedMessageID } = useContext(ChatContext)!;
  const [hidePlaceholder, setHidePlaceholder] = useState<boolean>(true);
  const [selectedReason, setSelectedReason] = useState<string | null>("");
  const [customFeedback, setCustomFeedback] = useState<string | null>("");
  if (hideReportContentDialogueBox) return null;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setSelectedReason(e.target.value);
  };
  const handleSubmit = () => {
    if (!selectedReason || !reportedMessageID) return;

    if (selectedReason === "other") {
      if (!customFeedback) return;
      wsSendAsync(
        wsRef?.current, {
        type: "report",
        message_id: reportedMessageID,
        feedback: customFeedback,
      }).catch(() => { })

    } else {
      wsSendAsync(
        wsRef?.current, {
        type: "report",
        message_id: reportedMessageID,
        feedback: selectedReason,
      }).catch(() => { })

    }
    setHideReportContentDialogueBox(true);
  };
  return (
    <div className="absolute w-screen h-screen flex justify-center items-center backdrop-blur-sm z-40">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, ease: "easeInOut" }}
        className="w-[90%] max-w-120 h-max bg-white px-2 py-3 border border-black/10 rounded-md shadow-md"
      >
        <div className="w-full h-full flex flex-col">
          <div className="w-full flex pl-2 justify-between">
            <p className="mb-1 inter-600 tracking-tight">
              What is wrong in the response
            </p>
            <DisclaimerIcon className="w-5 h-5" />
          </div>
          <form className="overflow-y-auto px-2 max-h-80">
            <div className="radio-group">
              {reportOptions?.map((option) => (
                <div
                  key={option.id}
                  className="radio-option border-b border-black/5 py-1"
                >
                  <input
                    type="radio"
                    id={option.id}
                    name="reportReason"
                    value={option.value}
                    checked={selectedReason === option.value}
                    onChange={(e) => {
                      handleChange(e);
                      if (option.id == "other") {
                        console.log("! done");
                        setHidePlaceholder(false);
                      }
                    }}
                  />
                  <label
                    className="ml-2 switzer-500 tracking-tight text-black/70"
                    htmlFor={option.id}
                  >
                    {option.label}
                  </label>
                </div>
              ))}
            </div>
          </form>

          <div className="relative">
            {selectedReason === "other" && (
              <div>
                <div
                  onInput={(e) => {
                    const target = e.target as HTMLDivElement;
                    const text = target.textContent.trim() ?? "";
                    setHidePlaceholder(text != "");
                    setCustomFeedback(text);
                  }}
                  contentEditable
                  className="focus:outline-none switzer-500 w-full border border-black/20 tracking-tight rounded-sm max-h-20 px-2 py-1 overflow-y-auto"
                ></div>

                {!hidePlaceholder && (
                  <span className="absolute left-2 text-[0.9rem] text-black/60 switzer-500 top-1.5 tracking-tight pointer-events-none">
                    The response is offensive, unauthentic
                  </span>
                )}
              </div>
            )}
          </div>
          <div className="flex gap-x-2 self-end-safe mt-2">
            <motion.button
              onClick={handleSubmit}
              whileHover={{ scale: 1.02 }}
              transition={{ duration: 0.25, ease: easeInOut }}
              className="bg-black cursor-pointer text-white rounded-md px-2 py-1 switzer-500"
            >
              Submit
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.02 }}
              transition={{ duration: 0.25, ease: easeInOut }}
              onClick={() => {
                setHideReportContentDialogueBox(true);
              }}
              className="bg-red-400 hover:bg-red-500 cursor-pointer text-white rounded-md px-2 py-1 switzer-500"
            >
              Cancel
            </motion.button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ReportContentDialogueBox;
