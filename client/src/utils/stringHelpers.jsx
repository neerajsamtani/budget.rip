function isAlphanumeric(str) {
    return /^[a-zA-Z0-9]+$/.test(str);
}

function removePrefixes(inputString) {
    // Define prefixes to remove
    const prefixesToRemove = ["SQ *", "TST* "];

    // Iterate through prefixes and remove them if found at the start of the string
    for (const prefix of prefixesToRemove) {
        if (inputString.startsWith(prefix)) {
            return inputString.slice(prefix.length);
        }
    }

    // If no matching prefix found, return the original string
    return inputString;
}

function titleCase(str) {
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

export default function defaultNameCleanup(str) {
    return titleCase(removePrefixes(str))
}