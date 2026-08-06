export interface ClassLabel {
    short: string
    full: string
}

const CLASS_LABELS: Record<string, ClassLabel> = {
    sso_ztf_candidates: {
        short: 'Asteroids',
        full: 'Solar System objects (mostly asteroids), Fink topic fink_sso_ztf_candidates_ztf',
    },
    sn_candidates: {
        short: 'SN candidates',
        full: 'Supernova candidates, Fink topic fink_sn_candidates_ztf',
    },
}

export function classLabel(name: string): ClassLabel {
    return CLASS_LABELS[name] ?? { short: name, full: name }
}

export const FILTER_LABELS: Record<number, ClassLabel> = {
    1: { short: 'g', full: 'g band — green filter, ~472 nm' },
    2: { short: 'r', full: 'r band — red filter, ~634 nm' },
}
