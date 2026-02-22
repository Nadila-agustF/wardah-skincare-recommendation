def generate_id(cursor, table, column, prefix, digit=3):
    query = f"""
        SELECT {column}
        FROM {table}
        WHERE {column} LIKE '{prefix}%'
        ORDER BY {column} DESC
        LIMIT 1
    """
    cursor.execute(query)
    last_id = cursor.fetchone()

    if last_id:
        number = int(last_id[0].replace(prefix, ""))
        new_number = number + 1
    else:
        new_number = 1

    return f"{prefix}{str(new_number).zfill(digit)}"
        