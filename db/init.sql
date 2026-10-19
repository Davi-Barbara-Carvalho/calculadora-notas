-- Executado pelo Postgres apenas na primeira vez que o volume é criado
-- (montado em /docker-entrypoint-initdb.d pelo docker-compose).
CREATE TABLE IF NOT EXISTS boletins (
    id        SERIAL PRIMARY KEY,
    aluno     TEXT               NOT NULL,
    notas     DOUBLE PRECISION[] NOT NULL,
    media     DOUBLE PRECISION   NOT NULL,
    situacao  TEXT               NOT NULL,
    criado_em TIMESTAMPTZ        NOT NULL DEFAULT now()
);
