"use client";

import React, { useEffect, useRef, useState } from "react";
import { SurahForAudios, SurahForVerseImages } from "../interfaces/Surah";
import { VerseForAudios, VerseForImages } from "../interfaces/Verse";
import { motion } from "framer-motion"
import ArrowLeft from "../../../../icons/arrow-down-head.svg"
import { Noto_Kufi_Arabic } from "next/font/google";
import Navigate from "../../../../icons/navigate_icon.svg"
import Diamond from "../../../../icons/diamond_icon.svg"
import OfflineBolt from "../../../../icons/offline_bolt.svg"
import List from "../../../../icons/list_icon.svg"
import Bookmark from "../../../../icons/bookmark_icon.svg"
import Image from "next/image";
import MosquePic from "../../../../images/mosque.jpg"
import HighWayPic from "../../../../images/road.jpg"
import Cluster from "../../../../images/cluster.jpg"

const noto_kufi_arabic = Noto_Kufi_Arabic({
  subsets: ['arabic'],
  weight: ['600'],
  display: 'swap',
})

type AudioDialogProps =
  | { type: "audio"; surahs: SurahForAudios[] }
  | { type: "read"; surahs: SurahForVerseImages[] };


export default function QuranDialogBox(props: AudioDialogProps) {
  const { type, surahs } = props;
  const [activeSurahIndex, setActiveSurahIndex] = useState<number>(0)
  const [openSurahDropdown, setOpenSurahDropdown] = useState<boolean>(false)
  const [activeVerseIndex, setActiveVerseIndex] = useState<number>(0)
  const [openVerseDropdown, setOpenVerseDropdown] = useState<boolean>(false)
  const [slideAmount, setSlideAmount] = useState<number>(0)

  useEffect(() => {
    setActiveVerseIndex(0)
  }, [activeSurahIndex])

  useEffect(() => {
    const id = setInterval(() => {
      setSlideAmount((prev) => (prev >= 200 ? 0 : prev + 104.5));
    }, 4000);

    return () => clearInterval(id);
  }, []);

  console.log("Surahs", surahs)
  return (
    <div className="">
      <div className={`flex gap-x-4 justify-center`}>
        {surahs?.map((surah, surah_index) =>
          surah_index === activeSurahIndex ? (
            <div className="border border-black/10 inset-shadow-2xs inset-shadow-black/5 rounded-md p-3 w-[95%] max-w-120" key={surah_index}>

              <div className="flex justify-between items-center relative">
                <motion.div onClick={() => setOpenSurahDropdown((prev) => !prev)} whileTap={{ backgroundColor: "rgba(0,0,0,0.09)" }} whileHover={{ backgroundColor: "rgba(0,0,0,0.05)" }} className="px-3 py-0.5 cursor-pointer border border-black/10 rounded-md flex justify-between items-center gap-x-2 re">
                  <Diamond className="w-5 h-5 fill-current text-yellow-600" />
                  <p className={`switzer-600 text-[1.25rem] tracking-tighter`}>Surah {surah?.englishName}</p>
                  {surahs?.length > 1 && (
                    <ArrowLeft className="w-5 h-5" />
                  )}
                </motion.div>

                {openSurahDropdown && (<SelectBox top={40} dropdownArray={surahs} openDropdown={openSurahDropdown} setOpenDropdown={setOpenSurahDropdown} activeIndex={activeSurahIndex}
                  setActiveIndex={setActiveSurahIndex} />)}

                <p lang="ar" dir="rtl" className={`${noto_kufi_arabic.className} w-max`}>{surah?.name}</p>
              </div>

              {type === "audio" && (
                <motion.div className="my-2 overflow-x-hidden">
                  <motion.div animate={{ x: `-${slideAmount}%` }} transition={{ duration: 1.2, ease: "easeInOut" }} className="flex gap-x-4">
                    <Image className="min-w-full rounded-md h-65 object-cover object-center" src={MosquePic} alt="mosque-pic" />
                    <Image className="min-w-full rounded-md h-65 object-cover object-center" src={HighWayPic} alt="highway-pic" />
                    <Image className="min-w-full rounded-md h-65 object-cover object-center" src={Cluster} alt="cluster-pic" />
                  </motion.div>
                </motion.div>
              )}


              <div style={{ height: type === "read" ? 250 : "auto", overflowY: type === "read" ? "auto" : "visible" }}>
                {surah?.ayahs?.map((ayah, ayah_index) => {
                  if (type === "audio" && activeVerseIndex !== ayah_index) return null;

                  return (
                    <div className="my-2" key={ayah_index}>
                      {type === "read" && (ayah as VerseForImages).verse_image_url && (
                        <div className="p-2 rounded-md border border-black/10">
                          <img src={(ayah as VerseForImages).verse_image_url} alt="verse-image" />
                          <div className="flex gap-x-1">
                            <div className="switzer-500 text-sm">
                              <strong>{ayah.numberInSurah}.</strong>
                            </div>
                            <p className="switzer-500 text-sm">{(ayah as VerseForImages).text}</p>
                          </div>
                        </div>
                      )}
                      <div className="my-2 text-sm flex gap-x-2 items-center relative">

                        {type === "audio" && (
                          <motion.div
                            onClick={() => {
                              setOpenVerseDropdown((prev) => !prev)
                            }}
                            whileTap={{ backgroundColor: "rgba(0,0,0,0.09)" }}
                            whileHover={{ backgroundColor: "rgba(0,0,0,0.05)" }}
                            className="flex justify-between gap-x-2 px-2 w-[40%] py-1 rounded-md border border-black/10 items-center cursor-pointer"
                          >
                            <div className="flex items-center gap-x-1">
                              <OfflineBolt className="w-5 h-5" />
                              <p className="switzer-600 tracking-tighter">Verse {ayah.numberInSurah}</p>
                            </div>
                            {surah?.ayahs?.length > 1 && (
                              <ArrowLeft className="w-4 h-4" />
                            )}
                          </motion.div>
                        )}
                        {openVerseDropdown && (
                          <SelectBox
                            top={30}
                            dropdownArray={surah.ayahs}
                            activeIndex={activeVerseIndex}
                            setActiveIndex={setActiveVerseIndex}
                            openDropdown={openVerseDropdown}
                            setOpenDropdown={setOpenVerseDropdown}
                          />
                        )}
                        {type === "audio" ? (
                          <div className="px-3 py-0.5 absolute -right-1.5 bottom-8 z-10 rounded-md bg-amber-400 shadow-sm">
                            <p className="poppins-semibold text-white/90 tracking-tighter">
                              {(surah as SurahForAudios).revelationType.toUpperCase()}
                            </p>
                          </div>
                        ) : null}
                      </div>

                      {/* audio */}
                      <div>
                        {(ayah as VerseForAudios).audio ? (
                          <audio className="w-full" controls src={(ayah as VerseForAudios).audio} />
                        ) : null}
                      </div>

                      {/* metadata */}
                      {type === "audio" && (
                        <div className="flex justify-end gap-x-2 my-3">
                          <div className="px-3 py-1 flex gap-x-2 items-center border border-green-800/10 rounded-full">
                            <Navigate className="w-5 h-5 fill-current text-green-600" />
                            <p className="poppins-semibold text-sm">Manzil: {(ayah as VerseForAudios).manzil}</p>
                          </div>

                          <div className="px-3 py-1 flex gap-x-2 items-center border border-blue-800/10 rounded-full">
                            <List className="w-5 h-5 fill-current text-blue-800" />
                            <p className="poppins-semibold text-sm">Ruku: {(ayah as VerseForAudios).ruku}</p>
                          </div>

                          <div className="px-3 py-1 flex gap-x-2 items-center border border-red-800/10 rounded-full">
                            <Bookmark className="w-5 h-5 fill-current text-red-600" />
                            <p className="poppins-bold text-sm">Juz: {(ayah as VerseForAudios).juz}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

            </div>
          ) : (null)
        )}
      </div>
    </div>
  );
}


type SurahType = SurahForAudios | SurahForVerseImages;
type VerseType = VerseForAudios | VerseForImages;

type SelectBoxProps = {
  dropdownArray: (SurahType | VerseType)[];
  openDropdown: boolean;
  setOpenDropdown: React.Dispatch<React.SetStateAction<boolean>>
  activeIndex: number;
  setActiveIndex: React.Dispatch<React.SetStateAction<number>>
  top: number
}


const SelectBox = ({
  dropdownArray,
  openDropdown,
  setOpenDropdown,
  activeIndex,
  setActiveIndex,
  top
}: SelectBoxProps) => {
  const overlayRef = useRef<HTMLDivElement>(null)

  const isSurah = (item: SurahType | VerseType): item is SurahType => {
    return "englishName" in item;
  }
  const handleOutsideClick = (e: MouseEvent) => {
    if (overlayRef.current && !overlayRef.current.contains(e.target as Node)) {
      setOpenDropdown(false)
    }
  }
  document.addEventListener('click', handleOutsideClick)
  if (!openDropdown || dropdownArray.length <= 1) {
    return null
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} style={{ top }} ref={overlayRef} className={`absolute p-1 z-10 h-max max-h-30 overflow-y-auto w-1/2 bg-gray-50 shadow-md rounded-md flex flex-col gap-y-2`}>
      {dropdownArray?.map((element, element_index) => element_index != activeIndex ? (
        <motion.div onClick={() => {
          setActiveIndex(element_index)
          setOpenDropdown(false)
        }} whileTap={{ backgroundColor: "rgba(0,0,0,0.09)" }} whileHover={{ backgroundColor: "rgba(0,0,0,0.05)" }} key={element_index} className="switzer-600 tracking-tighter px-2 py-1 rounded-md cursor-pointer">
          {isSurah(element) ? (
            <div className="flex items-center justify-between text-black/70">
              <p>{element.englishName}</p>
              <p className={`${noto_kufi_arabic.className} text-sm`}>{element.name.replace(/^سُورَةُ\s*/, "")}</p>
            </div>
          ) : (<div>
            <p className="text-black/60">Verse {element.numberInSurah}</p>
          </div>)}
        </motion.div>

      ) : (null))}
    </motion.div>
  )

}



// : type === "read" ? (
//   <div className="px-3 py-0.5 rounded-md border border-amber-800/20 ml-auto">
//     <p className="poppins-semibold  text-black tracking-tighter">
//       {surah.revelationType.toUpperCase()}
//     </p>
//   </div>
// ) 