ALTER TABLE declaraciones_pdf
ADD COLUMN saldo_a_favor NUMERIC(18,6) NOT NULL DEFAULT 0;

ALTER TABLE declaraciones_pdf
ADD COLUMN saldo_a_pagar NUMERIC(18,6) NOT NULL DEFAULT 0;
