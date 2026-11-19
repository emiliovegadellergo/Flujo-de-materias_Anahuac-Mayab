// Restricciones de unicidad (también crean un índice sobre la propiedad)
CREATE CONSTRAINT materia_clave IF NOT EXISTS FOR (m:Materia) REQUIRE m.clave IS UNIQUE;
CREATE CONSTRAINT alumno_matricula IF NOT EXISTS FOR (a:Alumno) REQUIRE a.matricula IS UNIQUE;
CREATE CONSTRAINT alumno_usuario IF NOT EXISTS FOR (a:Alumno) REQUIRE a.usuario IS UNIQUE;
CREATE CONSTRAINT coordinador_usuario IF NOT EXISTS FOR (c:Coordinador) REQUIRE c.usuario IS UNIQUE;
