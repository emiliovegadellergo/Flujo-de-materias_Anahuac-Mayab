// Restricciones de unicidad (también crean un índice sobre la propiedad)
CREATE CONSTRAINT materia_clave IF NOT EXISTS FOR (m:Materia) REQUIRE m.clave IS UNIQUE;
CREATE CONSTRAINT alumno_matricula IF NOT EXISTS FOR (a:Alumno) REQUIRE a.matricula IS UNIQUE;
