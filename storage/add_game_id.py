import sqlite3

def add_auto_increment_id(db_path, table_name, id_prefix="C"):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(f'PRAGMA table_info("{table_name}")')
        columns_info = cursor.fetchall()

        if not columns_info:
            # Table doesn't exist, handle error or return silently
            if conn: conn.close()
            return

        column_names = [col[1] for col in columns_info]
        column_names_lower = [name.lower() for name in column_names]

        if 'id' in column_names_lower:
            if conn: conn.close()
            return

        new_table_name = f"{table_name}_new_{sqlite3.version_info[0]}"

        column_definitions = []
        original_column_names_quoted = []

        for col in columns_info:
            name = col[1]
            dtype = col[2]
            not_null = col[3]
            quoted_name = f'"{name}"'
            original_column_names_quoted.append(quoted_name)
            definition = f"{quoted_name} {dtype}"
            if not_null:
                definition += " NOT NULL"
            column_definitions.append(definition)

        columns_definition_sql = ", ".join(column_definitions)
        original_columns_select_sql = ", ".join(original_column_names_quoted)
        original_columns_insert_sql = ", ".join(original_column_names_quoted)


        create_table_sql = f"""
            CREATE TABLE "{new_table_name}" (
                "id" TEXT PRIMARY KEY,
                {columns_definition_sql}
            );
        """
        cursor.execute(create_table_sql)


        select_sql = f'SELECT {original_columns_select_sql} FROM "{table_name}";'
        cursor.execute(select_sql)
        rows_to_copy = cursor.fetchall()

        placeholders = ", ".join(['?'] * len(original_column_names_quoted))
        insert_sql_template = f"""
            INSERT INTO "{new_table_name}" ("id", {original_columns_insert_sql})
            VALUES (?, {placeholders});
        """

        row_counter = 1
        for row_data in rows_to_copy:
            custom_id = f"{id_prefix}{row_counter}"
            data_to_insert = (custom_id,) + row_data
            cursor.execute(insert_sql_template, data_to_insert)
            row_counter += 1


        cursor.execute(f'DROP TABLE "{table_name}";')
        cursor.execute(f'ALTER TABLE "{new_table_name}" RENAME TO "{table_name}";')

        conn.commit()

    except sqlite3.Error as e:
        # Silently handle error or add minimal logging if needed
        # print(e) # Optional: uncomment for debugging
        if conn:
            try:
                conn.rollback()
            except sqlite3.Error:
                 pass # Ignore rollback error if transaction wasn't active

    finally:
        if conn:
            conn.close()


# Example usage
db_path = "joined_data.db"
table_name = "game_data"
custom_prefix = "C" # Define your desired prefix here

add_auto_increment_id(db_path, table_name, custom_prefix)