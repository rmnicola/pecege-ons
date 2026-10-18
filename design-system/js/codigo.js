/* Bloco de código offline: barra de arquivo, syntax highlight, cópia e âncoras de ajuda. */
(function () {
  const iconeCopiar = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M15 8 V4 a1 1 0 0 0-1-1 H4 a1 1 0 0 0-1 1 V15 a1 1 0 0 0 1 1 H8"/></svg>';
  const iconeCopiado = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12 L10 17 L20 6"/></svg>';

  /* Realce no padrão do Expressive Code (Starlight): cada trecho recebe uma classe tk-<tipo>. */
  const PALAVRAS_PY = new Set('and as assert async await break class continue def del elif else except finally for from global if import in is lambda nonlocal not or pass raise return try while with yield match case'.split(' '));
  const CONSTANTES_PY = new Set(['True', 'False', 'None']);
  const EMBUTIDOS_PY = new Set('print len dict list int float str bool open range sorted enumerate zip isinstance set tuple sum min max type round any all map filter super object Exception ValueError TypeError KeyError'.split(' '));
  const PREFIXOS_SHELL = new Set(['sudo', 'time', 'env']);
  const SHELL = new Set(['terminal', 'shell', 'bash', 'sh', 'zsh', 'console']);
  const ehShell = linguagem => SHELL.has(linguagem.toLowerCase());

  function tokensPython(codigo) {
    const re = /(#[^\n]*)|([rRbBfFuU]{0,2}(?:"""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*'))|(@[A-Za-z_][\w.]*)|(\b\d+(?:\.\d+)?(?:e[+-]?\d+)?\b)|([A-Za-z_]\w*)|(==|!=|<=|>=|->|\*\*|\/\/|[-+*\/%=<>!&|^~])|([()[\]{}.,:;])|(\s+)|([\s\S])/g;
    const saida = [];
    let anterior = '', depoisDeDef = false;
    for (const m of codigo.matchAll(re)) {
      const [t, com, str, dec, num, nome, op, pont] = m;
      let tipo = null;
      if (com) tipo = 'comentario';
      else if (str) tipo = 'string';
      else if (dec) tipo = 'funcao';
      else if (num) tipo = 'numero';
      else if (nome) {
        const resto = codigo.slice(m.index + t.length);
        if (depoisDeDef) tipo = 'definicao';
        else if (PALAVRAS_PY.has(t)) tipo = 'palavra';
        else if (CONSTANTES_PY.has(t)) tipo = 'constante';
        else if (/^\s*\(/.test(resto)) tipo = EMBUTIDOS_PY.has(t) && anterior !== '.' ? 'embutido' : 'funcao';
        else if (/^\s*=(?!=)/.test(resto) && /[(,]\s*$/.test(codigo.slice(0, m.index))) tipo = 'parametro';
        else if (anterior === '.') tipo = 'atributo';
        else if (EMBUTIDOS_PY.has(t)) tipo = 'embutido';
        else if (t === 'self' || t === 'cls') tipo = 'self';
        depoisDeDef = t === 'def' || t === 'class';
      } else if (op) tipo = 'operador';
      else if (pont) tipo = 'pontuacao';
      if (!/^\s+$/.test(t)) anterior = t;
      saida.push([t, tipo]);
    }
    return saida;
  }

  function tokensShell(codigo) {
    const saida = [];
    let continua = false;
    codigo.split('\n').forEach((linha, n) => {
      if (n) saida.push(['\n', null]);
      /* Linha que continua a anterior (terminada em \) não começa um comando novo. */
      let esperaComando = !continua;
      continua = /\\\s*$/.test(linha);
      const re = /(\s+)|(#.*$)|("(?:\\.|[^"\\])*"|'[^']*')|(\$\([^)]*\)|\$\{?\w+\}?)|(&&|\|\||[|;]|>>?|\\$)|([^\s"'|;>&$\\]+)|([\s\S])/g;
      for (const m of linha.matchAll(re)) {
        const [t, esp, com, str, variavel, op, palavra] = m;
        let tipo = null;
        if (esp) { saida.push([t, null]); continue; }
        if (com) tipo = 'comentario';
        else if (str) tipo = 'string';
        else if (variavel) tipo = 'variavel';
        else if (op) { tipo = 'operador'; esperaComando = /^(&&|\|\||\||;)$/.test(t); }
        else if (palavra) {
          if (esperaComando) { tipo = PREFIXOS_SHELL.has(t) ? 'palavra' : 'funcao'; esperaComando = PREFIXOS_SHELL.has(t); }
          else if (t.startsWith('-')) tipo = 'parametro';
          else if (/^\d+(\.\d+)?$/.test(t)) tipo = 'numero';
        }
        saida.push([t, tipo]);
      }
    });
    return saida;
  }

  function linhasColoridas(codigo, linguagem) {
    const linhas = [document.createElement('span')];
    const acrescentar = (texto, tipo) => {
      texto.split('\n').forEach((parte, i) => {
        if (i) linhas.push(document.createElement('span'));
        if (!parte) return;
        const trecho = tipo ? document.createElement('span') : document.createTextNode(parte);
        if (tipo) { trecho.className = 'tk-' + tipo; trecho.textContent = parte; }
        linhas.at(-1).append(trecho);
      });
    };
    const lang = linguagem.toLowerCase();
    const tokens = lang === 'python' ? tokensPython(codigo) : ehShell(lang) ? tokensShell(codigo) : [[codigo, null]];
    tokens.forEach(([texto, tipo]) => acrescentar(texto, tipo));
    linhas.forEach(linha => { linha.className = 'codigo-linha'; });
    return linhas;
  }

  async function copiarTexto(texto, botao) {
    try {
      if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(texto); return true; }
    } catch (_) { /* Abertura local ou permissão restrita: tenta o mecanismo legado. */ }
    const campo = document.createElement('textarea');
    campo.value = texto;
    campo.style.cssText = 'position:fixed;left:0;top:0;width:1px;height:1px;opacity:0';
    document.body.append(campo);
    campo.select();
    try { return document.execCommand('copy'); }
    catch (_) { return false; }
    finally { campo.remove(); botao.focus(); }
  }

  function montar(alvo, { codigo, arquivo = '', linguagem = 'Python', ajudas = [] }) {
    if (!(alvo instanceof HTMLElement) || typeof codigo !== 'string') throw new TypeError('Informe um elemento e o código como texto.');
    const linhas = linhasColoridas(codigo, linguagem);
    let ultimoFim = -1;
    for (const ajuda of ajudas) {
      if (!Number.isInteger(ajuda.inicio) || !Number.isInteger(ajuda.fim) || ajuda.inicio <= ultimoFim || ajuda.fim < ajuda.inicio || ajuda.fim >= linhas.length)
        throw new RangeError('As ajudas precisam indicar intervalos válidos, ordenados e sem sobreposição.');
      ultimoFim = ajuda.fim;
    }
    const terminal = ehShell(linguagem);
    alvo.classList.add('bloco-codigo', terminal ? 'moldura-terminal' : 'moldura-editor');
    const barra = document.createElement('div');
    barra.className = 'codigo-barra';
    const nome = document.createElement('span');
    nome.className = terminal ? 'codigo-titulo' : 'codigo-arquivo';
    nome.textContent = arquivo || (terminal ? 'Terminal' : linguagem);
    if (terminal) {
      const pontos = document.createElement('span');
      pontos.className = 'codigo-pontos';
      pontos.setAttribute('aria-hidden', 'true');
      barra.append(pontos);
    }
    const acoes = document.createElement('div');
    acoes.className = 'codigo-acoes';
    const status = document.createElement('span');
    status.className = 'codigo-status';
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.className = 'copiar-codigo';
    const rotulo = 'Copiar código' + (arquivo ? ' de ' + arquivo : '');
    const restaurar = () => {
      botao.innerHTML = iconeCopiar;
      botao.title = rotulo;
      botao.setAttribute('aria-label', rotulo);
      status.textContent = '';
    };
    restaurar();
    let temporizador;
    botao.addEventListener('click', async () => {
      const ok = await copiarTexto(codigo, botao);
      botao.innerHTML = ok ? iconeCopiado : iconeCopiar;
      status.textContent = ok ? 'Copiado!' : 'Falha ao copiar';
      botao.title = ok ? 'Código copiado' : 'Selecione o código e use Ctrl+C';
      botao.setAttribute('aria-label', botao.title);
      clearTimeout(temporizador);
      temporizador = setTimeout(restaurar, 2500);
    });
    acoes.append(status, botao);
    barra.append(nome, acoes);
    const pre = document.createElement('pre');
    pre.className = 'codigo-pre';
    const conteudo = document.createElement('code');
    conteudo.setAttribute('aria-label', 'Código ' + linguagem);
    for (let i = 0; i < linhas.length;) {
      const ordem = ajudas.findIndex(ajuda => ajuda.inicio === i);
      if (ordem < 0) { conteudo.append(linhas[i++]); continue; }
      const ajuda = ajudas[ordem];
      const grupo = document.createElement('span');
      grupo.className = 'codigo-grupo';
      grupo.dataset.ajuda = ajuda.texto;
      grupo.dataset.ajudaOrdem = ordem + 1;
      while (i <= ajuda.fim) grupo.append(linhas[i++]);
      conteudo.append(grupo);
    }
    pre.append(conteudo);
    alvo.replaceChildren(barra, pre);
    return alvo;
  }
  window.PECEGE_CODIGO = { montar };
})();
