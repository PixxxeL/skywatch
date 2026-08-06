DAILY_STATS = '''
    SELECT day, classification, sum(cnt) AS cnt
    FROM skywatch.alerts_daily
    WHERE day >= today() - {days:UInt32}
    GROUP BY day, classification
    ORDER BY day
    '''

CLASS_COUNTS = '''
    SELECT classification, uniqExact(candidate_id) AS cnt
    FROM skywatch.ztf_alerts
    GROUP BY classification
    ORDER BY cnt DESC
    '''

LATEST_ALERTS = '''
    SELECT object_id, event_ts, ra, dec, magpsf, fid, classification, class_score
    FROM skywatch.ztf_alerts
    WHERE ({cls:String} = '' OR classification = {cls:String})
        AND toDate(event_ts) >= {date_from:Date}
        AND toDate(event_ts) <= {date_to:Date}
    ORDER BY event_ts DESC
    LIMIT 1 BY object_id, candidate_id
    LIMIT {limit:UInt32}
    '''

INTERESTING_OBJECTS = '''
    SELECT
        object_id,
        any(classification) AS classification,
        uniqExact(candidate_id) AS n_events,
        round(max(magpsf) - min(magpsf), 2) AS amplitude
    FROM skywatch.ztf_alerts
    GROUP BY object_id
    HAVING n_events >= {min_events:UInt32}
    ORDER BY amplitude DESC
    LIMIT {limit:UInt32}
    '''

OBJECT_HISTORY = '''
    SELECT event_ts, magpsf, sigmapsf, fid
    FROM skywatch.ztf_alerts FINAL
    WHERE object_id = {object_id:String} ORDER BY event_ts
    '''
