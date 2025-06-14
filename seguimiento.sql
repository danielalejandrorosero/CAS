-- ============================================
-- BASE DE DATOS: SEGUIMIENTO INTEGRAL DEL APRENDIZ
-- ============================================

CREATE DATABASE seguimiento_aprendiz;
USE seguimiento_aprendiz;

-- ============================================
-- TABLAS DE CONFIGURACIÓN Y USUARIOS
-- ============================================

-- Tabla de roles del sistema
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de usuarios (instructores, aprendices, administradores)
CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    documento VARCHAR(20) NOT NULL UNIQUE,
    tipo_documento ENUM('CC', 'TI', 'CE', 'PAS') NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    telefono VARCHAR(15),
    foto_perfil VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    rol_id INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP NULL,
    token_recuperacion VARCHAR(255) NULL,
    token_expiracion TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (rol_id) REFERENCES roles(id)
);

-- ============================================
-- TABLAS ACADÉMICAS
-- ============================================

-- Tabla de programas formativos
CREATE TABLE programas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nombre VARCHAR(200) NOT NULL,
    nivel ENUM('TÉCNICO', 'TECNÓLOGO', 'ESPECIALIZACIÓN') NOT NULL,
    duracion_meses INT NOT NULL,
    modalidad ENUM('PRESENCIAL', 'VIRTUAL', 'MIXTA') NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabla de fichas (grupos de aprendices)
CREATE TABLE fichas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    numero VARCHAR(20) NOT NULL UNIQUE,
    programa_id INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    jornada ENUM('MAÑANA', 'TARDE', 'NOCHE', 'MIXTA') NOT NULL,
    estado ENUM('ACTIVA', 'FINALIZADA', 'SUSPENDIDA') DEFAULT 'ACTIVA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (programa_id) REFERENCES programas(id)
);

-- Tabla de resultados de aprendizaje
CREATE TABLE resultados_aprendizaje (
    id INT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL,
    programa_id INT NOT NULL,
    nombre VARCHAR(300) NOT NULL,
    descripcion TEXT,
    horas_presenciales INT DEFAULT 0,
    horas_virtuales INT DEFAULT 0,
    trimestre INT NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (programa_id) REFERENCES programas(id),
    UNIQUE KEY unique_codigo_programa (codigo, programa_id)
);

-- ============================================
-- TABLAS DE MATRÍCULA Y ASIGNACIÓN
-- ============================================

-- Tabla de matrícula de aprendices en fichas
CREATE TABLE matriculas (
    id INT PRIMARY KEY AUTO_INCREMENT,
    aprendiz_id INT NOT NULL,
    ficha_id INT NOT NULL,
    fecha_matricula DATE NOT NULL,
    estado ENUM('ACTIVO', 'RETIRADO', 'APLAZADO', 'CANCELADO') DEFAULT 'ACTIVO',
    fecha_cambio_estado DATE NULL,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (aprendiz_id) REFERENCES usuarios(id),
    FOREIGN KEY (ficha_id) REFERENCES fichas(id),
    UNIQUE KEY unique_aprendiz_ficha (aprendiz_id, ficha_id)
);

-- Tabla de asignación de instructores a resultados de aprendizaje por ficha
CREATE TABLE asignaciones_instructor (
    id INT PRIMARY KEY AUTO_INCREMENT,
    instructor_id INT NOT NULL,
    ficha_id INT NOT NULL,
    resultado_aprendizaje_id INT NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (instructor_id) REFERENCES usuarios(id),
    FOREIGN KEY (ficha_id) REFERENCES fichas(id),
    FOREIGN KEY (resultado_aprendizaje_id) REFERENCES resultados_aprendizaje(id)
);

-- ============================================
-- TABLAS DE ASISTENCIA
-- ============================================

-- Tabla de sesiones de clase
CREATE TABLE sesiones_clase (
    id INT PRIMARY KEY AUTO_INCREMENT,
    asignacion_id INT NOT NULL,
    fecha DATE NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME,
    tema VARCHAR(300),
    observaciones TEXT,
    estado ENUM('PROGRAMADA', 'EN_CURSO', 'FINALIZADA', 'CANCELADA') DEFAULT 'PROGRAMADA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (asignacion_id) REFERENCES asignaciones_instructor(id)
);

-- Tabla de asistencia de aprendices
CREATE TABLE asistencia (
    id INT PRIMARY KEY AUTO_INCREMENT,
    sesion_id INT NOT NULL,
    aprendiz_id INT NOT NULL,
    estado ENUM('PRESENTE', 'AUSENTE', 'JUSTIFICADO', 'TARDE') NOT NULL,
    hora_llegada TIME NULL,
    observaciones TEXT,
    registrado_por INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (sesion_id) REFERENCES sesiones_clase(id),
    FOREIGN KEY (aprendiz_id) REFERENCES usuarios(id),
    FOREIGN KEY (registrado_por) REFERENCES usuarios(id),
    UNIQUE KEY unique_sesion_aprendiz (sesion_id, aprendiz_id)
);

-- ============================================
-- TABLAS DE ACTIVIDADES Y VALORACIONES
-- ============================================

-- Tabla de tipos de actividad
CREATE TABLE tipos_actividad (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de actividades
CREATE TABLE actividades (
    id INT PRIMARY KEY AUTO_INCREMENT,
    asignacion_id INT NOT NULL,
    tipo_actividad_id INT NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_creacion DATE NOT NULL,
    fecha_entrega DATE,
    hora_entrega TIME,
    criterios_valoracion TEXT,
    valor_maximo DECIMAL(5,2) DEFAULT 5.00,
    es_grupal BOOLEAN DEFAULT FALSE,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (asignacion_id) REFERENCES asignaciones_instructor(id),
    FOREIGN KEY (tipo_actividad_id) REFERENCES tipos_actividad(id)
);

-- Tabla de archivos adjuntos a actividades
CREATE TABLE archivos_actividad (
    id INT PRIMARY KEY AUTO_INCREMENT,
    actividad_id INT NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    nombre_original VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    tipo_mime VARCHAR(100),
    tamaño_bytes BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actividad_id) REFERENCES actividades(id)
);

-- Tabla de asignación de actividades (individual o por grupos)
CREATE TABLE asignaciones_actividad (
    id INT PRIMARY KEY AUTO_INCREMENT,
    actividad_id INT NOT NULL,
    aprendiz_id INT NULL, -- NULL si es grupal
    grupo_nombre VARCHAR(100) NULL, -- Para actividades grupales
    fecha_asignacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (actividad_id) REFERENCES actividades(id),
    FOREIGN KEY (aprendiz_id) REFERENCES usuarios(id)
);

-- Tabla para miembros de grupos en actividades grupales
CREATE TABLE miembros_grupo_actividad (
    id INT PRIMARY KEY AUTO_INCREMENT,
    asignacion_actividad_id INT NOT NULL,
    aprendiz_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asignacion_actividad_id) REFERENCES asignaciones_actividad(id),
    FOREIGN KEY (aprendiz_id) REFERENCES usuarios(id)
);

-- Tabla de valoraciones de actividades
CREATE TABLE valoraciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    asignacion_actividad_id INT NOT NULL,
    aprendiz_id INT NOT NULL, -- Para saber qué aprendiz específico en caso de actividad grupal
    valor_obtenido DECIMAL(5,2),
    calificacion_cualitativa ENUM('EXCELENTE', 'SOBRESALIENTE', 'ACEPTABLE', 'NO_ACEPTABLE', 'PENDIENTE') DEFAULT 'PENDIENTE',
    comentarios TEXT,
    fecha_valoracion DATE,
    valorado_por INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (asignacion_actividad_id) REFERENCES asignaciones_actividad(id),
    FOREIGN KEY (aprendiz_id) REFERENCES usuarios(id),
    FOREIGN KEY (valorado_por) REFERENCES usuarios(id),
    UNIQUE KEY unique_asignacion_aprendiz (asignacion_actividad_id, aprendiz_id)
);

-- ============================================
-- TABLAS DE CITACIONES A COMITÉ
-- ============================================

-- Tabla de tipos de citación
CREATE TABLE tipos_citacion (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de citaciones a comité
CREATE TABLE citaciones_comite (
    id INT PRIMARY KEY AUTO_INCREMENT,
    aprendiz_id INT NOT NULL,
    instructor_id INT NOT NULL,
    asignacion_id INT NOT NULL,
    tipo_citacion_id INT NOT NULL,
    motivo TEXT NOT NULL,
    fecha_citacion DATE,
    hora_citacion TIME,
    estado ENUM('PENDIENTE', 'NOTIFICADA', 'REALIZADA', 'NO_ASISTIO', 'CANCELADA') DEFAULT 'PENDIENTE',
    observaciones TEXT,
    resultado_comite TEXT,
    fecha_notificacion TIMESTAMP NULL,
    fecha_realizacion TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (aprendiz_id) REFERENCES usuarios(id),
    FOREIGN KEY (instructor_id) REFERENCES usuarios(id),
    FOREIGN KEY (asignacion_id) REFERENCES asignaciones_instructor(id),
    FOREIGN KEY (tipo_citacion_id) REFERENCES tipos_citacion(id)
);

-- Tabla de archivos adjuntos a citaciones
CREATE TABLE archivos_citacion (
    id INT PRIMARY KEY AUTO_INCREMENT,
    citacion_id INT NOT NULL,
    nombre_archivo VARCHAR(255) NOT NULL,
    nombre_original VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    tipo_mime VARCHAR(100),
    tamaño_bytes BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (citacion_id) REFERENCES citaciones_comite(id)
);

-- ============================================
-- TABLAS DE NOTIFICACIONES
-- ============================================

-- Tabla de tipos de notificación
CREATE TABLE tipos_notificacion (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de notificaciones
CREATE TABLE notificaciones (
    id INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT NOT NULL,
    tipo_notificacion_id INT NOT NULL,
    titulo VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    referencia_id INT NULL, -- ID del objeto relacionado (actividad, citación, etc.)
    referencia_tipo ENUM('ACTIVIDAD', 'VALORACION', 'CITACION', 'ASISTENCIA') NULL,
    leida BOOLEAN DEFAULT FALSE,
    fecha_lectura TIMESTAMP NULL,
    enviada BOOLEAN DEFAULT FALSE,
    fecha_envio TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (tipo_notificacion_id) REFERENCES tipos_notificacion(id)
);

-- ============================================
-- TABLAS DE CONFIGURACIÓN DEL SISTEMA
-- ============================================

-- Tabla de configuración general
CREATE TABLE configuracion_sistema (
    id INT PRIMARY KEY AUTO_INCREMENT,
    clave VARCHAR(100) NOT NULL UNIQUE,
    valor TEXT,
    descripcion TEXT,
    tipo_dato ENUM('STRING', 'INTEGER', 'BOOLEAN', 'DECIMAL', 'JSON') DEFAULT 'STRING',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- ============================================

-- Índices para usuarios
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_documento ON usuarios(documento);
CREATE INDEX idx_usuarios_rol ON usuarios(rol_id);
CREATE INDEX idx_usuarios_activo ON usuarios(activo);

-- Índices para asistencia
CREATE INDEX idx_asistencia_sesion ON asistencia(sesion_id);
CREATE INDEX idx_asistencia_aprendiz ON asistencia(aprendiz_id);
CREATE INDEX idx_asistencia_fecha ON sesiones_clase(fecha);

-- Índices para actividades
CREATE INDEX idx_actividades_asignacion ON actividades(asignacion_id);
CREATE INDEX idx_actividades_fecha_entrega ON actividades(fecha_entrega);
CREATE INDEX idx_valoraciones_aprendiz ON valoraciones(aprendiz_id);

-- Índices para notificaciones
CREATE INDEX idx_notificaciones_usuario ON notificaciones(usuario_id);
CREATE INDEX idx_notificaciones_leida ON notificaciones(leida);
CREATE INDEX idx_notificaciones_fecha ON notificaciones(created_at);

-- Índices para citaciones
CREATE INDEX idx_citaciones_aprendiz ON citaciones_comite(aprendiz_id);
CREATE INDEX idx_citaciones_estado ON citaciones_comite(estado);
CREATE INDEX idx_citaciones_fecha ON citaciones_comite(fecha_citacion);

-- ============================================
-- DATOS INICIALES
-- ============================================

-- Insertar roles básicos
INSERT INTO roles (nombre, descripcion) VALUES 
('ADMINISTRADOR', 'Administrador del sistema con acceso completo'),
('INSTRUCTOR', 'Instructor que imparte formación'),
('APRENDIZ', 'Aprendiz matriculado en programas formativos');

-- Insertar tipos de actividad básicos
INSERT INTO tipos_actividad (nombre, descripcion) VALUES 
('CONSULTA', 'Actividad de consulta e investigación'),
('TRABAJO', 'Trabajo práctico individual o grupal'),
('PROYECTO', 'Proyecto de formación'),
('EVALUACION', 'Evaluación teórica o práctica'),
('TALLER', 'Taller práctico'),
('PRESENTACION', 'Presentación oral'),
('LABORATORIO', 'Práctica de laboratorio');

-- Insertar tipos de citación básicos
INSERT INTO tipos_citacion (nombre, descripcion) VALUES 
('BAJO_RENDIMIENTO', 'Citación por bajo rendimiento académico'),
('INASISTENCIA', 'Citación por alta inasistencia'),
('COMPORTAMIENTO', 'Citación por comportamiento inadecuado'),
('SEGUIMIENTO', 'Citación de seguimiento académico'),
('OTRO', 'Otro motivo de citación');

-- Insertar tipos de notificación básicos
INSERT INTO tipos_notificacion (nombre, descripcion) VALUES 
('NUEVA_ACTIVIDAD', 'Notificación de nueva actividad creada'),
('ACTIVIDAD_VALORADA', 'Notificación de actividad valorada'),
('CITACION_COMITE', 'Notificación de citación a comité'),
('RECORDATORIO', 'Recordatorio general'),
('SISTEMA', 'Notificación del sistema');

-- Insertar configuración básica del sistema
INSERT INTO configuracion_sistema (clave, valor, descripcion, tipo_dato) VALUES 
('app_name', 'Seguimiento Integral del Aprendiz', 'Nombre de la aplicación', 'STRING'),
('version', '1.0.0', 'Versión actual del sistema', 'STRING'),
('max_file_size', '10485760', 'Tamaño máximo de archivo en bytes (10MB)', 'INTEGER'),
('session_timeout', '7200', 'Tiempo de sesión en segundos (2 horas)', 'INTEGER'),
('notification_enabled', 'true', 'Notificaciones habilitadas', 'BOOLEAN');

-- ============================================
-- COMENTARIOS FINALES
-- ============================================

/*
ESTRUCTURA DE LA BASE DE DATOS:

1. USUARIOS Y ROLES: Manejo completo de usuarios con roles diferenciados
2. ESTRUCTURA ACADÉMICA: Programas, fichas, resultados de aprendizaje
3. ASIGNACIONES: Relación instructores-fichas-resultados de aprendizaje
4. ASISTENCIA: Sesiones de clase y registro de asistencia con fotos
5. ACTIVIDADES: Creación, asignación y valoración de actividades
6. CITACIONES: Gestión completa de citaciones a comité
7. NOTIFICACIONES: Sistema de notificaciones completo
8. CONFIGURACIÓN: Parámetros del sistema

CARACTERÍSTICAS IMPORTANTES:
- Soporte para actividades individuales y grupales
- Historial completo de cambios con timestamps
- Índices optimizados para consultas frecuentes
- Integridad referencial completa
- Flexibilidad para diferentes tipos de valoración
- Sistema de archivos adjuntos
- Notificaciones automáticas configurables
*/