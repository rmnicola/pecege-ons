#!/usr/bin/env node
/* Gera, verifica e exporta um deck Pecege–ONS. Adaptado do sistema Inteli.

   node design-system/tools/deck.mjs <deck.html> [--slide N] [--nome arquivo] [--pdf [--passos]]

   A partir do HTML-fonte (que aponta para ../design-system/...), produz na pasta do deck:
     dist/index.html   arquivo único: CSS, JS, fontes e imagens embutidos (pronto para GitHub Pages);
                       com --nome X, sai como dist/X.html, para distribuir o arquivo avulso
     dist/<pasta>.pdf  apenas com --pdf: uma página por slide e por conteúdo substituído, 16:9;
                       com --passos, uma página por estado de cada slide, todas com o número do slide
     qa/slide-NN.png   imagem de cada slide, para revisão visual
     qa/relatorio.json resultado das verificações
   Sai com código 1 se alguma verificação de erro falhar. */
import { spawn, execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { pathToFileURL } from "node:url";

/* Pontos de partida do design system. Ao promover um slide sob medida a template, acrescente-o aqui. */
const LAYOUTS = ["capa", "legal", "agenda", "capitulo-slide", "ideia", "painel", "fluxo-slide", "codigo-slide", "imagem", "citacao", "atividade", "encerramento", "referencias"];

const args = process.argv.slice(2);
const valor = (op) => (args.includes(op) ? args[args.indexOf(op) + 1] : null);
const src = path.resolve(args.find((a, i) => !a.startsWith("--") && !["--slide", "--nome"].includes(args[i - 1])) ?? "");
const soSlide = valor("--slide") ? parseInt(valor("--slide"), 10) : null;
const nome = (valor("--nome") ?? "index").replace(/\.html$/, "");
if (!fs.existsSync(src) || !fs.statSync(src).isFile() || (soSlide !== null && (!Number.isInteger(soSlide) || soSlide < 1)) || !/^[a-zA-Z0-9_-]+$/.test(nome)) { console.error("uso: node deck.mjs <deck.html> [--slide N positivo] [--nome nome-sem-espacos]"); process.exit(2); }

const pastaDeck = path.dirname(src);
const dist = path.join(pastaDeck, "dist");
const qa = path.join(pastaDeck, "qa");
fs.mkdirSync(dist, { recursive: true });
fs.mkdirSync(qa, { recursive: true });

/* ---------- 1. Embutir tudo num arquivo só ---------- */

const MIME = { ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".svg": "image/svg+xml",
  ".gif": "image/gif", ".webp": "image/webp", ".woff2": "font/woff2", ".woff": "font/woff" };
const externo = (u) => /^(data:|https?:|#|mailto:)/.test(u);
const dataUri = (arq) => `data:${MIME[path.extname(arq).toLowerCase()] ?? "application/octet-stream"};base64,${fs.readFileSync(arq).toString("base64")}`;

function embutirCss(arq) {
  const dir = path.dirname(arq);
  let css = fs.readFileSync(arq, "utf8");
  css = css.replace(/@import\s+url\(["']?([^"')]+)["']?\);?/g, (_, u) => embutirCss(path.resolve(dir, u)));
  return css.replace(/url\(["']?([^"')]+)["']?\)/g, (m, u) => (externo(u) ? m : `url("${dataUri(path.resolve(dir, u))}")`));
}

let html = fs.readFileSync(src, "utf8");
html = html.replace(/(<style[^>]*>)([\s\S]*?)(<\/style>)/g, (m, a, css, b) =>
  a + css.replace(/url\(["']?([^"')]+)["']?\)/g, (mm, u) => (externo(u) ? mm : `url("${dataUri(path.resolve(pastaDeck, u))}")`)) + b);
html = html.replace(/<link\s+rel="stylesheet"\s+href="([^"]+)"\s*\/?>/g, (m, u) =>
  externo(u) ? m : `<style>\n${embutirCss(path.resolve(pastaDeck, u))}\n</style>`);
html = html.replace(/<script\s+src="([^"]+)"\s*><\/script>/g, (m, u) =>
  externo(u) ? m : `<script>\n${fs.readFileSync(path.resolve(pastaDeck, u), "utf8")}\n</script>`);
html = html.replace(/(<img\b[^>]*\bsrc=")([^"]+)(")/g, (m, a, u, b) => (externo(u) ? m : a + dataUri(path.resolve(pastaDeck, u)) + b));
/* O rodapé é inserido pelo runtime; embuta também sua marca para o HTML ser offline. */
const simbolo = dataUri(path.resolve(path.dirname(new URL(import.meta.url).pathname), "../assets/img/simbolo-pecege.svg"));
html = html.replace('marca.src = ds + "/assets/img/simbolo-pecege.svg";', `marca.src = ${JSON.stringify(simbolo)};`);
const saida = path.join(dist, `${nome}.html`);
fs.writeFileSync(saida, html);

/* ---------- 2. Abrir no Chromium e verificar ---------- */

const porta = 9400 + Math.floor(Math.random() * 400);
const perfil = fs.mkdtempSync(path.join(process.env.TMPDIR ?? "/tmp/opencode", "deck-"));
const chrome = spawn("chromium", ["--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  `--remote-debugging-port=${porta}`, `--user-data-dir=${perfil}`, "--window-size=1600,900", "about:blank"]);
let alvo;
for (let t = 0; t < 50 && !alvo; t++) {
  await new Promise((r) => setTimeout(r, 200));
  try { alvo = (await (await fetch(`http://127.0.0.1:${porta}/json`)).json()).find((x) => x.type === "page"); } catch {}
}
if (!alvo) { chrome.kill(); fs.rmSync(perfil, {recursive:true, force:true}); throw new Error("Chromium não iniciou; confirme que está instalado e executável."); }
const ws = new WebSocket(alvo.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pend = {};
ws.onmessage = (e) => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m); delete pend[m.id]; } };
const cdp = (method, params = {}) => new Promise((r) => { const i = ++id; pend[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });
const avaliar = async (expr) => {
  const r = await cdp("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
  return r.result?.result?.value;
};

await cdp("Emulation.setDeviceMetricsOverride", { width: 1600, height: 900, deviceScaleFactor: 1, mobile: false });
await cdp("Page.enable");
/* Exceções de JavaScript da página viram erro do build: um slide montado por script pode ficar vazio sem nenhum outro sintoma. */
const excecoes = [];
ws.addEventListener("message", (e) => { const m = JSON.parse(e.data);
  if (m.method === "Runtime.exceptionThrown") excecoes.push((m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text || "").split("\n").slice(0, 2).join(" ")); });
await cdp("Runtime.enable");
/* No PDF, cada página escolhe o seu estado: o beforeprint de deck.js levaria todos ao estado final. */
if (args.includes("--pdf")) await cdp("Page.addScriptToEvaluateOnNewDocument", { source:
  `{ const add = window.addEventListener.bind(window); window.addEventListener = (t, ...r) => t === "beforeprint" || t === "afterprint" ? undefined : add(t, ...r); }` });
await cdp("Page.navigate", { url: pathToFileURL(saida).href });
await new Promise((r) => setTimeout(r, 1500));
await avaliar("document.fonts.ready.then(() => true)");
/* Sem transições durante as capturas */
await avaliar(`(() => { const st = document.createElement("style"); st.textContent = "*, *::before, *::after { transition: none !important; }"; document.head.append(st); return true; })()`);
/* Imagens antigas saem, para não sobrar estado de passo que não existe mais */
for (const f of fs.readdirSync(qa)) if (/^slide-\d+(-passo-\d+)?\.png$/.test(f) && !soSlide) fs.rmSync(path.join(qa, f));

/* Roda dentro da página, com o slide i visível. */
const VERIFICAR = (i) => `(() => {
  const s = window.deck.slides[${i}];
  const R = s.getBoundingClientRect();
  const erros = [], avisos = [];
  const dentroDeNotas = (el) => el.closest(".notas");
  const sangra = (el) => el.closest(".bloco-cinza, .esfera, .sangra");
  const emObjeto = (el) => el.closest(".objeto *");
  const visivel = (el) => { const c = getComputedStyle(el); return c.display !== "none" && c.visibility !== "hidden"; };
  const nome = (el) => el.tagName.toLowerCase() + (el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\\s+/).join(".") : "");

  /* Fora da área do slide */
  for (const el of s.querySelectorAll("*")) {
    if (dentroDeNotas(el) || !visivel(el) || sangra(el) || emObjeto(el)) continue;
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if (r.left < R.left - 1 || r.top < R.top - 1 || r.right > R.right + 1 || r.bottom > R.bottom + 1)
      erros.push("sai da área do slide: " + nome(el));
  }
  /* Caixa que passa da borda ANTES do transform: no PDF, o navegador quebra a página nesse ponto
     (ex.: top: 50% + translateY(-50%)). offsetTop/offsetHeight ignoram transforms. */
  for (const el of s.querySelectorAll("*")) {
    if (!(el instanceof HTMLElement) || dentroDeNotas(el) || !visivel(el) || el.closest(".sangra, .bloco-cinza, .esfera")) continue;
    let topo = 0, e = el;
    while (e && e !== s) { topo += e.offsetTop; e = e.offsetParent; }
    if (e !== s) continue;
    if (topo + el.offsetHeight > s.offsetHeight + 1 || topo < -1)
      erros.push("caixa passa da borda antes do transform (quebra o PDF): " + nome(el));
  }
  /* Conteúdo maior que a caixa */
  for (const el of s.querySelectorAll(".conteudo, .conteudo *, .lado, .rodape")) {
    if (dentroDeNotas(el) || !visivel(el)) continue;
    if (el.scrollHeight > el.clientHeight + 2 && el.clientHeight > 0 && getComputedStyle(el).overflow !== "visible")
      erros.push("texto vaza (altura): " + nome(el));
    if (el.matches(".conteudo")) {
      const cr = el.getBoundingClientRect();
      for (const f of el.children) { const fr = f.getBoundingClientRect();
        if (fr.bottom > cr.bottom + 2 || fr.top < cr.top - 2 || fr.right > cr.right + 2) erros.push("conteúdo maior que a área útil: " + nome(f)); }
    }
  }
  /* Texto: tamanho mínimo, fonte carregada, sobreposição, contraste */
  const linhas = [];
  const andar = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
  const lum = (c) => { const v = c.match(/[\\d.]+/g).slice(0, 3).map(Number).map((x) => { x /= 255; return x <= .03928 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4; });
    return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]; };
  const fundo = (el) => { for (let e = el; e; e = e.parentElement) { const b = getComputedStyle(e).backgroundColor;
    if (b && !/rgba\\(.*,\\s*0\\)$/.test(b) && b !== "transparent") return b; } return "rgb(255,255,255)"; };
  for (let n; (n = andar.nextNode());) {
    const el = n.parentElement;
    if (!n.textContent.trim() || dentroDeNotas(el) || !visivel(el) || el.closest(".objeto, .rodape-institucional")) continue;
    const c = getComputedStyle(el);
    const tam = parseFloat(c.fontSize);
    if (tam < 28) erros.push("fonte pequena demais (" + tam + "px): \\"" + n.textContent.trim().slice(0, 40) + "\\"");
    const fam = c.fontFamily.split(",")[0].replace(/["']/g, "").trim();
    if (!document.fonts.check(c.fontWeight + " " + tam + "px \\"" + fam + "\\"")) erros.push("fonte não carregada: " + fam);
    const a = lum(c.color), b = lum(fundo(el)); const razao = (Math.max(a, b) + .05) / (Math.min(a, b) + .05);
    if (razao < (tam >= 24 ? 3 : 4.5)) erros.push("contraste baixo (" + razao.toFixed(1) + "): \\"" + n.textContent.trim().slice(0, 40) + "\\"");
    const rg = document.createRange(); rg.selectNodeContents(n);
    for (const r of rg.getClientRects()) {
      linhas.push({ el, r });
      /* o texto pode transbordar a própria caixa sem que a caixa saia do slide */
      if (!el.closest(".sangra") && (r.left < R.left - 1 || r.right > R.right + 1 || r.top < R.top - 1 || r.bottom > R.bottom + 1))
        erros.push("texto sai da área do slide: \\"" + n.textContent.trim().slice(0, 40) + "\\"");
      else if (!el.closest(".sangra, .objeto") && r.width > 0 && (r.left < R.left + 40 || r.right > R.right - 40))
        avisos.push("texto a menos de 40px da borda: \\"" + n.textContent.trim().slice(0, 40) + "\\"");
    }
  }
  for (let x = 0; x < linhas.length; x++) for (let y = x + 1; y < linhas.length; y++) {
    const p = linhas[x], q = linhas[y];
    if (p.el === q.el || p.el.contains(q.el) || q.el.contains(p.el)) continue;
    /* compara só a faixa central da linha: a caixa do texto inclui folgas acima e abaixo das letras */
    const enc = (r) => ({ top: r.top + r.height * .2, bottom: r.bottom - r.height * .2 });
    const pv = enc(p.r), qv = enc(q.r);
    const ix = Math.min(p.r.right, q.r.right) - Math.max(p.r.left, q.r.left), iy = Math.min(pv.bottom, qv.bottom) - Math.max(pv.top, qv.top);
    if (ix > 2 && iy > 2) erros.push("textos sobrepostos: " + nome(p.el) + " × " + nome(q.el));
  }
  /* Imagens */
  for (const img of s.querySelectorAll("img")) if (!img.complete || !img.naturalWidth) erros.push("imagem não carregou: " + (img.alt || "sem alt"));
  /* Regra dos 30 segundos */
  /* Junta os trechos de texto com espaço: elementos vizinhos não podem colar palavras. */
  const trechos = []; const tw = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
  for (let n; (n = tw.nextNode());) if (!n.parentElement.closest(".notas, .objeto, .rodape-institucional") && visivel(n.parentElement)) trechos.push(n.textContent);
  const palavras = (trechos.join(" ").match(/[\\p{L}\\p{N}][\\p{L}\\p{N}'’-]*/gu) || []).length;
  const max = parseInt(s.dataset.maxPalavras || "30", 10);
  if (palavras > max) avisos.push("regra dos 30 segundos: " + palavras + " palavras (máximo " + max + ")");
  const blocos = s.querySelectorAll(".conteudo > *").length;
  if (blocos > 4) avisos.push("muitos elementos na tela: " + blocos + " blocos (máximo 4)");
  const LAYOUTS = ${JSON.stringify(LAYOUTS)};
  const tipo = LAYOUTS.find((l) => s.classList.contains(l)) || ("sob medida: " + (s.dataset.modelo || "sem nome"));
  if (!LAYOUTS.some((l) => s.classList.contains(l)) && !s.dataset.modelo) avisos.push("slide sob medida sem data-modelo (dê um nome curto)");
  return { slide: ${i} + 1, tipo, palavras, fundo: getComputedStyle(s).backgroundColor, imagemFundo: getComputedStyle(s).backgroundImage !== 'none', erros: [...new Set(erros)], avisos: [...new Set(avisos)] };
})()`;

const total = await avaliar("window.deck.total");
if (soSlide && soSlide > total) { ws.close(); chrome.kill(); fs.rmSync(perfil, {recursive:true, force:true}); throw new Error(`Slide ${soSlide} não existe (total: ${total}).`); }
const relatorio = [];
for (let i = 0; i < total; i++) {
  if (soSlide && i + 1 !== soSlide) continue;
  const quadro = () => "new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)))";
  const nn = String(i + 1).padStart(2, "0");
  /* Verificação e imagem principal com todos os passos visíveis */
  await avaliar(`window.deck.ir(${i}, false, Infinity); ${quadro()}`);
  relatorio.push(await avaliar(VERIFICAR(i)));
  const shot = await cdp("Page.captureScreenshot", { format: "png" });
  fs.writeFileSync(path.join(qa, `slide-${nn}.png`), Buffer.from(shot.result.data, "base64"));
  /* Uma imagem por estado intermediário, para revisar a sequência dos passos */
  const nPassos = await avaliar(`window.deck.passos(${i})`);
  for (let k = 0; k < nPassos; k++) {
    await avaliar(`window.deck.ir(${i}, false, ${k}); ${quadro()}`);
    const estado = await avaliar(VERIFICAR(i));
    const principal = relatorio.at(-1);
    principal.erros.push(...estado.erros.map(e => `passo ${k}: ${e}`));
    principal.avisos.push(...estado.avisos.map(e => `passo ${k}: ${e}`));
    const p = await cdp("Page.captureScreenshot", { format: "png" });
    fs.writeFileSync(path.join(qa, `slide-${nn}-passo-${k}.png`), Buffer.from(p.result.data, "base64"));
  }
}

/* ---------- Ajuda guiada: todo balão de todo passo dentro do slide ---------- */
for (let i = 0; i < total; i++) {
  if (soSlide && i + 1 !== soSlide) continue;
  const problemas = await avaliar(`(async () => {
    window.deck.ir(${i}, false, Infinity);
    const s = window.deck.slides[${i}];
    const b = s.querySelector(".ajuda-botao");
    if (!b) return [];
    const quadro = () => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
    b.click(); await quadro();
    const R = s.getBoundingClientRect(), esc = R.width / 1600, out = [];
    for (let k = 0; k < 40; k++) {
      const balao = s.querySelector(".ajuda-balao");
      if (!balao) break;
      const r = balao.getBoundingClientRect();
      if (r.left < R.left - 1 || r.top < R.top - 1 || r.right > R.right + 1 || r.bottom > R.bottom + 1)
        out.push("balão de ajuda sai do slide (passo " + (k + 1) + "): " + balao.querySelector("p").textContent.slice(0, 50));
      const prox = balao.querySelector("[data-a=prox]");
      if (!prox || prox.textContent === "fechar") { prox && prox.click(); break; }
      prox.click(); await quadro();
    }
    return out;
  })()`);
  const r = relatorio.find((x) => x.slide === i + 1);
  if (r) r.erros.push(...problemas);
}

/* ---------- 3. PDF ----------
   Uma página por slide no estado final e, quando um passo substitui conteúdo (data-sai),
   uma página no último estado antes de cada saída: nada do que aparece na aula fica de fora. */
if (!soSlide && args.includes("--pdf")) {
  await avaliar(`(() => { const st = document.createElement("style");
    st.textContent = "@media print { .slide.fora-pdf { display: none !important; } }"; document.head.append(st); return true; })()`);
  await cdp("Emulation.setEmulatedMedia", { media: "print" });
  const estados = await avaliar(`window.deck.slides.map((s) => {
    const itens = Array.from(s.querySelectorAll(".passo")).map((el, i) => ({
      entra: el.dataset.passo !== undefined ? parseFloat(el.dataset.passo) : i + 1,
      sai: el.dataset.sai !== undefined ? parseFloat(el.dataset.sai) : Infinity }));
    const marcos = [...new Set(itens.flatMap((x) => [x.entra, x.sai]).filter((v) => v > 0 && v !== Infinity))].sort((a, b) => a - b);
    if (${args.includes("--passos")}) return marcos.length ? [...marcos.keys(), marcos.length] : [0];
    const antesDeSair = itens.filter((x) => x.sai !== Infinity).map((x) => marcos.indexOf(x.sai));
    return [...new Set([...antesDeSair, marcos.length])].sort((a, b) => a - b);
  })`);
  const partes = [];
  for (let i = 0; i < estados.length; i++) for (const k of estados[i]) {
    await avaliar(`window.deck.ir(${i}, false, ${k});
      window.deck.slides.forEach((s, j) => s.classList.toggle("fora-pdf", j !== ${i})); true`);
    const pdf = await cdp("Page.printToPDF", { printBackground: true, preferCSSPageSize: true });
    const parte = path.join(perfil, `parte-${String(partes.length).padStart(3, "0")}.pdf`);
    fs.writeFileSync(parte, Buffer.from(pdf.result.data, "base64"));
    partes.push(parte);
  }
  execFileSync("qpdf", ["--empty", "--pages", ...partes, "--", path.join(dist, `${path.basename(pastaDeck)}.pdf`)]);
}

ws.close(); chrome.kill(); fs.rmSync(perfil, { recursive: true, force: true });
fs.writeFileSync(path.join(qa, "relatorio.json"), JSON.stringify(relatorio, null, 2));

let falhou = false;
for (const x of excecoes) { console.log(`✗ erro de JavaScript na página: ${x}`); falhou = true; }
for (const r of relatorio) {
  const marca = r.erros.length ? "✗" : r.avisos.length ? "!" : "✓";
  console.log(`${marca} slide ${r.slide} (${r.palavras} palavras)`);
  for (const e of r.erros) console.log(`    erro: ${e}`);
  for (const a of r.avisos) console.log(`    aviso: ${a}`);
  if (r.erros.length) falhou = true;
}
console.log(`\n${saida}\n${qa}`);
process.exit(falhou ? 1 : 0);
