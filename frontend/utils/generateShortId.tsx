const generateShortId = (): string =>
  Math.random().toString(36).substring(2, 8);

export default generateShortId;
