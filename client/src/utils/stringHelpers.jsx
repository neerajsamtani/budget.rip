export default function titleCase(str) {
    return str
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9&\-\s]/gi, '')
        .split(' ')
        .map(function (word) {
            return word.replace(word[0], word[0].toUpperCase());
        })
        .join(' ');
}
