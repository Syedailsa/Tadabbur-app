import { animate, easeInOut, motion, spring } from "framer-motion"
import { StoryParagraph } from "../interfaces/ChatMessage"
import { useContext, useEffect, useState } from "react"
import ArrowLeft from "../../../../icons/arrow-left-bold.svg"
import FullSizeIcon from "../../../../icons/full_size_icon.svg"
import { ChatContext } from "@/app/context/chatbot/ChatContext"

const FullStoryViewContainer = ({ story_data }: { story_data: StoryParagraph[] }) => {
    const { setOpenFullStoryView } = useContext(ChatContext)!
    const [activeIndex, setActiveIndex] = useState<number>(0)
    const dataLength = story_data.length ?? 0
    const translationOffset = 100 + 5

    const [translateAmount, setTranslateAmount] = useState<number>(0)
    const swipe = ({ direction }: { direction: string }) => {
        switch (direction) {
            case "right":
                if (activeIndex < dataLength - 1) {
                    setActiveIndex((prev) => prev + 1)
                    const translateBy = Math.abs(translateAmount) + translationOffset
                    setTranslateAmount(-translateBy)
                }
                break
            case "left":
                if (activeIndex > 0) {
                    setActiveIndex((prev) => prev - 1)
                    const translateBy = activeIndex === 1 ? 0 : translateAmount + translationOffset
                    setTranslateAmount(translateBy)
                }
                break
            default:
                break

        }
    }
    useEffect(() => {
        console.log("activeIndex", activeIndex)
    }, [activeIndex])
    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, ease: "linear" }} className="absolute w-screen h-screen flex items-center backdrop-blur-xl lg z-30 justify-center px-8">

            <motion.div onClick={() => {
                swipe({ direction: "left" })

            }}
                animate={{ color: activeIndex > 0 ? "#ffffff" : "#FFFFFF80" }}
                style={{ cursor: activeIndex > 0 ? "pointer" : "default" }}
                className="absolute left-4 text-indigo-400 z-10">
                <ArrowLeft className={`w-6 h-6 fill-current`} />
            </motion.div>

            <div className="flex flex-col md:flex-row md:gap-x-8 gap-y-6 py-8 md:py-16 justify-center items-center bg-black/80 backdrop-blur-md rounded-lg w-[90%] max-w-200 border border-white/5 shadow-2xl shadow-zinc-800 relative">
                <div onClick={() => {
                    setOpenFullStoryView(false)
                }} className="absolute top-3 left-3 flex gap-x-2 items-center cursor-pointer rounded-md border border-white/5 px-2 py-0.5 text-red-500 hover:text-red-600">
                    <FullSizeIcon className="w-2.5 h-2.5 fill-current" />
                    <p className="switzer-500 text-[13px]">Exit full mode</p>
                </div>
                {/* add a dummy box */}
                <div className="w-full h-4 md:hidden"></div>
                <motion.div className="w-full px-4 overflow-x-hidden">
                    <motion.div animate={{ x: `${translateAmount}%` }}
                        transition={{ duration: 0.5, ease: "linear" }} className="flex gap-x-4 w-full items-center">
                        {story_data.map((seg, idx) => {
                            if (activeIndex < idx) {
                                return (
                                    <div key={idx} className="flex justify-center w-full shrink-0">
                                        <motion.img
                                            animate={{ width: "30%", height: "max-content" }}
                                            transition={{duration:0.5, ease:"linear"}}
                                            className="rounded-md"
                                            src={seg.image}
                                            alt={`image${idx + 1}`}
                                        />
                                    </div>
                                )
                            }
                            else if (activeIndex === idx) {
                                return (
                                    <div key={idx} className="flex justify-center w-full shrink-0">
                                        <motion.img
                                            animate={{ width: "70%", height: "max-content" }}
                                            transition={{ duration: 0.2, ease: "linear" }}
                                            className="rounded-md"
                                            src={seg.image}
                                            alt={`image${idx + 1}`}
                                        />
                                    </div>
                                )
                            }
                            else {
                                return (
                                    <div key={idx} className="flex justify-center w-full shrink-0">
                                        <motion.img
                                            animate={{ width: "30%", height: "max-content" }}
                                            transition={{ duration: 0.5, ease: "linear" }}
                                            className="rounded-md"
                                            src={seg.image}
                                            alt={`image${idx + 1}`}
                                        />
                                    </div>
                                )
                            }
                        })}
                    </motion.div>
                </motion.div>
                {story_data[activeIndex] && (
                    <div className="flex flex-col gap-y-1 items-center w-[80%]">
                        <p className="roboto-600 text-xl tracking-tight text-white self-start">
                            {activeIndex + 1}. {story_data[activeIndex].paragraph_title}
                        </p>
                        <div className="rounded-md relative">
                            <div className="h-max px-1 flex flex-col">
                                <div id="paragraph">
                                    <p className="roboto-500 text-white/80 text-[0.9rem]">
                                        {story_data[activeIndex].story_paragraph}
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
                className="absolute rotate-180 right-4 z-10">
                <ArrowLeft className="w-6 h-6 fill-current" />
            </motion.div>
        </motion.div>
    )
}

export default FullStoryViewContainer