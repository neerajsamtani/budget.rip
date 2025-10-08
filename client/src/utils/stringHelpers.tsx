function isAlphanumeric(str: string) {
    return /^[a-zA-Z0-9]+$/.test(str);
}

function removePrefixes(inputString: string) {
    // Define prefixes to remove
    // These are inserted by payment processors or platforms like Square and Toast
    const prefixesToRemove = ["SQ *", "TST* ", "TST*", "SP ", "DD *DOORDASH "];

    // Iterate through prefixes and remove them if found at the start of the string
    for (const prefix of prefixesToRemove) {
        if (inputString.startsWith(prefix)) {
            return inputString.slice(prefix.length);
        }
    }

    // If no matching prefix found, return the original string
    return inputString;
}

function titleCase(str: string) {
    return str
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9&\-\s]/gi, '')
        .split(' ')
        .map(function (word) {
            if (!isAlphanumeric(word)) {
                return word
            }
            return word.replace(word[0], word[0].toUpperCase());
        })
        .join(' ');
}

export default function defaultNameCleanup(str: string) {
    return titleCase(removePrefixes(str))
}