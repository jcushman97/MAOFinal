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