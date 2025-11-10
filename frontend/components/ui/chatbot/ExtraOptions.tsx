import { useState, useContext, useRef, useEffect } from "react";
import { OptionsContext } from "@/app/context/chatbot/OptionsContext";

const ExtraOptions = (): React.ReactElement | null => {
  const { hideExtraOptions, setHideExtraOptions } = useContext(OptionsContext);
  const scrollInterval = useRef<NodeJS.Timeout | null>(null);
  const overlayRef = useRef<HTMLDivElement | null>(null);
  const [hasScrolled, setHasScrolled] = useState<boolean>(false);
  const scrollY = useRef(0);
  const controls = useAnimation();

  useEffect(() => {
    if (hideExtraOptions) return;
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        overlayRef.current &&
        !overlayRef.current.contains(e.target as Node)
      ) {
        setHideExtraOptions(true);
      }
    };
    document.addEventListener("click", handleOutsideClick);

    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  }, [hideExtraOptions, setHideExtraOptions]);

  if (hideExtraOptions) return null;

  const startScrolling = (direction: "up" | "down") => {
    stopScrolling();

    scrollInterval.current = setInterval(() => {
      scrollY.current += direction === "down" ? -2 : 2;
      scrollY.current = Math.max(Math.min(scrollY.current, 0), -450);
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
  interface OptionProps {
    title: string;
    isNew: boolean | null;
    description: string;
    isImage: boolean | null;
    icon: React.ElementType;
  }
  const Option: FC<OptionProps> = ({
    title,
    icon: Icon,
    description,
    isNew,
    isImage,
  }) => (
    <motion.div
      onClick={() => {
        setHideExtraOptions(true);
      }}
      whileHover={{ scale: 1.01 }}
      transition={{ duration: 0.2, ease: easeInOut }}
      id={`${title}-generation-box`}
      className="relative flex flex-col items-center shadow-xs h-max gap-y-1 p-2 cursor-pointer border rounded-md border-black/5"
    >
      {isImage ? (
        <Image
          className="rounded-md w-40 h-36 object-cover object-top"
          src={Image1}
          alt="smiling boy"
        ></Image>
      ) : (
        <video
          className="w-40 h-56 rounded-md object-cover object-top"
          src="/videos/ai_video.mp4"
          autoPlay
          muted
          playsInline
          loop
        ></video>
      )}
      {isNew && (
        <div className="absolute w-8 rounded-sm h-4 right-2 top-1 shadow-md bg-amber-400 flex justify-center items-center">
          <span className="poppins-semibold text-[0.6rem] text-white">NEW</span>
        </div>
      )}
      <div className="relative flex">
        <p className="switzer-500 text-sm">
          {title}
          <br />
          <span className="text-black/50">{description}</span>
        </p>
        <motion.div className="absolute border border-black/5 flex justify-center items-center w-4.5 h-4.5 rounded-sm right-0 bottom-0 hover:text-black/90 text-black/70">
          <FullSizeIcon className="w-3.5 h-3.5 fill-current " />
        </motion.div>
      </div>
    </motion.div>
  );

  return (
    <motion.div
      ref={overlayRef}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute right-57 backdrop-blur-md bottom-14 rounded-lg w-50 h-58 p-2 shadow-md bg-white/80 border border-black/10 overflow-x-clip overflow-y-hidden"
    >
      <motion.div
        className="flex flex-col gap-y-4 w-full justify-center"
        animate={controls}
      >
        <Option
          title="Image Generation"
          description="Powerful, high-quality image generation through our latest state of the art diffusion models."
          icon={ImageIcon}
          isNew={true}
          isImage={true}
        />
        <Option
          title="Video Generation"
          description="Seamless, realistic and and modernist ultra high quality videos through our latest Generative AI models."
          isImage={false}
          icon={ImageIcon}
          isNew={true}
        />
      </motion.div>
      <div className="relative sticky -bottom-3 w-full h-10 pointer-events-none flex justify-center items-center">
        {/* Blurred background layer */}
        <div className="absolute inset-0 bg-white blur-xs" />

        {/* Arrow layer (not blurred) */}
        <div className={`flex w-full mb-2`}>
          <div
            className="w-6 h-6 ml-19 shadow-sm relative flex justify-center items-center rounded-full hover:bg-black/10 border hover:inset-shadow-black/10 border-black/5 pointer-events-auto cursor-pointer"
            onMouseEnter={() => {
              startScrolling("down");
            }}
            onMouseLeave={stopScrolling}
          >
            <DownArrow className="w-4 h-4" />
          </div>
          {hasScrolled && (
            <div
              className="w-6 h-6 ml-auto shadow-sm relative flex justify-center items-center rounded-full hover:bg-black/10 border hover:inset-shadow-black/10 border-black/5 pointer-events-auto cursor-pointer"
              onMouseEnter={() => {
                startScrolling("up");
              }}
              onMouseLeave={stopScrolling}
            >
              <DownArrow className="rotate-180 w-4 h-4" />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export { ExtraOptions };
