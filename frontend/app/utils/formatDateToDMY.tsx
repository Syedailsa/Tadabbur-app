const formatDateToDMY = (dateString: string | null): string => {
    const date = new Date(dateString || new Date());
    const day = date.getDate().toString().padStart(2, "0");
    const month = (date.getMonth() + 1).toString().padStart(2, "0");
    const year = date.getFullYear();

    return `${day}-${month}-${year}`;
};

export default formatDateToDMY