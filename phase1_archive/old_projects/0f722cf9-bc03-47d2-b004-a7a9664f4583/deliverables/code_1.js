const generateRandomHSL = () => {

    const h = Math.floor(Math.random() * 360);

    const s = Math.floor(Math.random() * 100);

    const l = Math.floor(Math.random() * 100);

    return { h, s, l };