import { useContext, useEffect, useRef } from "react"
import { motion } from "framer-motion"
import { ChatContext } from "@/app/context/chatbot/ChatContext"
import ProtectedImage from "./ProtectedImage";

const ImageContainer = ({ images }: { images: { image_url: string }[] }) => {
    const overlayRef = useRef<HTMLDivElement>(null)
    
    const { setOpenImageContainer, currentMode } = useContext(ChatContext)!

    const backgroundTheme = currentMode === "normal" ? "white" : "black"
    const fontTheme = currentMode === "normal" ? "black" : "white"
    useEffect(() => {

        const handleOutsideClick = (e: MouseEvent) => {
            if (overlayRef.current && !overlayRef.current.contains(e.target as Node)) {
                setOpenImageContainer(false)
            }
        }
        document.addEventListener('click', handleOutsideClick)

        return () => {
            document.removeEventListener('click', handleOutsideClick)
        }
    }, [setOpenImageContainer])
    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3, ease: "linear" }} className="absolute w-screen h-screen flex justify-center items-center backdrop-blur-md px-2 z-40">
            <div ref={overlayRef} className={`p-2 border border-black/10 bg-${backgroundTheme} rounded-md flex flex-col w-[90%] max-w-160 h-[60%] max-h-160 gap-y-2 border-${fontTheme}/10`}>
                <div>
                    <p className={`roboto-500 text-lg tracking-tight px-1 text-${fontTheme}/80`}>Your images</p>
                </div>
                {images && images.length>0 ? (
                <div className={`grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1 px-2 h-max max-h-80 max-w-200 overflow-x-hidden ${currentMode === "normal" ? " overflow-y-auto" : "black-scrollbar"}`}>

                    {images?.map((record, idx) => {
                        return (
                            <motion.div key={idx} className={`cursor-pointer border border-${fontTheme}/10`} whileHover={{ scale: 1.01 }} transition={{ duration: 0.4, ease: "linear" }}>

                                <ProtectedImage filename={record.image_url} alt={`image${idx + 1}`} />
                            </motion.div>
                        )
                    })}
                </div>
                ):(<div>
                    <p className = {`switzer-500 text-${fontTheme}/70`}>No images to show.</p>
                </div>)}
            </div>
        </motion.div >
    )
}

export default ImageContainer