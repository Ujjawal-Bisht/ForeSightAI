def is_duplicate_hash(review_hash, connection):
    """
    Check whether a review hash already exists in PostgreSQL.

    Returns
    -------
    bool
        True  -> hash already exists
        False -> hash is new
    """

    query = """
        SELECT 1
        FROM review_dedupe
        WHERE review_hash = %s
        LIMIT 1;
    """

    with connection.cursor() as cur:
        cur.execute(query, (review_hash,))
        result = cur.fetchone()

    return result is not None


def insert_review_hash(review_hash, connection):
    """
    Insert a review hash into PostgreSQL.

    Returns
    -------
    bool
        True  -> hash was newly inserted
        False -> hash already existed
    """

    query = """
        INSERT INTO review_dedupe (review_hash)
        VALUES (%s)
        ON CONFLICT (review_hash) DO NOTHING
        RETURNING review_hash;
    """

    with connection.cursor() as cur:
        cur.execute(query, (review_hash,))
        result = cur.fetchone()

    return result is not None