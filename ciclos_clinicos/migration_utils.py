"""Utilidades para migraciones idempotentes (recuperación de migraciones parciales)."""


def column_exists(cursor, table, column):
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
        """,
        [table, column],
    )
    return cursor.fetchone()[0] > 0


def fk_exists(cursor, table, column, ref_table='ciclos_clinicos_cicloclinico'):
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
          AND REFERENCED_TABLE_NAME = %s
        """,
        [table, column, ref_table],
    )
    return cursor.fetchone()[0] > 0


def unique_index_exists(cursor, table, column):
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = %s
          AND NON_UNIQUE = 0
        """,
        [table, column],
    )
    return cursor.fetchone()[0] > 0


def add_bigint_column_if_missing(schema_editor, table, column, nullable=True):
    with schema_editor.connection.cursor() as cursor:
        if column_exists(cursor, table, column):
            return False
    null = 'NULL' if nullable else 'NOT NULL'
    schema_editor.execute(f'ALTER TABLE `{table}` ADD COLUMN `{column}` bigint {null}')
    return True


def add_ciclo_fk(schema_editor, table, unique=False):
    """Agrega ciclo_id + FK (+ UNIQUE opcional) si faltan."""
    with schema_editor.connection.cursor() as cursor:
        if not column_exists(cursor, table, 'ciclo_id'):
            schema_editor.execute(
                f'ALTER TABLE `{table}` ADD COLUMN `ciclo_id` bigint NULL'
            )
        if not fk_exists(cursor, table, 'ciclo_id'):
            schema_editor.execute(
                f'ALTER TABLE `{table}` ADD CONSTRAINT `{table}_ciclo_id_fk` '
                f'FOREIGN KEY (`ciclo_id`) REFERENCES `ciclos_clinicos_cicloclinico` (`id`)'
            )
        if unique and not unique_index_exists(cursor, table, 'ciclo_id'):
            schema_editor.execute(
                f'CREATE UNIQUE INDEX `{table}_ciclo_id_uniq` ON `{table}` (`ciclo_id`)'
            )


def _drop_foreign_keys_on_column(schema_editor, table, column):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND COLUMN_NAME = %s
              AND REFERENCED_TABLE_NAME IS NOT NULL
            """,
            [table, column],
        )
        for (constraint_name,) in cursor.fetchall():
            schema_editor.execute(
                f'ALTER TABLE `{table}` DROP FOREIGN KEY `{constraint_name}`'
            )


def _restore_paciente_fk(schema_editor, table):
    with schema_editor.connection.cursor() as cursor:
        if fk_exists(cursor, table, 'paciente_id', ref_table='Login_paciente'):
            return
    schema_editor.execute(
        f'ALTER TABLE `{table}` ADD CONSTRAINT `{table}_paciente_id_fk` '
        f'FOREIGN KEY (`paciente_id`) REFERENCES `Login_paciente` (`rut`)'
    )


def migrate_questionnaire_pk_to_id(schema_editor, table):
    """
    Convierte cuestionario con PK paciente_id → id autoincrement + paciente_id FK nullable.
    Idempotente.
    """
    add_ciclo_fk(schema_editor, table, unique=True)

    with schema_editor.connection.cursor() as cursor:
        if column_exists(cursor, table, 'id'):
            _restore_paciente_fk(schema_editor, table)
            return

    _drop_foreign_keys_on_column(schema_editor, table, 'paciente_id')

    schema_editor.execute(
        f'ALTER TABLE `{table}` '
        f'DROP PRIMARY KEY, '
        f'ADD COLUMN `id` bigint NOT NULL AUTO_INCREMENT FIRST, '
        f'ADD PRIMARY KEY (`id`)'
    )
    schema_editor.execute(
        f'ALTER TABLE `{table}` MODIFY COLUMN `paciente_id` varchar(255) NULL'
    )
    _restore_paciente_fk(schema_editor, table)
