import logging
from datetime import timedelta

import odoo.modules.module
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class MigalAgenteRateLimit(models.Model):
    """Contador persistente para limitar solicitudes a endpoints públicos.

    Compatible con multi-worker: usa PostgreSQL como almacén compartido y
    actualización atómica por clave/ventana.
    """

    _name = "migal.agente.rate.limit"
    _description = "Rate limit de endpoints públicos del agente"
    _rec_name = "key"

    key = fields.Char(required=True, index=True)
    window_start = fields.Datetime(required=True)
    count = fields.Integer(required=True, default=0)

    _key_uniq = models.Constraint("unique(key)", "La clave de rate limit debe ser única.")

    _index_ensured = False

    @api.model
    def _ensure_key_index(self):
        # Compatibilidad: tablas creadas antes del Constraint Odoo 19.
        if self.__class__._index_ensured:
            return
        self.env.cr.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS migal_agente_rate_limit_key_uniq
            ON migal_agente_rate_limit (key)
            """
        )
        self.__class__._index_ensured = True

    @api.model
    def check_and_hit(self, key, limit, window_seconds):
        """Registra un hit y devuelve (allowed, retry_after_seconds).

        Ventana fija por clave. Al expirar la ventana se reinicia el contador.
        Usa cursor independiente para persistir aunque la request termine en 404/rollback.
        En modo test (TestCursor) usa un cursor real para evitar rollback de savepoints.
        """
        if not key:
            return True, 0
        now = fields.Datetime.now()
        cutoff = now - timedelta(seconds=window_seconds)
        uid = self.env.uid or 1
        sql = """
            INSERT INTO migal_agente_rate_limit
                (key, window_start, count, create_uid, create_date, write_uid, write_date)
            VALUES (%s, %s, 1, %s, %s, %s, %s)
            ON CONFLICT (key) DO UPDATE SET
                count = CASE
                    WHEN migal_agente_rate_limit.window_start <= %s THEN 1
                    ELSE migal_agente_rate_limit.count + 1
                END,
                window_start = CASE
                    WHEN migal_agente_rate_limit.window_start <= %s THEN %s
                    ELSE migal_agente_rate_limit.window_start
                END,
                write_uid = EXCLUDED.write_uid,
                write_date = EXCLUDED.write_date
            RETURNING count, window_start
        """
        params = (key, now, uid, now, uid, now, cutoff, cutoff, now)
        # Cursor independiente para persistir conteo aunque la request termine en 404/rollback.
        # Producción: registry.cursor() devuelve un Cursor real independiente; en Odoo 19 __exit__ hace commit+close.
        # Test mode: registry.cursor() está parcheado por el arnés de tests para devolver TestCursor (savepoint);
        # un commit en TestCursor no persiste ante rollback 404. Se usa registry._db.cursor() (Cursor real del pool,
        # no parcheado) para persistir el contador en una transacción DB independiente.
        # Detección: odoo.modules.module.current_test es establecido por el runner de tests de Odoo 19.
        in_test_mode = bool(getattr(odoo.modules.module, "current_test", False))
        from psycopg2 import errors as pg_errors  # noqa: PLC0415

        last_exc = None
        for attempt in range(3):
            try:
                if in_test_mode:
                    with self.env.registry._db.cursor() as cr:
                        cr.execute(
                            "CREATE UNIQUE INDEX IF NOT EXISTS migal_agente_rate_limit_key_uniq ON migal_agente_rate_limit (key)"
                        )
                        cr.execute(sql, params)
                        count, window_start = cr.fetchone()
                        cr.commit()
                else:
                    with self.env.registry.cursor() as cr:
                        cr.execute(
                            "CREATE UNIQUE INDEX IF NOT EXISTS migal_agente_rate_limit_key_uniq ON migal_agente_rate_limit (key)"
                        )
                        cr.execute(sql, params)
                        count, window_start = cr.fetchone()
                        # Commit explícito en cursor independiente para robustez (además del commit de __exit__).
                        cr.commit()
                last_exc = None
                break
            except (pg_errors.DeadlockDetected, pg_errors.SerializationFailure) as exc:
                last_exc = exc
                if attempt == 2:
                    raise
        if last_exc is not None:
            raise last_exc
        if count > limit:
            elapsed = (now - window_start).total_seconds()
            retry_after = max(1, int(window_seconds - elapsed))
            _logger.warning("migal_agente rate limit exceeded: key=%s count=%s limit=%s", key, count, limit)
            return False, retry_after
        return True, 0

    @api.autovacuum
    def _gc_old_limits(self):
        """Limpia contadores antiguos para evitar crecimiento indefinido."""
        cutoff = fields.Datetime.now() - timedelta(days=1)
        self.sudo().search([("window_start", "<", cutoff)]).unlink()
