import { motion, useAnimation } from "framer-motion"
import { StoryParagraph } from "../interfaces/ChatMessage"
import { useCallback, useContext, useEffect, useRef, useState } from "react"
import ArrowLeft from "../../../../icons/arrow-left-bold.svg"
import FullSizeIcon from "../../../../icons/full_size_icon.svg"
import { ChatContext } from "@/app/context/chatbot/ChatContext"
import DownArrow from "../../../../icons/down-arrow-white.svg"
import ProtectedImage from "./ProtectedImage";

const FullViewStoryContainer = ({ story_data }: { story_data: StoryParagraph[] }) => {
    const { setOpenFullStoryView } = useContext(ChatContext)!
    const [activeIndex, setActiveIndex] = useState<number>(0)
    const dataLength = story_data.length ?? 0
    const scrollInterval = useRef<NodeJS.Timeout | null>(null);
    const [hasScrolled, setHasScrolled] = useState<boolean>(false);
    const scrollY = useRef(0);
    const controls = useAnimation()
    const contentRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [translateAmount, setTranslateAmount] = useState<number>(0)
    const translationOffset = 100 + 5       // 5 extra 5 for spacing offset


    const swipe = useCallback(({ direction }: { direction: string }) => {
        switch (direction) {
            case "right":
                if (activeIndex < dataLength - 1) {
                    setActiveIndex((prev) => prev + 1)
                    const translateBy = Math.abs(translateAmount) + translationOffset
                    setTranslateAmount(-translateBy)
                    controls.start({ y: 0 })
                    scrollY.current = 0
                    setHasScrolled(false)
                }
                break
            case "left":
                if (activeIndex > 0) {
                    setActiveIndex((prev) => prev - 1)
                    const translateBy = activeIndex === 1 ? 0 : translateAmount + translationOffset
                    setTranslateAmount(translateBy)
                    controls.start({ y: 0 })
                    scrollY.current = 0
                    setHasScrolled(false)
                }
                break
            default:
                break

        }
    },[activeIndex, dataLength, translateAmount, translationOffset, controls])
    // navigation through left-right keys
    useEffect(() => {
        const handleNavigation = (e: KeyboardEvent) => {
            if (e.key === "ArrowRight") {
                swipe({ direction: "right" })
            } else if (e.key === "ArrowLeft") {
                swipe({ direction: "left" })
            }
        }

        window.addEventListener("keydown", handleNavigation)

        return () => {
            window.removeEventListener("keydown", handleNavigation)
        }
    }, [swipe])

    const startScrolling = (direction: "up" | "down") => {
        if (!contentRef.current || !containerRef.current) return;

        const containerHeight = containerRef.current.clientHeight;
        const contentHeight = contentRef.current.scrollHeight;
        const maxScroll = -((contentHeight - containerHeight) + 14);

        stopScrolling();
        scrollInterval.current = setInterval(() => {
            scrollY.current += direction === "down" ? -1 : 1;
            scrollY.current = Math.max(Math.min(scrollY.current, 0), maxScroll);
            controls.start({ y: scrollY.current, transition: { duration: 0.1 } });
            setHasScrolled(scrollY.current < 0);
        }, 20);
    };

    const stopScrolling = () => {
        if (scrollInterval.current) {
            clearInterval(scrollInterval.current);
            scrollInterval.current = null;
        }
    };

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

            <div className="flex flex-col md:flex-row gap-y-6 py-8 md:py-16 md:px-6 justify-center items-center bg-black/80 backdrop-blur-md rounded-lg w-[90%] max-w-200 border border-white/5 shadow-2xl shadow-zinc-800 relative">
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
                                        <motion.div animate={{ width: "30%", height: "max-content" }}
                                            transition={{ duration: 0.5, ease: "linear" }}
                                        >
                                            <ProtectedImage
                                                className="rounded-md"
                                                filename={seg.image}
                                                alt={`image${idx + 1}`}
                                            />
                                        </motion.div>
                                    </div>
                                )
                            }
                            else if (activeIndex === idx) {
                                return (
                                    <div key={idx} className="flex justify-center w-full shrink-0">
                                        <motion.div initial={{ width: "80%", height: "max-content" }} 
                                            transition={{ duration: 0.5, ease: "linear" }}
                                        >
                                            <ProtectedImage
                                                className="rounded-md"
                                                filename={seg.image}
                                                alt={`image${idx + 1}`}
                                            />
                                        </motion.div>
                                    </div>
                                )
                            }
                            else {
                                return (
                                    <div key={idx} className="flex justify-center w-full shrink-0">
                                        <motion.div animate={{ width: "80%", height: "max-content" }}
                                            transition={{ duration: 0.5, ease: "linear" }}
                                        >
                                            <ProtectedImage
                                                className="rounded-md"
                                                filename={seg.image}
                                                alt={`image${idx + 1}`}
                                            />
                                        </motion.div>
                                    </div>
                                )
                            }
                        })}
                    </motion.div>
                </motion.div>
                {story_data[activeIndex] && (
                    <motion.div ref={containerRef} className="w-[80%] h-30 md:h-45 overflow-y-hidden relative overflow-x-clip">
                        <motion.div ref={contentRef} drag="y" dragConstraints={containerRef} animate={controls} className="flex flex-col gap-y-1 items-center ">
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

                        </motion.div>
                        {/* relative sticky */}
                        <div className="absolute -left-2 -bottom-2 w-[104%] h-6 pointer-events-none flex justify-center items-center">
                            {/* Blurred background layer */}
                            <div className="absolute inset-0 bg-black blur-[5px]" />
                        </div>


                    </motion.div>
                )}
                {/* Arrow layer (not blurred) */}
                <div className={`absolute bottom-1 w-full gap-x-2 justify-center mb-2 hidden sm:flex`}>
                    <div
                        className="w-6 h-6 shadow-sm relative flex justify-center items-center rounded-full hover:bg-white/10 border hover:inset-shadow-white/10 border-white/20 pointer-events-auto cursor-pointer"
                        onMouseEnter={() => {
                            startScrolling("down");
                        }}
                        onMouseLeave={stopScrolling}
                    >
                        <DownArrow className="w-5 h-5" />
                    </div>
                    <motion.div
                        animate={{ opacity: hasScrolled ? 1 : 0.5, cursor: hasScrolled ? "pointer" : "default", pointerEvents: hasScrolled ? "auto" : "none" }}
                        whileHover={hasScrolled ? { backgroundColor: "#FFFFFF1A" } : {}}
                        className="w-6 h-6 shadow-sm relative flex justify-center items-center rounded-full border hover:inset-shadow-white/10 border-white/20"
                        onMouseEnter={() => {
                            startScrolling("up");
                        }}
                        onMouseLeave={stopScrolling}
                    >
                        <DownArrow className="rotate-180 w-5 h-5" />
                    </motion.div>

                </div>

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

export default FullViewStoryContainer















