-- Agregar campo cantidad_a_cargo a la tabla declaraciones_pdf
-- Este campo se utiliza para almacenar la cantidad a cargo de la declaración SAT

ALTER TABLE declaraciones_pdf
ADD COLUMN cantidad_a_cargo NUMERIC(18,6) NOT NULL DEFAULT 0;
