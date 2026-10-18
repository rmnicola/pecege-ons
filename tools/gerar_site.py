#!/usr/bin/env python3
"""Gera o site estático do curso a partir de curso.json.

Saída em _site/: index.html com a lista de aulas e, para cada aula com
material, aulas/<slug>/index.html com a apresentação, os arquivos de
preparação e o comando do laboratório. Usa apenas a biblioteca padrão.

    python tools/gerar_site.py
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "_site"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
FONTES = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
          '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
          '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">')
COPIAR = """<script>
document.querySelectorAll('.copiar').forEach(b => b.addEventListener('click', () => {
  const texto = b.closest('.codigo').querySelector('code').innerText;
  navigator.clipboard.writeText(texto).then(() => {
    b.classList.add('copiado'); setTimeout(() => b.classList.remove('copiado'), 1600);
  });
}));
</script>"""
ICONE_COPIAR = ('<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.75" '
                'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2"/>'
                '<path d="M5 15H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v1"/></svg>')
TOKEN_SHELL = re.compile(r"""(?P<esp>\s+)|(?P<com>\#.*$)|(?P<str>"(?:[^"\\]|\\.)*"|'[^']*')"""
                         r"""|(?P<var>\$\([^)]*\)|\$\{?\w+\}?)|(?P<op>&&|\|\||2>|[|;>])|(?P<pal>[^\s"'|;>&$]+)|(?P<outro>.)""")
PREFIXOS = {"sudo"}


# Tela de senha: apenas reduz a exposição casual. O conteúdo continua
# acessível pelo repositório público e pelos links diretos dos arquivos.
PORTAO = """<div id="portao" role="dialog" aria-modal="true" aria-labelledby="portao-titulo">
<style>
#portao { position: fixed; inset: 0; z-index: 2147483647; display: grid; place-items: center;
  background: #fdfcfc; color: #646262; font: 400 15px/1.8 "IBM Plex Mono", ui-monospace, Menlo, Consolas, monospace; }
@media (prefers-color-scheme: dark) { #portao { background: #131010; color: #b7b1b1; } #portao input { background: #1b1818; color: #f1eded; } #portao h1, #portao button { color: #f1eded; } }
#portao form { width: min(22rem, calc(100vw - 3rem)); display: flex; flex-direction: column; gap: 0.75rem; }
#portao h1 { margin: 0; font: 500 1rem/1.5 inherit; color: #201d1d; }
#portao label { font-size: 13px; }
#portao input { font: inherit; padding: 0.5rem 0.75rem; border: 1px solid #d0cfcd; border-radius: 4px; background: #fff; color: #201d1d; }
#portao button { align-self: flex-start; font: inherit; padding: 0.25rem 0; border: 0; background: none; color: #201d1d; text-decoration: underline; text-underline-offset: 4px; cursor: pointer; }
#portao .erro { min-height: 1.8em; margin: 0; font-size: 13px; color: #cd0028; }
html.liberado #portao { display: none; }
</style>
<form>
<h1 id="portao-titulo">Material das aulas</h1>
<label for="portao-senha">Senha informada pelo professor</label>
<input id="portao-senha" type="password" autocomplete="current-password" required>
<button type="submit">entrar →</button>
<p class="erro" aria-live="polite"></p>
</form>
<script>
(() => {
  const ALVO = "__HASH__", CHAVE = "acesso-" + ALVO.slice(0, 8);
  const raiz = document.documentElement, portao = document.getElementById("portao");
  const ler = () => { try { return localStorage.getItem(CHAVE); } catch (e) { return null; } };
  const liberar = () => { raiz.classList.add("liberado"); document.removeEventListener("keydown", bloquear, true); };
  const bloquear = ev => { if (!portao.contains(ev.target)) ev.stopImmediatePropagation(); };
  if (ler() === ALVO) { liberar(); return; }
  document.addEventListener("keydown", bloquear, true);
  const campo = document.getElementById("portao-senha");
  setTimeout(() => campo.focus(), 0);
  portao.querySelector("form").addEventListener("submit", async ev => {
    ev.preventDefault();
    const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(campo.value.trim().toLowerCase()));
    const hash = [...new Uint8Array(bytes)].map(b => b.toString(16).padStart(2, "0")).join("");
    if (hash === ALVO) { try { localStorage.setItem(CHAVE, hash); } catch (e) {} liberar(); }
    else { portao.querySelector(".erro").textContent = "Senha incorreta."; campo.select(); }
  });
})();
</script>
</div>"""


def com_portao(html: str, curso: dict) -> str:
    if not curso.get("senha_sha256"):
        return html
    portao = PORTAO.replace("__HASH__", curso["senha_sha256"])
    return re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + portao, html, count=1)


def data_curta(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day:02d} {MESES[d.month - 1]} {d.year}"


def pagina(curso: dict, titulo: str, corpo: str, raiz: str) -> str:
    repo = escape(curso["repositorio"])
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(titulo)}</title>
<meta name="description" content="{escape(curso['descricao'])}">
{FONTES}
<link rel="stylesheet" href="{raiz}estilo.css">
</head>
<body>
<div class="moldura">
<header class="topo"><a class="marca" href="{raiz}">{escape(curso['instituicao'])}</a><nav><a href="{raiz}">aulas</a><a href="{repo}">github</a></nav></header>
<main>
{corpo}
</main>
<footer class="rodape"><p>{escape(curso['professor'])} · {escape(curso['titulo'])}</p><p>{escape(curso['aviso'])}</p></footer>
</div>
{COPIAR}
</body>
</html>
"""


def inline(texto: str) -> str:
    """Formatação mínima: `código`, **forte**, *ênfase*."""
    t = escape(texto)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)


def realcar_shell(texto: str) -> str:
    """Realce mínimo de shell: comando, prefixo (sudo), opções, textos, variáveis, operadores e comentários."""
    linhas = []
    for linha in texto.split("\n"):
        partes, espera_comando = [], True
        for m in TOKEN_SHELL.finditer(linha):
            tipo, t = m.lastgroup, m.group()
            classe = None
            if tipo == "esp":
                partes.append(t)
                continue
            if tipo == "com":
                classe = "sx-com"
            elif tipo == "str":
                classe = "sx-str"
            elif tipo == "var":
                classe = "sx-var"
            elif tipo == "op":
                classe, espera_comando = "sx-op", t not in (">", "2>")
            elif tipo == "pal":
                if espera_comando:
                    classe = "sx-kw" if t in PREFIXOS else "sx-cmd"
                    espera_comando = t in PREFIXOS
                elif t.startswith("-"):
                    classe = "sx-flag"
                elif re.fullmatch(r"\d+(\.\d+)?", t):
                    classe = "sx-num"
            partes.append(f'<span class="{classe}">{escape(t)}</span>' if classe else escape(t))
        linhas.append("".join(partes))
    return "\n".join(linhas)


def comando(texto: str, titulo: str = "Terminal") -> str:
    return (f'<figure class="codigo terminal"><figcaption class="codigo-barra"><span class="pontos" aria-hidden="true"></span>'
            f'<span class="codigo-titulo">{escape(titulo)}</span></figcaption>'
            f'<pre><code>{realcar_shell(texto)}</code></pre>'
            f'<button class="copiar" type="button" aria-label="Copiar" title="Copiar">{ICONE_COPIAR}</button></figure>')


def saida(texto: str, titulo: str = "Saída esperada") -> str:
    corpo = re.sub(r"\[OK\]", '<span class="sx-ok">[OK]</span>', escape(texto))
    return (f'<figure class="codigo saida"><figcaption class="codigo-barra"><span class="codigo-titulo">{escape(titulo)}</span>'
            f'</figcaption><pre><code>{corpo}</code></pre></figure>')


def tem_material(aula: dict) -> bool:
    return bool(aula.get("apresentacao") or aula.get("antes"))


def gerar_indice(curso: dict) -> str:
    itens = []
    for aula in curso["aulas"]:
        miolo = (f'<span class="data">{data_curta(aula["data"])}</span>'
                 f'<span><h3>{escape(aula["titulo"])}</h3><span class="sub">{escape(aula["subtitulo"])}</span></span>')
        if tem_material(aula):
            itens.append(f'<li class="aula"><a href="aulas/{aula["slug"]}/">{miolo}<span class="estado">abrir →</span></a></li>')
        else:
            itens.append(f'<li class="aula"><div>{miolo}<span class="estado">em breve</span></div></li>')
    corpo = f"""<section class="secao">
<p class="rotulo">{escape(curso['instituicao'])} · {escape(curso['professor'])}</p>
<h1>{escape(curso['titulo'])}</h1>
<p>{escape(curso['descricao'])}</p>
</section>
<section class="secao">
<h2>Aulas</h2>
<ul class="aulas">
{chr(10).join(itens)}
</ul>
</section>"""
    return pagina(curso, curso["titulo"], corpo, "")


def gerar_aula(curso: dict, aula: dict) -> str:
    partes = [f"""<section class="secao">
<p class="rotulo">{data_curta(aula['data'])} · {escape(aula['horario'])}</p>
<h1>{escape(aula['titulo'])}</h1>
<p>{escape(aula['subtitulo'])}</p>
{f"<p>{escape(aula['resumo'])}</p>" if aula.get('resumo') else ''}
</section>"""]
    if aula.get("apresentacao"):
        partes.append(f"""<section class="secao">
<a class="cartao" href="{escape(aula['apresentacao'])}"><span><h3>Apresentação</h3><p>Abre no navegador · setas do teclado para navegar</p></span><span class="seta">→</span></a>
</section>""")
    if aula.get("antes"):
        itens = "".join(
            f'<li><a href="{escape(a["link"])}">{escape(a["rotulo"])}</a><span class="rotulo">{escape(a["tipo"])}</span></li>'
            if a.get("link") else
            f'<li><a href="{escape(a["arquivo"])}" download>{escape(a["rotulo"])}</a><span class="rotulo">{escape(a["tipo"])}</span></li>'
            for a in aula["antes"])
        partes.append(f'<section class="secao"><h2>Antes da aula</h2><ul class="arquivos">{itens}</ul></section>')
    if aula.get("laboratorio"):
        repo = curso["repositorio"]
        pasta = repo.rstrip("/").rsplit("/", 1)[-1]
        partes.append(f"""<section class="secao">
<h2>Laboratório</h2>
<p>Clone o repositório na sua máquina e entre na pasta do laboratório. Os próximos passos estão na preparação do ambiente.</p>
{comando(f"git clone {repo}.git{chr(10)}cd {pasta}/playground")}
</section>""")
    return pagina(curso, f"{aula['titulo']} · {curso['instituicao']}", "\n".join(partes), "../../")


def gerar_preparacao(curso: dict, aula: dict, prep: dict) -> str:
    partes = [f"""<section class="secao">
<p class="rotulo"><a href="../">{escape(aula['titulo'])}</a> · {data_curta(aula['data'])}</p>
<h1>{escape(prep['titulo'])}</h1>
<p>{inline(prep['resumo'])}</p>
{f"<p>{inline(prep['contexto'])}</p>" if prep.get('contexto') else ''}
</section>"""]
    for n, passo in enumerate(prep["passos"], 1):
        miolo = [f'<h2><span class="num">{n:02d}</span>{escape(passo["titulo"])}</h2>']
        textos = passo.get("texto", [])
        if len(textos) > 1:
            miolo.append("<ol class=\"lista\">" + "".join(f"<li>{inline(t)}</li>" for t in textos) + "</ol>")
        miolo += [f"<p>{inline(t)}</p>" for t in textos[:1] if len(textos) == 1]
        if passo.get("comandos"):
            miolo.append(comando(passo["comandos"]))
        if passo.get("saida"):
            miolo.append(saida(passo["saida"]))
        miolo += [f"<p>{inline(t)}</p>" for t in passo.get("depois", [])]
        if passo.get("aviso"):
            miolo.append(f'<p class="aviso">{inline(passo["aviso"])}</p>')
        partes.append(f'<section class="secao passo" id="passo-{n}">{"".join(miolo)}</section>')
    if prep.get("problemas"):
        linhas = "".join(f"<tr><td>{inline(a)}</td><td>{inline(b)}</td></tr>" for a, b in prep["problemas"])
        fecho = f"<p>{inline(prep['fechamento'])}</p>" if prep.get("fechamento") else ""
        partes.append(f'<section class="secao"><h2>Se algo der errado</h2><table class="tabela"><thead><tr><th>Mensagem</th><th>O que fazer</th></tr></thead><tbody>{linhas}</tbody></table>{fecho}</section>')
    if prep.get("dia_da_aula"):
        partes.append(f'<section class="secao"><h2>No dia da aula</h2>{comando(prep["dia_da_aula"])}</section>')
    return pagina(curso, f"{prep['titulo']} · {aula['titulo']}", "\n".join(partes), "../../../")


def main() -> None:
    curso = json.loads((RAIZ / "curso.json").read_text(encoding="utf-8"))
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir()
    shutil.copy(RAIZ / "site" / "estilo.css", SAIDA / "estilo.css")
    (SAIDA / ".nojekyll").touch()
    (SAIDA / "index.html").write_text(com_portao(gerar_indice(curso), curso), encoding="utf-8")
    for aula in curso["aulas"]:
        if not tem_material(aula):
            continue
        origem = RAIZ / "aulas" / aula["slug"]
        destino = SAIDA / "aulas" / aula["slug"]
        shutil.copytree(origem, destino)
        prep_json = destino / "preparacao.json"
        if prep_json.exists():
            prep = json.loads(prep_json.read_text(encoding="utf-8"))
            (destino / "preparacao").mkdir()
            (destino / "preparacao" / "index.html").write_text(gerar_preparacao(curso, aula, prep), encoding="utf-8")
            prep_json.unlink()
        for html in destino.rglob("*.html"):
            html.write_text(com_portao(html.read_text(encoding="utf-8"), curso), encoding="utf-8")
        (destino / "index.html").write_text(com_portao(gerar_aula(curso, aula), curso), encoding="utf-8")
    print(f"site gerado em {SAIDA}")


if __name__ == "__main__":
    main()
