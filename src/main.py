import sqlite3
import unicodedata
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "database.db")
GENERATED = os.path.join(ROOT, "generated")


def slugify(text):
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.lower().replace(" ", "-")


def init_db(conn: sqlite3.Connection):
    schema = """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS casadeoracao (
      id INTEGER PRIMARY KEY,
      localidade TEXT
    );

    CREATE TABLE IF NOT EXISTS categoria (
      id INTEGER PRIMARY KEY,
      nome TEXT,
      descricao TEXT
    );

    CREATE TABLE IF NOT EXISTS funcao (
      id INTEGER PRIMARY KEY,
      id_categoria INTEGER NOT NULL,
      nome TEXT,
      descricao TEXT,
      FOREIGN KEY (id_categoria) REFERENCES categoria(id)
    );

    CREATE TABLE IF NOT EXISTS pessoa (
      id INTEGER PRIMARY KEY,
      nome TEXT,
      comum INTEGER,
      telefone1 TEXT,
      telefone2 TEXT,
      FOREIGN KEY (comum) REFERENCES casadeoracao(id)
    );

    CREATE TABLE IF NOT EXISTS pessoa_funcao_casadeoracao (
      id INTEGER PRIMARY KEY,
      id_pessoa INTEGER NOT NULL,
      id_funcao INTEGER NOT NULL,
      id_casadeoracao INTEGER NOT NULL,
      FOREIGN KEY (id_pessoa) REFERENCES pessoa(id),
      FOREIGN KEY (id_funcao) REFERENCES funcao(id),
      FOREIGN KEY (id_casadeoracao) REFERENCES casadeoracao(id)
    );
    """
    conn.executescript(schema)
    conn.commit()


def build_index(conn: sqlite3.Connection):
    cursor = conn.execute("SELECT id, localidade FROM casadeoracao ORDER BY localidade")
    casas = cursor.fetchall()

    cards_html = ""
    for cid, localidade in casas:
        slug = slugify(localidade)
        cards_html += (
            f'<a href="generated/{slug}.html" class="card">'
            f'<span class="card-title">{localidade}</span></a>\n'
        )

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, nofollow">
  <title>Casas de Oração</title>
  <link rel="stylesheet" href="generated/static/style.css">
</head>
<body>
  <main>
    <h1>Casas de Oração</h1>
    <div class="grid">
{cards_html}    </div>
  </main>
</body>
</html>"""

    with open(os.path.join(ROOT, "index.html"), "w") as f:
        f.write(html)


def build_church_pages(conn: sqlite3.Connection):
    casas = conn.execute(
        "SELECT id, localidade FROM casadeoracao ORDER BY localidade"
    ).fetchall()
    categorias = conn.execute(
        "SELECT id, nome, descricao FROM categoria"
    ).fetchall()

    for cid, localidade in casas:
        church_slug = slugify(localidade)
        cards_html = ""
        for kid, nome, descricao in categorias:
            cat_slug = slugify(nome)
            link = f"{church_slug}_{cat_slug}.html"
            descricao = descricao or ''
            has_people = conn.execute(
                """
                SELECT COUNT(*)
                FROM pessoa_funcao_casadeoracao pfc
                JOIN funcao f ON pfc.id_funcao = f.id
                WHERE pfc.id_casadeoracao = ? AND f.id_categoria = ?
                """,
                (cid, kid),
            ).fetchone()[0]
            if has_people:
                cards_html += (
                    f'\t<a href="{link}" class="card">'
                    f'  <span class="card-title">{nome}</span>'
                    f'  <span class="card-desc">{descricao}</span>'
                    '</a>\n'
                )
            else:
                cards_html += (
                    '\t<span class="card disabled" aria-disabled="true">'
                    f'  <span class="card-title">{nome}</span>'
                    f'  <span class="card-desc">{descricao}</span>'
                    '</span>\n'
                )

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, nofollow">
  <title>{localidade} — Casas de Oração</title>
  <link rel="stylesheet" href="static/style.css">
</head>
<body>
  <main>
    <a href="../index.html" class="back">← Voltar</a>
    <h1>{localidade}</h1>
    <div class="grid">
{cards_html}    </div>
  </main>
</body>
</html>"""

        with open(os.path.join(GENERATED, f"{church_slug}.html"), "w") as f:
            f.write(html)


def build_category_pages(conn: sqlite3.Connection):
    casas = conn.execute(
        "SELECT id, localidade FROM casadeoracao ORDER BY localidade"
    ).fetchall()
    categorias = conn.execute(
        "SELECT id, nome, descricao FROM categoria ORDER BY nome"
    ).fetchall()

    for cid, localidade in casas:
        church_slug = slugify(localidade)
        for kid, cat_nome, descricao in categorias:
            cat_slug = slugify(cat_nome)
            church_link = f"{church_slug}.html"

            pessoas = conn.execute(
                """
                SELECT
                    f.nome as funcao,
                    p.nome,
                    f.descricao as descricao,
                    p.telefone1, p.telefone2,
                    (SELECT localidade FROM casadeoracao WHERE id = p.comum) as comum,
                    c.localidade
                FROM pessoa p
                JOIN pessoa_funcao_casadeoracao pfc ON p.id = pfc.id_pessoa
                JOIN funcao f ON pfc.id_funcao = f.id
                JOIN casadeoracao c ON pfc.id_casadeoracao = c.id
                WHERE pfc.id_casadeoracao = ? AND f.id_categoria = ?
                ORDER BY f.nome, p.nome;
                """,
                (cid, kid),
            ).fetchall()

            tel_svg = (
                '<svg class="tel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>'
            )

            if pessoas:
                cards_html = ""
                for funcao, nome, descricao, tel1, tel2, comum, _ in pessoas:
                    tels = []
                    for t in (tel1, tel2):
                        if t:
                            clean = "".join(c for c in t if c.isdigit() or c == "+")
                            tels.append(
                                f'<span class="tel-row">{tel_svg}'
                                f'</svg><a href="tel:{clean}">{t}</a></span>'
                            )
                    tels_html = "".join(tels) if tels else '<span class="empty">Sem telefone</span>'
                    descricao_html = ''
                    if descricao:
                        descricao_html = f'<hr><span>{descricao}</span>'
                    print(nome, comum)
                    comum = comum or ' - '
                    cards_html += (
                        '   <div class="card">'
                        f'    <span class="card-title">{funcao}</span>'
                        f'    <span class="card-desc">{nome}</span>'
                        f'    <div class="card-tels">{tels_html}</div>'
                        f'    <span class="card-comum">Comum: {comum}</span>'
                        f'    {descricao_html}'
                        '  </div>'
                    )
                people_html = f'    <div class="grid">\n{cards_html}    </div>'
            else:
                people_html = '      <p class="empty">Nenhuma pessoa cadastrada nesta categoria.</p>'

            html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex, nofollow">
  <title>{cat_nome} — {localidade}</title>
  <link rel="stylesheet" href="static/style.css">
</head>
<body>
  <main>
    <a href="{church_link}" class="back">← Voltar</a>
    <h1>{localidade} — {cat_nome}</h1>
{people_html}
  </main>
</body>
</html>"""

            with open(os.path.join(GENERATED, f"{church_slug}_{cat_slug}.html"), "w") as f:
                f.write(html)


def main():
    os.makedirs(GENERATED, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        init_db(conn)
        build_index(conn)
        build_church_pages(conn)
        build_category_pages(conn)


if __name__ == "__main__":
    main()
