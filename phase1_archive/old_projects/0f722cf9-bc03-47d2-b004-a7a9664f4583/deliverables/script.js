// Color generation utilities

const generateRandomRGB = () => {

    const r = Math.floor(Math.random() * 256);

    const g = Math.floor(Math.random() * 256);

    const b = Math.floor(Math.random() * 256);

    return { r, g, b };

};



const rgbToHex = ({ r, g, b }) => {

    return '#' + [r, g, b].map(x => {

        const hex = x.toString(16);

        return hex.length === 1 ? '0' + hex : hex;

    }).join('');

};



const generateRandomHSL = () => {

    const h = Math.floor(Math.random() * 360);

    const s = Math.floor(Math.random() * 100);

    const l = Math.floor(Math.random() * 100);

    return { h, s, l };

};



const generateColorScheme = (count = 5) => {

    const baseHSL = generateRandomHSL();

    const scheme = [];

    

    // Generate analogous colors

    for (let i = 0; i < count; i++) {

        const hue = (baseHSL.h + (i * 30)) % 360;

        scheme.push({

            h: hue,

            s: baseHSL.s,

            l: baseHSL.l

        });

    }

    

    return scheme;

};



const hslToString = ({ h, s, l }) => `hsl(${h}, ${s}%, ${l}%)`;



export {

    generateRandomRGB,

    rgbToHex,

    generateRandomHSL,

    generateColorScheme,

    hslToString

};