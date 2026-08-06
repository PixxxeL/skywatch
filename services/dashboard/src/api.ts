export interface DailyStat {
    day: string
    classification: string
    cnt: number
}

export interface ClassCount {
    classification: string
    cnt: number
}

export interface Alert {
    object_id: string
    event_ts: string
    ra: number
    dec: number
    magpsf: number
    fid: number
    classification: string
    class_score: number
}

export interface HistoryPoint {
    event_ts: string
    magpsf: number
    sigmapsf: number
    fid: number
}

async function get<T>(url: string): Promise<T> {
    const resp = await fetch(url)
    if (!resp.ok) {
        throw new Error(`${url}: ${resp.status}`)
    }
    return resp.json()
}

export async function fetchDailyStats(days: number): Promise<DailyStat[]> {
    const rows = await get<DailyStat[]>(`/api/stats/daily?days=${days}`)
    return rows.map(r => ({ ...r, cnt: Number(r.cnt) }))
}

export async function fetchClassCounts(): Promise<ClassCount[]> {
    const rows = await get<ClassCount[]>('/api/stats/classes')
    return rows.map(r => ({ ...r, cnt: Number(r.cnt) }))
}

export interface AlertFilters {
    limit: number
    classification: string
    dateFrom: string
    dateTo: string
}

export function fetchLatestAlerts(filters: AlertFilters): Promise<Alert[]> {
    const params = new URLSearchParams({ limit: String(filters.limit) })
    if (filters.classification) {
        params.set('classification', filters.classification)
    }
    if (filters.dateFrom) {
        params.set('date_from', filters.dateFrom)
    }
    if (filters.dateTo) {
        params.set('date_to', filters.dateTo)
    }
    return get(`/api/alerts/latest?${params}`)
}

export function fetchObjectHistory(objectId: string): Promise<HistoryPoint[]> {
    return get(`/api/objects/${encodeURIComponent(objectId)}`)
}

export interface InterestingObject {
    object_id: string
    classification: string
    n_events: number
    amplitude: number
}

export async function fetchInterestingObjects(): Promise<InterestingObject[]> {
    const rows = await get<InterestingObject[]>('/api/objects/interesting?limit=15&min_events=5')
    return rows.map(r => ({ ...r, n_events: Number(r.n_events) }))
}
