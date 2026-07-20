"""
Módulo de base de datos con type hints y validación robusta.
Maneja usuarios, picks, historial y escalera.
"""
import sqlite3
import hashlib
import logging
from datetime import date, datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from contextlib import contextmanager

from scorpion.config import config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Excepción personalizada para errores de base de datos."""
    pass


class ValidationError(Exception):
    """Excepción para errores de validación."""
    pass


@dataclass
class Usuario:
    """Dataclass para usuario."""
    cedula: str
    nombre: str
    plan: str
    fecha_inicio: str
    dias: int
    activo: int
    es_admin: int
    pwd_hash: Optional[str]
    consultas_hoy: int
    fecha_reset: Optional[str]
    creado: str


@dataclass
class Pick:
    """Dataclass para pick."""
    id: int
    fecha: str
    liga: str
    local: str
    visitante: str
    hora: str
    mercado: str
    detalle: str
    cuota: Optional[float]
    edge: Optional[float]
    confianza: Optional[float]
    rango: str
    resultado: Optional[str]
    acierto: Optional[int]
    notas: Optional[str]
    plan_min: str
    auto: int
    creado: str


class Database:
    """Clase para manejar la base de datos SQLite."""
    
    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta opcional a la base de datos.
        """
        self.db_path = db_path or config.DB_PATH
        self._init_schema()
    
    @contextmanager
    def _get_connection(self):
        """
        Context manager para obtener conexión a la BD.
        Asegura que la conexión se cierra correctamente.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Error de SQLite: {e}")
            raise DatabaseError(f"Error de conexión a base de datos: {e}")
        finally:
            if conn:
                conn.close()
    
    def _init_schema(self) -> None:
        """Inicializa el esquema de la base de datos."""
        try:
            with self._get_connection() as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        cedula TEXT PRIMARY KEY, nombre TEXT, plan TEXT DEFAULT 'gratis',
                        fecha_inicio TEXT, dias INTEGER DEFAULT 36500, activo INTEGER DEFAULT 1,
                        es_admin INTEGER DEFAULT 0, pwd_hash TEXT,
                        consultas_hoy INTEGER DEFAULT 0, fecha_reset TEXT,
                        creado TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS picks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        fecha TEXT, liga TEXT, local TEXT, visitante TEXT, hora TEXT,
                        mercado TEXT, detalle TEXT, cuota REAL, edge REAL,
                        confianza REAL, rango TEXT, resultado TEXT, acierto INTEGER,
                        notas TEXT, plan_min TEXT DEFAULT 'gratis', auto INTEGER DEFAULT 0,
                        creado TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS historial (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, cedula TEXT, fecha TEXT,
                        liga TEXT, local TEXT, visitante TEXT,
                        p1 REAL, px REAL, p2 REAL, xg_l REAL, xg_v REAL,
                        over25 REAL, btts REAL, mercado TEXT, rango TEXT, confianza REAL,
                        creado TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS escalera (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT,
                        pasos TEXT, estado TEXT DEFAULT 'activa',
                        creado TEXT DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Crear usuario admin si no existe
                admin_hash = hashlib.sha256(config.ADMIN_PASSWORD.encode()).hexdigest()
                conn.execute("""
                    INSERT OR IGNORE INTO usuarios 
                    (cedula, nombre, plan, fecha_inicio, dias, activo, es_admin, pwd_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, ("admin", "Administrador", "admin", str(date.today()), 36500, 1, 1, admin_hash))
                
                conn.commit()
                logger.info("Base de datos inicializada correctamente")
                
        except DatabaseError:
            raise
        except Exception as e:
            logger.error(f"Error inicializando schema: {e}")
            raise DatabaseError(f"Error inicializando base de datos: {e}")
    
    # ==================== USUARIOS ====================
    
    def get_usuario(self, cedula: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por cédula.
        
        Args:
            cedula: Número de cédula/DNI del usuario.
            
        Returns:
            Dict con datos del usuario o None si no existe.
        """
        self._validate_cedula(cedula)
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM usuarios WHERE cedula = ?", (cedula,)
                ).fetchone()
                return dict(row) if row else None
        except DatabaseError:
            raise
    
    def get_todos_usuarios(self) -> List[Dict[str, Any]]:
        """Obtiene todos los usuarios ordenados por fecha de creación."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM usuarios ORDER BY creado DESC"
                ).fetchall()
                return [dict(row) for row in rows]
        except DatabaseError:
            raise
    
    def guardar_usuario(
        self,
        cedula: str,
        nombre: str,
        plan: str,
        dias: int,
        fecha_inicio: Optional[date] = None,
        activo: int = 1
    ) -> None:
        """
        Guarda o actualiza un usuario.
        
        Args:
            cedula: Cédula única del usuario.
            nombre: Nombre completo.
            plan: Plan ('gratis', 'dia', 'semana', 'mes', 'admin').
            dias: Duración del plan en días.
            fecha_inicio: Fecha de inicio (default: hoy).
            activo: 1=activo, 0=inactivo.
        """
        self._validate_cedula(cedula)
        self._validate_plan(plan)
        
        if dias <= 0 or dias > 36500:
            raise ValidationError("Días debe estar entre 1 y 36500")
        
        fecha_str = str(fecha_inicio or date.today())
        
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO usuarios
                    (cedula, nombre, plan, fecha_inicio, dias, activo, es_admin, pwd_hash, creado)
                    VALUES (
                        ?, ?, ?, ?, ?, ?,
                        COALESCE((SELECT es_admin FROM usuarios WHERE cedula = ?), 0),
                        COALESCE((SELECT pwd_hash FROM usuarios WHERE cedula = ?), NULL),
                        COALESCE((SELECT creado FROM usuarios WHERE cedula = ?), CURRENT_TIMESTAMP)
                    )
                """, (cedula, nombre, plan, fecha_str, dias, activo, cedula, cedula, cedula))
                conn.commit()
                logger.info(f"Usuario {cedula} guardado exitosamente")
        except DatabaseError:
            raise
    
    def verificar_acceso(self, cedula: str) -> Tuple[bool, str, int]:
        """
        Verifica si un usuario tiene acceso válido.
        
        Returns:
            Tuple (tiene_acceso, plan, dias_restantes)
        """
        usuario = self.get_usuario(cedula)
        
        if not usuario:
            return (False, "no_existe", 0)
        
        if not usuario["activo"]:
            return (False, "inactivo", 0)
        
        if usuario["es_admin"]:
            return (True, "admin", 99999)
        
        if usuario["plan"] == "gratis":
            return (True, "gratis", 99999)
        
        # Calcular días restantes
        try:
            inicio = date.fromisoformat(usuario["fecha_inicio"])
            vence = inicio + __import__("datetime").timedelta(days=usuario["dias"])
            dias_restantes = (vence - date.today()).days
            
            if date.today() > vence:
                return (False, "vencido", 0)
            
            return (True, usuario["plan"], dias_restantes)
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculando vencimiento: {e}")
            return (False, "error", 0)
    
    def login_admin(self, password: str) -> bool:
        """
        Verifica credenciales de administrador.
        
        Args:
            password: Contraseña a verificar.
            
        Returns:
            True si las credenciales son válidas.
        """
        if not password:
            return False
        
        usuario = self.get_usuario("admin")
        if not usuario or not usuario.get("pwd_hash"):
            return False
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == usuario["pwd_hash"]
    
    def incrementar_consultas(self, cedula: str) -> int:
        """
        Incrementa el contador de consultas diarias.
        
        Returns:
            Número actual de consultas.
        """
        self._validate_cedula(cedula)
        hoy = str(date.today())
        
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT consultas_hoy, fecha_reset FROM usuarios WHERE cedula = ?",
                    (cedula,)
                ).fetchone()
                
                if not row:
                    raise DatabaseError(f"Usuario {cedula} no encontrado")
                
                consultas_hoy = row["consultas_hoy"] or 0
                fecha_reset = row["fecha_reset"]
                
                if fecha_reset != hoy:
                    # Resetear contador
                    conn.execute(
                        "UPDATE usuarios SET consultas_hoy = 1, fecha_reset = ? WHERE cedula = ?",
                        (hoy, cedula)
                    )
                    conn.commit()
                    return 1
                else:
                    nuevas = consultas_hoy + 1
                    conn.execute(
                        "UPDATE usuarios SET consultas_hoy = ? WHERE cedula = ?",
                        (nuevas, cedula)
                    )
                    conn.commit()
                    return nuevas
                    
        except DatabaseError:
            raise
    
    def get_estadisticas(self) -> Dict[str, int]:
        """Obtiene estadísticas generales del sistema."""
        try:
            with self._get_connection() as conn:
                total = conn.execute(
                    "SELECT COUNT(*) FROM usuarios WHERE es_admin = 0"
                ).fetchone()[0]
                picks = conn.execute("SELECT COUNT(*) FROM picks").fetchone()[0]
                
                # Contar activos
                activos = sum(
                    1 for u in self.get_todos_usuarios()
                    if u.get("es_admin") == 0 and self.verificar_acceso(u["cedula"])[0]
                )
                
                return {"usuarios": total, "activos": activos, "picks": picks}
        except DatabaseError:
            raise
    
    # ==================== PICKS ====================
    
    def guardar_pick(
        self,
        fecha: str,
        liga: str,
        local: str,
        visitante: str,
        hora: str,
        mercado: str,
        detalle: str,
        cuota: Optional[float],
        edge: Optional[float],
        confianza: float,
        rango: str,
        notas: str = "",
        plan_min: str = "gratis",
        auto: int = 0
    ) -> None:
        """Guarda un pick publicado."""
        self._validate_rango(rango)
        
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO picks 
                    (fecha, liga, local, visitante, hora, mercado, detalle, 
                     cuota, edge, confianza, rango, notas, plan_min, auto)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fecha, liga, local, visitante, hora, mercado, detalle,
                    cuota, edge, confianza, rango, notas, plan_min, auto
                ))
                conn.commit()
                logger.info(f"Pick guardado: {local} vs {visitante} - {mercado}")
        except DatabaseError:
            raise
    
    def get_picks(
        self,
        fecha: Optional[str] = None,
        plan: str = "gratis"
    ) -> List[Dict[str, Any]]:
        """
        Obtiene picks filtrados por fecha y plan.
        
        Args:
            fecha: Fecha específica (None = todos).
            plan: Plan mínimo requerido ('gratis', 'dia', 'semana', 'mes', 'admin').
        """
        try:
            with self._get_connection() as conn:
                if fecha:
                    if plan == "admin":
                        query = "SELECT * FROM picks WHERE fecha = ? ORDER BY confianza DESC"
                        rows = conn.execute(query, (fecha,)).fetchall()
                    else:
                        query = """
                            SELECT * FROM picks 
                            WHERE fecha = ? AND plan_min IN ('gratis', ?)
                            ORDER BY confianza DESC
                        """
                        rows = conn.execute(query, (fecha, plan)).fetchall()
                else:
                    if plan == "admin":
                        rows = conn.execute(
                            "SELECT * FROM picks ORDER BY fecha DESC, confianza DESC"
                        ).fetchall()
                    else:
                        query = """
                            SELECT * FROM picks 
                            WHERE plan_min IN ('gratis', ?)
                            ORDER BY fecha DESC, confianza DESC
                        """
                        rows = conn.execute(query, (plan,)).fetchall()
                
                return [dict(row) for row in rows]
        except DatabaseError:
            raise
    
    def get_picks_top(
        self,
        fecha: str,
        limite: int = 3,
        umbral_confianza: float = 50.0
    ) -> List[Dict[str, Any]]:
        """Obtiene los mejores picks de una fecha."""
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT * FROM picks 
                    WHERE fecha = ? AND confianza >= ?
                    ORDER BY confianza DESC, edge DESC
                    LIMIT ?
                """, (fecha, umbral_confianza, limite)).fetchall()
                return [dict(row) for row in rows]
        except DatabaseError:
            raise
    
    # ==================== HISTORIAL ====================
    
    def guardar_historial(
        self,
        cedula: str,
        partido: Dict[str, Any],
        calculo: Dict[str, Any]
    ) -> None:
        """Guarda un análisis en el historial."""
        self._validate_cedula(cedula)
        
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO historial
                    (cedula, fecha, liga, local, visitante, p1, px, p2,
                     xg_l, xg_v, over25, btts, mercado, rango, confianza)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cedula,
                    partido.get("dia", str(date.today())),
                    partido.get("liga", ""),
                    partido.get("local", ""),
                    partido.get("visitante", ""),
                    calculo.get("p1"),
                    calculo.get("px"),
                    calculo.get("p2"),
                    calculo.get("xl"),
                    calculo.get("xv"),
                    calculo.get("over25"),
                    calculo.get("btts_si"),
                    calculo.get("mk2", ""),
                    calculo.get("rango", ""),
                    calculo.get("confianza", 0)
                ))
                conn.commit()
        except DatabaseError:
            raise
    
    def get_historial(self, cedula: str, limite: int = 30) -> List[Dict[str, Any]]:
        """Obtiene historial de análisis de un usuario."""
        self._validate_cedula(cedula)
        
        try:
            with self._get_connection() as conn:
                rows = conn.execute("""
                    SELECT * FROM historial 
                    WHERE cedula = ?
                    ORDER BY creado DESC
                    LIMIT ?
                """, (cedula, limite)).fetchall()
                return [dict(row) for row in rows]
        except DatabaseError:
            raise
    
    # ==================== VALIDACIONES ====================
    
    @staticmethod
    def _validate_cedula(cedula: str) -> None:
        """Valida formato de cédula."""
        if not cedula or not isinstance(cedula, str):
            raise ValidationError("Cédula debe ser una cadena no vacía")
        if len(cedula.strip()) < 3:
            raise ValidationError("Cédula debe tener al menos 3 caracteres")
    
    @staticmethod
    def _validate_plan(plan: str) -> None:
        """Valida que el plan sea válido."""
        planes_validos = {"gratis", "dia", "semana", "mes", "admin"}
        if plan not in planes_validos:
            raise ValidationError(f"Plan debe ser uno de: {planes_validos}")
    
    @staticmethod
    def _validate_rango(rango: str) -> None:
        """Valida que el rango sea válido."""
        rangos_validos = {"A+", "B", "C", "D"}
        if rango not in rangos_validos:
            raise ValidationError(f"Rango debe ser uno de: {rangos_validos}")


# Instancia global de base de datos
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """Obtiene la instancia global de la base de datos."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
