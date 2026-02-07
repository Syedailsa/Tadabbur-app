import Verse from "./Verse";


interface Surah {
    number: number;
    name: string;
    englishName: string;
    englishNameTranslation: string;
    revelationType: string;
    ayahs: Verse[]
}


interface SurahForVerseImages {
    name: string;
    englishName: string;
    ayahs: Verse[]
}

export default Surah