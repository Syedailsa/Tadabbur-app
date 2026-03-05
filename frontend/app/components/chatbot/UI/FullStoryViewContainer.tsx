import { animate, easeInOut, motion, spring } from "framer-motion"
import { StoryParagraph } from "../interfaces/ChatMessage"
import { useContext, useState } from "react"
import ArrowLeft from "../../../../icons/arrow-left-bold.svg"
import FullSizeIcon from "../../../../icons/full_size_icon.svg"
import { ChatContext } from "@/app/context/chatbot/ChatContext"

const FullStoryViewContainer = ({ story_data }: { story_data: StoryParagraph[] }) => {
    const { setOpenFullStoryView } = useContext(ChatContext)!
    const [activeIndex, setActiveIndex] = useState<number>(0)
    const dataLength = story_data.length ?? 0
    const swipe = ({ direction }: { direction: string }) => {
        switch (direction) {
            case "right":
                if (activeIndex < dataLength - 1) {
                    setActiveIndex((prev) => prev + 1)
                }
                break
            case "left":
                if (activeIndex > 0) {
                    setActiveIndex((prev) => prev - 1)
                }
                break
            default:
                break

        }
    }
    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, ease: "linear" }} className="absolute w-screen h-screen flex items-center backdrop-blur-xl lg z-30 justify-center px-8">

            <motion.div onClick={() => {
                swipe({ direction: "left" })
            }}
                animate={{ color: activeIndex > 0 ? "#ffffff" : "#FFFFFF80" }}
                style={{ cursor: activeIndex > 0 ? "pointer" : "default" }}

                className="absolute left-4 text-indigo-400">
                <ArrowLeft className={`w-6 h-6 fill-current`} />
            </motion.div>

            <div className="flex flex-col md:flex-row md:gap-x-8 gap-y-6 py-8 md:py-16 px-6 md:px-8 justify-center items-center bg-black/80 backdrop-blur-md rounded-lg w-[90%] max-w-200 border border-white/5 shadow-2xl shadow-zinc-800 relative">
                <div onClick={() => {
                    setOpenFullStoryView(false)
                }} className="absolute top-3 left-3 flex gap-x-2 items-center cursor-pointer rounded-md border border-white/5 px-2 py-0.5 text-red-500 hover:text-red-600">
                    <FullSizeIcon className="w-2.5 h-2.5 fill-current" />
                    <p className="switzer-500 text-[13px]">Exit full mode</p>
                </div>
                {/* add a dummy box */}
                <div className="w-full h-4 md:hidden"></div>
                <div className="image-container relative w-[65%] sm:w-[55%] md:w-[45%] lg:w-[35%]">
                    {/* Spacer div to maintain dimensions */}
                    <div className="w-full aspect-square" /> {/* Adjust aspect ratio as needed */}
                    {story_data.map((segment, idx) => {
                        if (idx > activeIndex) {
                            return (
                                <motion.img
                                    animate={{ rotate: (idx + 1) * 3 }}
                                    transition={{ type: spring, damping: 20 }}
                                    key={idx}
                                    className="absolute top-0 left-0 w-full h-full object-cover rounded-lg"
                                    src={`data:image/png;base64,${segment.image}`}
                                    alt={`ai-image-${idx + 1}`}
                                />
                            );
                        } else if (idx < activeIndex) {
                            return (
                                <motion.img
                                    animate={{ rotate: -((idx + 1) * 8) }}
                                    transition={{ type: spring, damping: 20 }}
                                    key={idx}
                                    className="absolute top-0 left-0 w-full h-full object-cover  rounded-lg"
                                    src={`data:image/png;base64,${segment.image}`}
                                    alt={`ai-image-${idx + 1}`}
                                />
                            );
                        } else {
                            return (
                                <motion.div
                                    key={idx}>
                                    <img
                                        className="absolute top-0 left-0 w-full h-full object-cover rounded-lg z-30 border border-white/30"
                                        src={`data:image/png;base64,${segment.image}`}
                                        alt={`ai-image-${idx + 1}`}
                                    />
                                    {/* <div className="absolute bottom-0 w-full h-8 bg-white/20 z-40 rounded-full border border-white/20 backdrop-blur-sm"></div> */}
                                </motion.div>
                            );
                        }
                    })}
                </div>
                {story_data[activeIndex] && (
                    <div className="flex flex-col gap-y-1 items-center w-[80%]">
                        <p className="roboto-600 text-xl tracking-tight text-white self-start">
                            {activeIndex + 1}. {story_data[activeIndex].paragraph_title}
                        </p>
                        <div className="rounded-md relative">
                            <div className="h-max px-1 flex flex-col">
                                <div id="paragraph">
                                    <p className="roboto-500 text-white/80 text-[0.9rem]">
                                        {story_data[activeIndex].story_paragraph.slice(0, 200)}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

            </div>
            <motion.div onClick={() => {
                swipe({ direction: "right" })
            }}
                animate={{ color: activeIndex < dataLength - 1 ? "#ffffff" : "#FFFFFF80" }}
                style={{ cursor: activeIndex < dataLength - 1 ? "pointer" : "default" }}
                className="absolute rotate-180 right-4">
                <ArrowLeft className="w-6 h-6 fill-current" />
            </motion.div>
        </motion.div>
    )
}

export default FullStoryViewContainer