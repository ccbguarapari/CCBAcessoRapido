import sqlite3
import unicodedata
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "database.db")
GENERATED = os.path.join(ROOT, "generated")
WHATSAPP_ICON = '''<svg viewBox="0 0 24 24" width="24" height="24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
    <g id="SVGRepo_iconCarrier"> <path d="M17.6 6.31999C16.8669 5.58141 15.9943 4.99596 15.033 4.59767C14.0716 4.19938 13.0406 3.99622 12 3.99999C10.6089 4.00135 9.24248 4.36819 8.03771 5.06377C6.83294 5.75935 5.83208 6.75926 5.13534 7.96335C4.4386 9.16745 4.07046 10.5335 4.06776 11.9246C4.06507 13.3158 4.42793 14.6832 5.12 15.89L4 20L8.2 18.9C9.35975 19.5452 10.6629 19.8891 11.99 19.9C14.0997 19.9001 16.124 19.0668 17.6222 17.5816C19.1205 16.0965 19.9715 14.0796 19.99 11.97C19.983 10.9173 19.7682 9.87634 19.3581 8.9068C18.948 7.93725 18.3505 7.05819 17.6 6.31999ZM12 18.53C10.8177 18.5308 9.65701 18.213 8.64 17.61L8.4 17.46L5.91 18.12L6.57 15.69L6.41 15.44C5.55925 14.0667 5.24174 12.429 5.51762 10.8372C5.7935 9.24545 6.64361 7.81015 7.9069 6.80322C9.1702 5.79628 10.7589 5.28765 12.3721 5.37368C13.9853 5.4597 15.511 6.13441 16.66 7.26999C17.916 8.49818 18.635 10.1735 18.66 11.93C18.6442 13.6859 17.9355 15.3645 16.6882 16.6006C15.441 17.8366 13.756 18.5301 12 18.53ZM15.61 13.59C15.41 13.49 14.44 13.01 14.26 12.95C14.08 12.89 13.94 12.85 13.81 13.05C13.6144 13.3181 13.404 13.5751 13.18 13.82C13.07 13.96 12.95 13.97 12.75 13.82C11.6097 13.3694 10.6597 12.5394 10.06 11.47C9.85 11.12 10.26 11.14 10.64 10.39C10.6681 10.3359 10.6827 10.2759 10.6827 10.215C10.6827 10.1541 10.6681 10.0941 10.64 10.04C10.64 9.93999 10.19 8.95999 10.03 8.56999C9.87 8.17999 9.71 8.23999 9.58 8.22999H9.19C9.08895 8.23154 8.9894 8.25465 8.898 8.29776C8.8066 8.34087 8.72546 8.403 8.66 8.47999C8.43562 8.69817 8.26061 8.96191 8.14676 9.25343C8.03291 9.54495 7.98287 9.85749 8 10.17C8.0627 10.9181 8.34443 11.6311 8.81 12.22C9.6622 13.4958 10.8301 14.5293 12.2 15.22C12.9185 15.6394 13.7535 15.8148 14.58 15.72C14.8552 15.6654 15.1159 15.5535 15.345 15.3915C15.5742 15.2296 15.7667 15.0212 15.91 14.78C16.0428 14.4856 16.0846 14.1583 16.03 13.84C15.94 13.74 15.81 13.69 15.61 13.59Z" fill="#404040"></path>
    </g>
</svg>'''


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
    <h1 style="margin-bottom: 0;">Casas de Oração</h1>
    <h2 style="text-align: center; margin-bottom: 2rem;">Setor Guarapari - ES</h2>
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
                ORDER BY f.id, p.nome;
                """,
                (cid, kid),
            ).fetchall()

            tel_svg = (
                '<svg class="tel-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/>'
            )
            whatsapp_fmt = '<a href="https://wa.me/{0}" target="_blank" rel="noopener">Abrir WhatsApp</a>'.format

            if pessoas:
                cards_html = ""
                for funcao, nome, descricao, tel1, tel2, comum, _ in pessoas:
                    tels = []
                    for t in (tel1, tel2):
                        if t:
                            clean = "".join(c for c in t if c.isdigit() or c == "+")
                            tels.append(
                                f'<span class="tel-row">{tel_svg}' +
                                f'</svg><a href="tel:{clean}">{t}</a>' +
                                WHATSAPP_ICON + whatsapp_fmt(t) +
                                '</span>'
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
