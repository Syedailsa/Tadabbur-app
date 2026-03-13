import { useContext, useEffect, useRef } from "react"
import { motion } from "framer-motion"
import { ChatContext } from "@/app/context/chatbot/ChatContext"

const ImageContainer = ({ images }: { images: { image_url: string }[] }) => {
    const overlayRef = useRef<HTMLDivElement>(null)
    const { setOpenImageContainer } = useContext(ChatContext)!
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
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3, ease: "linear" }} className="absolute w-screen h-screen flex justify-center items-center backdrop-blur-md px-2 z-60">
            <div ref={overlayRef} className="px-4 py-2 border border-black/10 bg-white rounded-md flex flex-col gap-y-2">
                <div>
                    <p className="roboto-600 text-lg tracking-tight">Your images</p>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-1 h-max max-h-80 max-w-200 overflow-y-auto overflow-x-hidden">

                    {images?.map((record, idx) => {
                        return (
                            <motion.div key={idx} className="cursor-pointer" whileHover={{ scale: 1.01 }} transition={{ duration: 0.4, ease: "linear" }}>
                                <img className="w-80 h-auto rounded-lg" src={record.image_url} alt={`image${idx + 1}`} />
                            </motion.div>
                        )
                    })}
                </div>
            </div>
        </motion.div >
    )
}

export default ImageContainer