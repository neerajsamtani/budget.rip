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

interface SuggestionEvidence {
    source?: string | null;
    matched_hint_name?: string | null;
    source_metadata?: { primary_label?: string; detailed_label?: string | null; selected_count?: number } | null;
}

/** Why a category was suggested, worded the same in the create-event modal and the review list. */
export function formatSuggestionSource(suggestion: SuggestionEvidence): string {
    if (suggestion.source !== 'stripe_personal_finance') {
        return suggestion.matched_hint_name ? `Hint: ${suggestion.matched_hint_name}` : 'Event hint';
    }
    const metadata = suggestion.source_metadata;
    if (metadata?.selected_count) return `Stripe: all ${metadata.selected_count} transactions`;
    // Prefer the detailed label, humanized: "fast_food" → "Fast food".
    const label = metadata?.detailed_label || metadata?.primary_label;
    return label ? `Stripe: ${label.replaceAll('_', ' ').replace(/^./, char => char.toUpperCase())}` : 'Stripe';
}
