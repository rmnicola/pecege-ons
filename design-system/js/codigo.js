/* Bloco de código offline: barra de arquivo, syntax highlight, cópia e âncoras de ajuda. */
(function () {
  const iconeCopiar = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="8" y="8" width="12" height="13" rx="2"/><path d="M15 8 V4 a1 1 0 0 0-1-1 H4 a1 1 0 0 0-1 1 V15 a1 1 0 0 0 1 1 H8"/></svg>';
  const iconeCopiado = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12 L10 17 L20 6"/></svg>';

  function linhasColoridas(codigo, linguagem) {
    const linhas = [document.createElement('span')];
    const acrescentar = (texto, tipo) => {
      texto.split('\n').forEach((parte, i) => {
        if (i) linhas.push(document.createElement('span'));
        if (!parte) return;
        const trecho = tipo ? document.createElement('span') : document.createTextNode(parte);
        if (tipo) { trecho.className = 'py-' + tipo; trecho.textContent = parte; }
        linhas.at(-1).append(trecho);
      });
    };
    if (linguagem.toLowerCase() === 'python') {
      const tokens = /("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|#[^\n]*|\b(?:False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b|\b\d+(?:\.\d+)?\b|\b[A-Za-z_]\w*(?=\s*\())/g;
      let fim = 0;
      for (const token of codigo.matchAll(tokens)) {
        acrescentar(codigo.slice(fim, token.index));
        const texto = token[0];
        const tipo = /^["']/.test(texto) ? 'string' : texto.startsWith('#') ? 'comentario' : /^\d/.test(texto) ? 'numero' : /^(?:False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)$/.test(texto) ? 'palavra' : 'funcao';
        acrescentar(texto, tipo);
        fim = token.index + texto.length;
      }
      acrescentar(codigo.slice(fim));
    } else acrescentar(codigo);
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
    alvo.classList.add('bloco-codigo');
    const barra = document.createElement('div');
    barra.className = 'codigo-barra';
    const nome = document.createElement('span');
    nome.className = 'codigo-arquivo';
    nome.textContent = arquivo ? arquivo + ' · ' + linguagem : linguagem;
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
