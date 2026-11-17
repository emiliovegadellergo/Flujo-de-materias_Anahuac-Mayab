// 0. Limpiar la base (hace el seed idempotente)
MATCH (n) DETACH DELETE n;

// 1. Materias del plan de ejemplo (Ingeniería en TI, 8 semestres)
UNWIND [
  {clave:'MAT101', nombre:'Cálculo Diferencial',              semestre:1, creditos:8,  area:'Matemáticas'},
  {clave:'MAT102', nombre:'Álgebra Lineal',                   semestre:1, creditos:8,  area:'Matemáticas'},
  {clave:'PRG101', nombre:'Fundamentos de Programación',      semestre:1, creditos:8,  area:'Programación'},
  {clave:'COM101', nombre:'Comunicación Oral y Escrita',      semestre:1, creditos:6,  area:'Formación'},
  {clave:'MAT201', nombre:'Cálculo Integral',                 semestre:2, creditos:8,  area:'Matemáticas'},
  {clave:'MAT202', nombre:'Matemáticas Discretas',            semestre:2, creditos:8,  area:'Matemáticas'},
  {clave:'PRG201', nombre:'Programación Orientada a Objetos', semestre:2, creditos:8,  area:'Programación'},
  {clave:'PRG301', nombre:'Estructuras de Datos',             semestre:3, creditos:8,  area:'Programación'},
  {clave:'BD301',  nombre:'Bases de Datos',                   semestre:3, creditos:8,  area:'Bases de Datos'},
  {clave:'MAT301', nombre:'Probabilidad y Estadística',       semestre:3, creditos:8,  area:'Matemáticas'},
  {clave:'PRG401', nombre:'Análisis de Algoritmos',           semestre:4, creditos:8,  area:'Programación'},
  {clave:'BD401',  nombre:'Bases de Datos Avanzadas',         semestre:4, creditos:8,  area:'Bases de Datos'},
  {clave:'RED401', nombre:'Redes de Computadoras',            semestre:4, creditos:8,  area:'Redes'},
  {clave:'SO501',  nombre:'Sistemas Operativos',              semestre:5, creditos:8,  area:'Programación'},
  {clave:'ING501', nombre:'Ingeniería de Software',           semestre:5, creditos:8,  area:'Gestión'},
  {clave:'IA501',  nombre:'Inteligencia Artificial',          semestre:5, creditos:8,  area:'Programación'},
  {clave:'WEB601', nombre:'Desarrollo Web',                   semestre:6, creditos:8,  area:'Programación'},
  {clave:'SEG601', nombre:'Seguridad Informática',            semestre:6, creditos:8,  area:'Redes'},
  {clave:'CD601',  nombre:'Ciencia de Datos',                 semestre:6, creditos:8,  area:'Bases de Datos'},
  {clave:'NUB701', nombre:'Cómputo en la Nube',               semestre:7, creditos:8,  area:'Redes'},
  {clave:'PRY701', nombre:'Gestión de Proyectos de TI',       semestre:7, creditos:8,  area:'Gestión'},
  {clave:'TES801', nombre:'Proyecto Terminal',                semestre:8, creditos:12, area:'Gestión'}
] AS fila
CREATE (:Materia {clave: fila.clave, nombre: fila.nombre, semestre: fila.semestre,
                  creditos: fila.creditos, area: fila.area});

// 2. Prerrequisitos: [materia, requisito]
UNWIND [
  ['MAT201','MAT101'], ['MAT202','MAT102'], ['PRG201','PRG101'],
  ['PRG301','PRG201'], ['PRG301','MAT202'], ['BD301','PRG201'], ['MAT301','MAT201'],
  ['PRG401','PRG301'], ['BD401','BD301'], ['RED401','PRG201'],
  ['SO501','PRG301'], ['ING501','BD301'], ['ING501','PRG301'], ['IA501','PRG401'], ['IA501','MAT301'],
  ['WEB601','BD401'], ['WEB601','RED401'], ['SEG601','RED401'], ['SEG601','SO501'],
  ['CD601','IA501'], ['CD601','BD401'],
  ['NUB701','WEB601'], ['NUB701','SO501'], ['PRY701','ING501'],
  ['TES801','PRY701'], ['TES801','NUB701']
] AS par
MATCH (m:Materia {clave: par[0]}), (r:Materia {clave: par[1]})
CREATE (m)-[:REQUIERE]->(r);

// 3. Alumnos: semestres aprobados y materias que cursan ahora
UNWIND [
  {matricula:'A001', nombre:'Ana López',   aprobados:3, cursa:['PRG401','BD401','RED401']},
  {matricula:'A002', nombre:'Luis Pérez',  aprobados:1, cursa:['MAT201','MAT202','PRG201']},
  {matricula:'A003', nombre:'María Chan',  aprobados:5, cursa:['WEB601','SEG601']},
  {matricula:'A004', nombre:'Diego Canul', aprobados:3, cursa:['BD401','RED401']}
] AS al
CREATE (a:Alumno {matricula: al.matricula, nombre: al.nombre, carrera: 'Ingeniería en TI'})
WITH a, al
MATCH (m:Materia) WHERE m.semestre <= al.aprobados
CREATE (a)-[:APROBO {calificacion: round(7 + rand() * 3, 1),
                     periodo: ['2024-P','2024-O','2025-P','2025-O','2026-P'][m.semestre - 1]}]->(m)
WITH DISTINCT a, al
UNWIND al.cursa AS clave
MATCH (m:Materia {clave: clave})
CREATE (a)-[:CURSA {periodo: '2026-O'}]->(m);
